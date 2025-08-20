"""
GPU推理池 - 每个GPU一个专用线程，支持CUDA图
"""
import torch
import threading
import queue
from typing import Dict, Any
import time

class GPUInferenceWorker:
    """单个GPU的专用推理线程"""
    
    def __init__(self, gpu_id: int, gpu_models: dict):
        self.gpu_id = gpu_id
        self.device = f'cuda:{gpu_id}'
        self.gpu_models = gpu_models
        
        # 任务队列
        self.task_queue = queue.Queue()
        self.result_dict = {}
        
        # 启动专用线程
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        
        # CUDA图缓存（在专用线程中创建）
        self.cuda_graphs = {}
        
    def _worker_loop(self):
        """专用线程主循环 - 这里可以安全使用CUDA图"""
        torch.cuda.set_device(self.gpu_id)
        
        while True:
            try:
                # 获取任务
                task = self.task_queue.get(timeout=0.1)
                if task is None:
                    break
                    
                batch_idx, whisper_batch, latent_batch, timesteps = task
                
                # 执行推理（在同一线程中，CUDA图安全）
                result = self._inference(whisper_batch, latent_batch, timesteps)
                
                # 存储结果
                self.result_dict[batch_idx] = result
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"GPU {self.gpu_id} 推理错误: {e}")
                
    def _inference(self, whisper_batch, latent_batch, timesteps):
        """实际推理 - 可以使用CUDA图"""
        with torch.cuda.device(self.device):
            with torch.no_grad():
                # 这里的模型已经被torch.compile优化
                # 且在单线程中可以安全使用CUDA图
                audio_features = self.gpu_models['pe'](whisper_batch)
                pred_latents = self.gpu_models['unet'].model(
                    latent_batch, timesteps, 
                    encoder_hidden_states=audio_features
                ).sample
                recon_frames = self.gpu_models['vae'].decode_latents(pred_latents)
                
        return recon_frames
        
    def submit_task(self, batch_idx, whisper_batch, latent_batch, timesteps):
        """提交推理任务"""
        # 将数据移到GPU
        whisper_batch = whisper_batch.to(self.device)
        latent_batch = latent_batch.to(self.device) 
        timesteps = timesteps.to(self.device)
        
        self.task_queue.put((batch_idx, whisper_batch, latent_batch, timesteps))
        
    def get_result(self, batch_idx, timeout=10):
        """获取推理结果"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if batch_idx in self.result_dict:
                return self.result_dict.pop(batch_idx)
            time.sleep(0.01)
        raise TimeoutError(f"等待批次 {batch_idx} 结果超时")


class GPUInferencePool:
    """GPU推理池管理器"""
    
    def __init__(self, gpu_models_dict: Dict[str, dict]):
        """
        gpu_models_dict: {
            'cuda:0': {'unet': ..., 'vae': ..., 'pe': ...},
            'cuda:1': {'unet': ..., 'vae': ..., 'pe': ...}
        }
        """
        self.workers = {}
        
        # 为每个GPU创建专用worker
        for device, models in gpu_models_dict.items():
            gpu_id = int(device.split(':')[1])
            self.workers[device] = GPUInferenceWorker(gpu_id, models)
            print(f"✅ GPU {gpu_id} 推理线程已启动（支持CUDA图）")
    
    def process_batch(self, batch_idx, batch_data, target_device):
        """处理一个批次"""
        whisper_batch, latent_batch = batch_data
        timesteps = torch.tensor([0], dtype=torch.long)
        
        # 提交到指定GPU的专用线程
        worker = self.workers[target_device]
        worker.submit_task(batch_idx, whisper_batch, latent_batch, timesteps)
        
        # 异步获取结果
        return worker.get_result(batch_idx)
    
    def process_batches_parallel(self, all_batches):
        """并行处理所有批次"""
        results = {}
        gpu_count = len(self.workers)
        
        # 分配批次到不同GPU
        for batch_idx, batch_data in enumerate(all_batches):
            target_device = f'cuda:{batch_idx % gpu_count}'
            worker = self.workers[target_device]
            
            whisper_batch, latent_batch = batch_data
            timesteps = torch.tensor([0], dtype=torch.long)
            
            # 提交任务（非阻塞）
            worker.submit_task(batch_idx, whisper_batch, latent_batch, timesteps)
        
        # 收集结果
        for batch_idx in range(len(all_batches)):
            target_device = f'cuda:{batch_idx % gpu_count}'
            worker = self.workers[target_device]
            results[batch_idx] = worker.get_result(batch_idx)
            
        return results