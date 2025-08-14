#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-GPU Parallel Processing Engine for MuseTalk
支持真正的GPU并行处理，可配置GPU数量和批处理策略
"""

import os
import sys
import json
import torch
import torch.nn as nn
import torch.multiprocessing as mp
from torch.nn.parallel import DataParallel, DistributedDataParallel
import numpy as np
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import gc
import psutil
import warnings
warnings.filterwarnings("ignore")

# 添加MuseTalk模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MuseTalk'))

@dataclass
class GPUConfig:
    """GPU配置类"""
    gpu_ids: List[int]  # 使用的GPU ID列表
    batch_size_per_gpu: int  # 每个GPU的批处理大小
    memory_fraction: float = 0.9  # 每个GPU使用的内存比例
    enable_amp: bool = True  # 是否启用自动混合精度
    enable_cudnn_benchmark: bool = True  # 是否启用cudnn benchmark
    enable_model_parallel: bool = False  # 是否启用模型并行
    enable_pipeline_parallel: bool = False  # 是否启用流水线并行

class MultiGPUParallelEngine:
    """多GPU并行处理引擎"""
    
    def __init__(self, config: GPUConfig):
        self.config = config
        self.num_gpus = len(config.gpu_ids)
        
        # 验证GPU可用性
        self._validate_gpus()
        
        # 初始化GPU设置
        self._setup_gpus()
        
        # 模型容器
        self.models = {}
        self.model_locks = {}
        
        # 批处理队列
        self.batch_queues = {gpu_id: queue.Queue(maxsize=10) for gpu_id in config.gpu_ids}
        self.result_queue = queue.Queue()
        
        # 工作线程池
        self.executor = ThreadPoolExecutor(max_workers=self.num_gpus * 2)
        
        # 性能监控
        self.performance_stats = {
            gpu_id: {
                'processed_batches': 0,
                'total_time': 0,
                'avg_batch_time': 0,
                'memory_usage': 0
            } for gpu_id in config.gpu_ids
        }
        
        print(f"Multi-GPU Parallel Engine initialized with {self.num_gpus} GPUs")
        print(f"GPU IDs: {config.gpu_ids}")
        print(f"Batch size per GPU: {config.batch_size_per_gpu}")
        
    def _validate_gpus(self):
        """验证GPU可用性"""
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available")
        
        available_gpus = torch.cuda.device_count()
        for gpu_id in self.config.gpu_ids:
            if gpu_id >= available_gpus:
                raise ValueError(f"GPU {gpu_id} not available. Only {available_gpus} GPUs detected.")
        
        # 打印GPU信息
        for gpu_id in self.config.gpu_ids:
            props = torch.cuda.get_device_properties(gpu_id)
            memory_gb = props.total_memory / (1024**3)
            print(f"GPU {gpu_id}: {props.name}, Memory: {memory_gb:.1f}GB")
    
    def _setup_gpus(self):
        """设置GPU环境"""
        # 设置CUDA设备顺序
        os.environ['CUDA_VISIBLE_DEVICES'] = ','.join(map(str, self.config.gpu_ids))
        
        # 设置PyTorch优化
        if self.config.enable_cudnn_benchmark:
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
        
        # 设置内存分配策略
        for gpu_id in self.config.gpu_ids:
            torch.cuda.set_device(gpu_id)
            # 设置内存分配比例
            torch.cuda.set_per_process_memory_fraction(
                self.config.memory_fraction, 
                device=gpu_id
            )
            # 清空缓存
            torch.cuda.empty_cache()
    
    def load_models(self, model_paths: Dict[str, str]):
        """加载模型到多个GPU"""
        from musetalk.utils.utils import load_all_model
        
        print("Loading models to GPUs...")
        
        # 首先在CPU上加载模型
        cpu_models = load_all_model(
            model_paths.get('audio_processor'),
            model_paths.get('vae'),
            model_paths.get('unet'),
            model_paths.get('pe')
        )
        
        # 为每个GPU创建模型副本
        for gpu_id in self.config.gpu_ids:
            device = f'cuda:{gpu_id}'
            self.models[gpu_id] = {}
            self.model_locks[gpu_id] = threading.Lock()
            
            # 复制模型到GPU
            for name, model in cpu_models.items():
                if model is not None:
                    # 创建模型副本
                    model_copy = self._copy_model_to_device(model, device)
                    
                    # 启用混合精度
                    if self.config.enable_amp and name != 'audio_processor':
                        model_copy = model_copy.half()
                    
                    # 设置为评估模式
                    model_copy.eval()
                    
                    self.models[gpu_id][name] = model_copy
                    
            print(f"Models loaded to GPU {gpu_id}")
        
        # 清理CPU模型
        del cpu_models
        gc.collect()
        
        print("All models loaded successfully")
    
    def _copy_model_to_device(self, model, device):
        """复制模型到指定设备"""
        with torch.cuda.device(device):
            if hasattr(model, 'to'):
                return model.to(device)
            elif hasattr(model, 'cuda'):
                return model.cuda(device)
            else:
                # 对于复杂的模型结构，递归处理
                return self._deep_copy_to_device(model, device)
    
    def _deep_copy_to_device(self, obj, device):
        """深度复制对象到设备"""
        import copy
        
        if isinstance(obj, torch.nn.Module):
            return obj.to(device)
        elif isinstance(obj, torch.Tensor):
            return obj.to(device)
        elif isinstance(obj, dict):
            return {k: self._deep_copy_to_device(v, device) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy_to_device(item, device) for item in obj]
        else:
            return copy.deepcopy(obj)
    
    def process_batch_parallel(self, batch_data: List[Dict], strategy='round_robin'):
        """
        并行处理批次数据
        
        Args:
            batch_data: 批处理数据列表
            strategy: 分配策略 ('round_robin', 'load_balance', 'data_parallel')
        
        Returns:
            处理结果列表
        """
        if strategy == 'data_parallel':
            return self._process_data_parallel(batch_data)
        elif strategy == 'load_balance':
            return self._process_load_balanced(batch_data)
        else:
            return self._process_round_robin(batch_data)
    
    def _process_round_robin(self, batch_data: List[Dict]):
        """轮询分配策略"""
        results = []
        futures = []
        
        # 将数据分配到不同GPU
        for i, data in enumerate(batch_data):
            gpu_id = self.config.gpu_ids[i % self.num_gpus]
            future = self.executor.submit(self._process_on_gpu, gpu_id, data)
            futures.append(future)
        
        # 收集结果
        for future in futures:
            result = future.result()
            results.append(result)
        
        return results
    
    def _process_load_balanced(self, batch_data: List[Dict]):
        """负载均衡分配策略"""
        results = []
        futures = []
        
        # 根据GPU内存使用情况分配
        gpu_loads = self._get_gpu_loads()
        sorted_gpus = sorted(gpu_loads.items(), key=lambda x: x[1])
        
        for i, data in enumerate(batch_data):
            # 选择负载最低的GPU
            gpu_id = sorted_gpus[i % len(sorted_gpus)][0]
            future = self.executor.submit(self._process_on_gpu, gpu_id, data)
            futures.append(future)
        
        # 收集结果
        for future in futures:
            result = future.result()
            results.append(result)
        
        return results
    
    def _process_data_parallel(self, batch_data: List[Dict]):
        """数据并行处理策略"""
        # 将批次数据分割到多个GPU
        chunk_size = len(batch_data) // self.num_gpus
        chunks = []
        
        for i in range(self.num_gpus):
            start_idx = i * chunk_size
            if i == self.num_gpus - 1:
                # 最后一个GPU处理剩余数据
                chunk = batch_data[start_idx:]
            else:
                chunk = batch_data[start_idx:start_idx + chunk_size]
            chunks.append(chunk)
        
        # 并行处理
        futures = []
        for gpu_id, chunk in zip(self.config.gpu_ids, chunks):
            if chunk:  # 只处理非空块
                future = self.executor.submit(self._process_chunk_on_gpu, gpu_id, chunk)
                futures.append(future)
        
        # 收集结果
        results = []
        for future in futures:
            chunk_results = future.result()
            results.extend(chunk_results)
        
        return results
    
    def _process_on_gpu(self, gpu_id: int, data: Dict):
        """在指定GPU上处理单个数据"""
        start_time = time.time()
        
        with self.model_locks[gpu_id]:
            torch.cuda.set_device(gpu_id)
            
            # 获取模型
            models = self.models[gpu_id]
            
            # 处理数据（这里需要根据实际MuseTalk处理逻辑实现）
            result = self._inference_step(models, data, gpu_id)
            
            # 更新统计
            elapsed_time = time.time() - start_time
            self._update_stats(gpu_id, elapsed_time)
            
        return result
    
    def _process_chunk_on_gpu(self, gpu_id: int, chunk: List[Dict]):
        """在指定GPU上处理数据块"""
        results = []
        
        with self.model_locks[gpu_id]:
            torch.cuda.set_device(gpu_id)
            models = self.models[gpu_id]
            
            for data in chunk:
                start_time = time.time()
                result = self._inference_step(models, data, gpu_id)
                results.append(result)
                
                elapsed_time = time.time() - start_time
                self._update_stats(gpu_id, elapsed_time)
        
        return results
    
    def _inference_step(self, models: Dict, data: Dict, gpu_id: int):
        """执行推理步骤"""
        # 这里需要根据实际MuseTalk的推理逻辑实现
        # 示例实现
        device = f'cuda:{gpu_id}'
        
        # 启用自动混合精度
        if self.config.enable_amp:
            with torch.cuda.amp.autocast():
                # 执行推理
                output = self._run_inference(models, data, device)
        else:
            output = self._run_inference(models, data, device)
        
        return output
    
    def _run_inference(self, models: Dict, data: Dict, device: str):
        """运行实际推理（需要根据MuseTalk实现）"""
        # 这是一个占位实现，需要根据实际MuseTalk逻辑替换
        return {'status': 'processed', 'device': device, 'data': data}
    
    def _get_gpu_loads(self) -> Dict[int, float]:
        """获取GPU负载情况"""
        loads = {}
        
        for gpu_id in self.config.gpu_ids:
            # 获取内存使用情况
            allocated = torch.cuda.memory_allocated(gpu_id)
            total = torch.cuda.get_device_properties(gpu_id).total_memory
            load = allocated / total
            loads[gpu_id] = load
        
        return loads
    
    def _update_stats(self, gpu_id: int, elapsed_time: float):
        """更新性能统计"""
        stats = self.performance_stats[gpu_id]
        stats['processed_batches'] += 1
        stats['total_time'] += elapsed_time
        stats['avg_batch_time'] = stats['total_time'] / stats['processed_batches']
        
        # 更新内存使用
        allocated = torch.cuda.memory_allocated(gpu_id) / (1024**3)  # GB
        stats['memory_usage'] = allocated
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        report = {
            'gpu_stats': self.performance_stats,
            'total_processed': sum(s['processed_batches'] for s in self.performance_stats.values()),
            'avg_processing_time': np.mean([s['avg_batch_time'] for s in self.performance_stats.values()])
        }
        
        # 添加GPU利用率
        for gpu_id in self.config.gpu_ids:
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                report['gpu_stats'][gpu_id]['utilization'] = util.gpu
            except:
                pass
        
        return report
    
    def cleanup(self):
        """清理资源"""
        print("Cleaning up Multi-GPU Engine...")
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        # 清理模型
        for gpu_id in self.config.gpu_ids:
            torch.cuda.set_device(gpu_id)
            torch.cuda.empty_cache()
        
        # 清理队列
        for q in self.batch_queues.values():
            while not q.empty():
                q.get()
        
        print("Cleanup completed")


class OptimizedBatchProcessor:
    """优化的批处理器"""
    
    def __init__(self, engine: MultiGPUParallelEngine):
        self.engine = engine
        self.batch_size = engine.config.batch_size_per_gpu * engine.num_gpus
        
    def process_video_batch(self, video_paths: List[str], audio_paths: List[str]):
        """批量处理视频"""
        # 准备批处理数据
        batch_data = []
        for video_path, audio_path in zip(video_paths, audio_paths):
            batch_data.append({
                'video': video_path,
                'audio': audio_path,
                'timestamp': time.time()
            })
        
        # 使用数据并行策略处理
        results = self.engine.process_batch_parallel(batch_data, strategy='data_parallel')
        
        return results
    
    def process_stream(self, stream_generator):
        """处理流式数据"""
        batch_buffer = []
        
        for data in stream_generator:
            batch_buffer.append(data)
            
            # 当缓冲区满时处理
            if len(batch_buffer) >= self.batch_size:
                results = self.engine.process_batch_parallel(batch_buffer, strategy='load_balance')
                batch_buffer = []
                
                yield results
        
        # 处理剩余数据
        if batch_buffer:
            results = self.engine.process_batch_parallel(batch_buffer, strategy='load_balance')
            yield results


def create_gpu_config(gpu_ids: List[int], batch_size_per_gpu: int, **kwargs) -> GPUConfig:
    """创建GPU配置"""
    return GPUConfig(
        gpu_ids=gpu_ids,
        batch_size_per_gpu=batch_size_per_gpu,
        **kwargs
    )


if __name__ == "__main__":
    # 示例：配置和测试
    print("Multi-GPU Parallel Engine Test")
    
    # 检测可用GPU
    if torch.cuda.is_available():
        num_gpus = torch.cuda.device_count()
        print(f"Detected {num_gpus} GPUs")
        
        # 创建配置
        # 对于单张RTX 4090D 48GB
        if num_gpus == 1:
            config = create_gpu_config(
                gpu_ids=[0],
                batch_size_per_gpu=16,  # 48GB可以处理更大批次
                memory_fraction=0.95
            )
        # 对于4张RTX 4090 24GB
        else:
            config = create_gpu_config(
                gpu_ids=list(range(min(4, num_gpus))),
                batch_size_per_gpu=8,  # 24GB的合理批次大小
                memory_fraction=0.9
            )
        
        # 创建引擎
        engine = MultiGPUParallelEngine(config)
        
        # 测试性能
        print("\nRunning performance test...")
        test_data = [{'id': i, 'data': f'test_{i}'} for i in range(32)]
        
        start_time = time.time()
        results = engine.process_batch_parallel(test_data, strategy='data_parallel')
        elapsed = time.time() - start_time
        
        print(f"Processed {len(test_data)} items in {elapsed:.2f} seconds")
        print(f"Throughput: {len(test_data)/elapsed:.2f} items/second")
        
        # 打印性能报告
        report = engine.get_performance_report()
        print("\nPerformance Report:")
        print(json.dumps(report, indent=2))
        
        # 清理
        engine.cleanup()
    else:
        print("CUDA not available")