"""
GPU配置和优化设置
"""

import torch

# GPU内存优化配置
GPU_MEMORY_CONFIG = {
    # 批次大小配置
    'batch_size': {
        'default': 8,  # 默认批次大小（48GB单卡建议）
        'min': 1,      # 最小批次大小
        'max': 12,     # 最大批次大小
    },
    
    # 内存管理
    'memory_fraction': 0.9,  # 每个GPU使用的最大内存比例（48GB 预留10%）
    'max_split_size_mb': 256,  # PyTorch内存分配块大小
    
    # 并发控制
    'max_concurrent_batches_per_gpu': 2,  # 单卡并发批次
    
    # 内存清理
    'aggressive_cleanup': True,  # 激进的内存清理模式
    'cleanup_interval': 2,  # 每处理2个批次后强制清理内存
}

def configure_gpu_memory():
    """配置GPU内存使用"""
    # 设置PyTorch内存分配策略
    import os
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = f'max_split_size_mb:{GPU_MEMORY_CONFIG["max_split_size_mb"]}'
    
    # 设置每个GPU的内存限制
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            torch.cuda.set_per_process_memory_fraction(
                GPU_MEMORY_CONFIG['memory_fraction'], 
                device=i
            )
    
    print(f"GPU内存配置完成:")
    print(f"  - 批次大小: {GPU_MEMORY_CONFIG['batch_size']['default']}")
    print(f"  - 内存使用比例: {GPU_MEMORY_CONFIG['memory_fraction'] * 100}%")
    print(f"  - 内存块大小: {GPU_MEMORY_CONFIG['max_split_size_mb']}MB")

def get_optimal_batch_size(gpu_memory_gb=24):
    """根据GPU内存动态计算最优批次大小"""
    # 基于GPU内存的批次大小推荐
    memory_to_batch = {
        8: 2,    # 8GB GPU
        12: 3,   # 12GB GPU
        16: 4,   # 16GB GPU
        24: 4,   # 24GB GPU (保守设置)
        32: 6,   # 32GB GPU
        40: 8,   # 40GB GPU
        48: 10,  # 48GB GPU
    }
    
    # 找到最接近的内存配置
    for mem, batch in sorted(memory_to_batch.items()):
        if gpu_memory_gb <= mem:
            return batch
    
    return GPU_MEMORY_CONFIG['batch_size']['default']

def monitor_gpu_memory():
    """监控GPU内存使用情况"""
    if not torch.cuda.is_available():
        return {}
    
    memory_info = {}
    for i in range(torch.cuda.device_count()):
        allocated = torch.cuda.memory_allocated(i) / 1024**3  # GB
        reserved = torch.cuda.memory_reserved(i) / 1024**3    # GB
        total = torch.cuda.get_device_properties(i).total_memory / 1024**3  # GB
        
        memory_info[f'cuda:{i}'] = {
            'allocated_gb': round(allocated, 2),
            'reserved_gb': round(reserved, 2),
            'total_gb': round(total, 2),
            'free_gb': round(total - reserved, 2),
            'usage_percent': round((reserved / total) * 100, 1)
        }
    
    return memory_info