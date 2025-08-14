"""
GPU优化器 - 自动检测并最大化利用GPU显存
"""
import os
import torch
import pynvml
import numpy as np
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPUOptimizer:
    """GPU资源优化器"""
    
    def __init__(self):
        pynvml.nvmlInit()
        self.device_count = torch.cuda.device_count()
        self.gpu_info = self._collect_gpu_info()
        
    def _collect_gpu_info(self) -> List[Dict]:
        """收集GPU信息"""
        info = []
        for i in range(self.device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
            
            info.append({
                'id': i,
                'name': name,
                'total_memory': mem_info.total,
                'free_memory': mem_info.free,
                'used_memory': mem_info.used,
                'total_gb': mem_info.total / (1024**3),
                'free_gb': mem_info.free / (1024**3),
                'used_gb': mem_info.used / (1024**3)
            })
            
            logger.info(f"GPU {i}: {name}, Total: {info[-1]['total_gb']:.1f}GB, Free: {info[-1]['free_gb']:.1f}GB")
            
        return info
    
    def calculate_optimal_batch_size(self, model_memory_mb: float = 2000, 
                                    frame_memory_mb: float = 50,
                                    safety_factor: float = 0.95) -> Dict:
        """
        计算最优batch_size
        
        Args:
            model_memory_mb: 模型占用显存(MB)
            frame_memory_mb: 每帧占用显存(MB)  
            safety_factor: 安全系数(默认95%利用率)
        """
        results = {}
        
        for gpu in self.gpu_info:
            # 可用显存(MB)
            available_mb = (gpu['free_gb'] * 1024) * safety_factor
            
            # 减去模型占用
            remaining_mb = available_mb - model_memory_mb
            
            # 计算可处理帧数
            if remaining_mb > 0:
                batch_size = int(remaining_mb / frame_memory_mb)
            else:
                batch_size = 1
                
            results[gpu['id']] = {
                'gpu_name': gpu['name'],
                'total_memory_gb': gpu['total_gb'],
                'free_memory_gb': gpu['free_gb'],
                'model_memory_mb': model_memory_mb,
                'frame_memory_mb': frame_memory_mb,
                'optimal_batch_size': batch_size,
                'estimated_usage_gb': (model_memory_mb + batch_size * frame_memory_mb) / 1024
            }
            
            logger.info(f"GPU {gpu['id']}: Optimal batch_size = {batch_size}")
            
        return results
    
    def measure_actual_memory_usage(self, test_batch_sizes: List[int] = [1, 2, 4, 8, 16, 32]) -> Dict:
        """实际测试不同batch_size的显存占用"""
        results = {}
        
        for gpu_id in range(self.device_count):
            torch.cuda.set_device(gpu_id)
            torch.cuda.empty_cache()
            
            gpu_results = []
            
            for batch_size in test_batch_sizes:
                try:
                    # 创建测试张量(模拟MuseTalk的latent)
                    # MuseTalk使用256x256图像，latent通常是64x64x4
                    test_tensor = torch.randn(
                        batch_size, 4, 64, 64, 
                        device=f'cuda:{gpu_id}',
                        dtype=torch.float16
                    )
                    
                    # 测量显存
                    torch.cuda.synchronize()
                    allocated = torch.cuda.memory_allocated(gpu_id) / (1024**3)
                    reserved = torch.cuda.memory_reserved(gpu_id) / (1024**3)
                    
                    gpu_results.append({
                        'batch_size': batch_size,
                        'allocated_gb': allocated,
                        'reserved_gb': reserved
                    })
                    
                    # 清理
                    del test_tensor
                    torch.cuda.empty_cache()
                    
                except RuntimeError as e:
                    logger.warning(f"GPU {gpu_id} batch_size {batch_size} failed: {e}")
                    break
                    
            results[gpu_id] = gpu_results
            
        return results
    
    def get_recommended_config(self) -> Dict:
        """获取推荐配置"""
        # 先计算理论值
        theoretical = self.calculate_optimal_batch_size()
        
        # 实测显存占用
        measured = self.measure_actual_memory_usage()
        
        config = {
            'gpu_count': self.device_count,
            'gpus': []
        }
        
        for gpu_id in range(self.device_count):
            gpu_config = {
                'id': gpu_id,
                'name': self.gpu_info[gpu_id]['name'],
                'total_memory_gb': self.gpu_info[gpu_id]['total_gb'],
                'free_memory_gb': self.gpu_info[gpu_id]['free_gb']
            }
            
            # 根据GPU型号设置推荐配置
            if '4090' in gpu_config['name']:
                if gpu_config['total_memory_gb'] > 40:  # 4090D 48GB
                    gpu_config['recommended_batch_size'] = 24
                    gpu_config['max_batch_size'] = 32
                else:  # 4090 24GB
                    gpu_config['recommended_batch_size'] = 8
                    gpu_config['max_batch_size'] = 12
            elif '3090' in gpu_config['name']:
                gpu_config['recommended_batch_size'] = 6
                gpu_config['max_batch_size'] = 10
            else:
                # 根据显存大小估算
                free_gb = gpu_config['free_memory_gb']
                gpu_config['recommended_batch_size'] = max(1, int(free_gb / 3))
                gpu_config['max_batch_size'] = max(1, int(free_gb / 2))
            
            # 如果有实测数据，调整推荐值
            if gpu_id in measured and measured[gpu_id]:
                max_tested = max([m['batch_size'] for m in measured[gpu_id]])
                gpu_config['tested_max_batch_size'] = max_tested
                
            config['gpus'].append(gpu_config)
            
        # 计算总配置
        config['total_batch_size'] = sum([g['recommended_batch_size'] for g in config['gpus']])
        config['cuda_visible_devices'] = ','.join([str(g['id']) for g in config['gpus']])
        
        return config
    
    def auto_configure(self) -> Dict:
        """自动配置并设置环境变量"""
        config = self.get_recommended_config()
        
        # 设置环境变量
        os.environ['CUDA_VISIBLE_DEVICES'] = config['cuda_visible_devices']
        os.environ['BATCH_SIZE'] = str(config['total_batch_size'])
        
        # 如果是单GPU，设置更高的批处理
        if config['gpu_count'] == 1:
            gpu = config['gpus'][0]
            if gpu['free_memory_gb'] > 40:
                os.environ['BATCH_SIZE'] = '24'
            elif gpu['free_memory_gb'] > 20:
                os.environ['BATCH_SIZE'] = '12'
        
        logger.info(f"Auto-configured: CUDA_VISIBLE_DEVICES={os.environ['CUDA_VISIBLE_DEVICES']}")
        logger.info(f"Auto-configured: BATCH_SIZE={os.environ['BATCH_SIZE']}")
        
        return config


def optimize_for_musetalk():
    """针对MuseTalk优化"""
    optimizer = GPUOptimizer()
    config = optimizer.auto_configure()
    
    print("\n" + "="*60)
    print("MuseTalk GPU配置优化完成")
    print("="*60)
    print(f"检测到 {config['gpu_count']} 个GPU")
    
    for gpu in config['gpus']:
        print(f"\nGPU {gpu['id']}: {gpu['name']}")
        print(f"  总显存: {gpu['total_memory_gb']:.1f} GB")
        print(f"  空闲显存: {gpu['free_memory_gb']:.1f} GB")
        print(f"  推荐batch_size: {gpu['recommended_batch_size']}")
        print(f"  最大batch_size: {gpu['max_batch_size']}")
    
    print(f"\n总batch_size: {config['total_batch_size']}")
    print(f"CUDA_VISIBLE_DEVICES: {config['cuda_visible_devices']}")
    print("="*60 + "\n")
    
    return config


if __name__ == "__main__":
    config = optimize_for_musetalk()