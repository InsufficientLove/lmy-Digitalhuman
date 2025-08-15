#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU Benchmark Script for MuseTalk
测试单张RTX 4090D 48GB和4张RTX 4090 24GB的性能
"""

import os
import sys
import time
import json
import torch
import numpy as np
import psutil
import argparse
from datetime import datetime
from typing import List, Dict, Tuple
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

# 添加路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'MuseTalkEngine'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'MuseTalk'))

from multi_gpu_parallel_engine import MultiGPUParallelEngine, GPUConfig, create_gpu_config


class GPUBenchmark:
    """GPU性能基准测试"""
    
    def __init__(self, config_name: str = "auto"):
        self.config_name = config_name
        self.results = {
            'config': {},
            'system_info': {},
            'benchmarks': [],
            'summary': {}
        }
        
        # 检测GPU配置
        self._detect_gpu_config()
        
    def _detect_gpu_config(self):
        """检测GPU配置"""
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA不可用，无法运行GPU基准测试")
        
        num_gpus = torch.cuda.device_count()
        gpu_info = []
        total_memory = 0
        
        for i in range(num_gpus):
            props = torch.cuda.get_device_properties(i)
            memory_gb = props.total_memory / (1024**3)
            gpu_info.append({
                'id': i,
                'name': props.name,
                'memory_gb': round(memory_gb, 1),
                'compute_capability': f"{props.major}.{props.minor}",
                'multi_processor_count': props.multi_processor_count
            })
            total_memory += memory_gb
        
        self.results['system_info'] = {
            'num_gpus': num_gpus,
            'total_gpu_memory_gb': round(total_memory, 1),
            'gpu_details': gpu_info,
            'cuda_version': torch.version.cuda,
            'pytorch_version': torch.__version__,
            'cpu_count': psutil.cpu_count(),
            'ram_gb': round(psutil.virtual_memory().total / (1024**3), 1)
        }
        
        # 自动判断配置类型
        if self.config_name == "auto":
            if num_gpus == 1 and gpu_info[0]['memory_gb'] >= 40:
                self.config_name = "single_4090d_48gb"
            elif num_gpus >= 4 and all(g['memory_gb'] >= 20 for g in gpu_info[:4]):
                self.config_name = "quad_4090_24gb"
            else:
                self.config_name = "custom"
        
        print(f"检测到 {num_gpus} 个GPU")
        for gpu in gpu_info:
            print(f"  GPU {gpu['id']}: {gpu['name']}, {gpu['memory_gb']}GB")
        print(f"使用配置: {self.config_name}")
    
    def create_engine_config(self) -> GPUConfig:
        """创建引擎配置"""
        num_gpus = self.results['system_info']['num_gpus']
        
        if self.config_name == "single_4090d_48gb":
            # 单张RTX 4090D 48GB配置
            config = create_gpu_config(
                gpu_ids=[0],
                batch_size_per_gpu=20,  # 48GB可以处理更大批次
                memory_fraction=0.95,
                enable_amp=True,
                enable_cudnn_benchmark=True
            )
            print("配置: 单张RTX 4090D 48GB")
            print("  - 批次大小: 20")
            print("  - 内存使用: 95%")
            
        elif self.config_name == "quad_4090_24gb":
            # 4张RTX 4090 24GB配置
            config = create_gpu_config(
                gpu_ids=list(range(min(4, num_gpus))),
                batch_size_per_gpu=8,  # 每个24GB GPU的批次大小
                memory_fraction=0.9,
                enable_amp=True,
                enable_cudnn_benchmark=True
            )
            print("配置: 4张RTX 4090 24GB")
            print(f"  - GPU数量: {min(4, num_gpus)}")
            print("  - 每GPU批次大小: 8")
            print("  - 总批次大小: 32")
            print("  - 内存使用: 90%")
            
        else:
            # 自定义配置
            batch_size = self._estimate_batch_size()
            config = create_gpu_config(
                gpu_ids=list(range(num_gpus)),
                batch_size_per_gpu=batch_size,
                memory_fraction=0.85,
                enable_amp=True,
                enable_cudnn_benchmark=True
            )
            print(f"自定义配置: {num_gpus} GPUs")
            print(f"  - 每GPU批次大小: {batch_size}")
        
        self.results['config'] = {
            'name': self.config_name,
            'gpu_ids': config.gpu_ids,
            'batch_size_per_gpu': config.batch_size_per_gpu,
            'total_batch_size': config.batch_size_per_gpu * len(config.gpu_ids),
            'memory_fraction': config.memory_fraction
        }
        
        return config
    
    def _estimate_batch_size(self) -> int:
        """估算批次大小"""
        # 基于最小GPU内存估算
        min_memory = min(g['memory_gb'] for g in self.results['system_info']['gpu_details'])
        
        if min_memory >= 40:
            return 16
        elif min_memory >= 24:
            return 8
        elif min_memory >= 16:
            return 4
        elif min_memory >= 12:
            return 3
        else:
            return 2
    
    def run_latency_test(self, engine: MultiGPUParallelEngine, num_samples: int = 100):
        """延迟测试"""
        print(f"\n运行延迟测试 ({num_samples} 样本)...")
        
        latencies = []
        
        for i in range(num_samples):
            data = {'id': i, 'timestamp': time.time()}
            
            start_time = time.perf_counter()
            result = engine.process_batch_parallel([data], strategy='round_robin')
            end_time = time.perf_counter()
            
            latency = (end_time - start_time) * 1000  # 转换为毫秒
            latencies.append(latency)
            
            if (i + 1) % 20 == 0:
                print(f"  处理 {i + 1}/{num_samples} 样本...")
        
        # 计算统计
        latencies = np.array(latencies)
        stats = {
            'mean_ms': float(np.mean(latencies)),
            'median_ms': float(np.median(latencies)),
            'std_ms': float(np.std(latencies)),
            'min_ms': float(np.min(latencies)),
            'max_ms': float(np.max(latencies)),
            'p50_ms': float(np.percentile(latencies, 50)),
            'p95_ms': float(np.percentile(latencies, 95)),
            'p99_ms': float(np.percentile(latencies, 99))
        }
        
        print(f"延迟测试完成:")
        print(f"  - 平均延迟: {stats['mean_ms']:.2f} ms")
        print(f"  - P50延迟: {stats['p50_ms']:.2f} ms")
        print(f"  - P95延迟: {stats['p95_ms']:.2f} ms")
        print(f"  - P99延迟: {stats['p99_ms']:.2f} ms")
        
        return stats
    
    def run_throughput_test(self, engine: MultiGPUParallelEngine, 
                           batch_sizes: List[int] = None,
                           duration_seconds: int = 30):
        """吞吐量测试"""
        if batch_sizes is None:
            total_batch = self.results['config']['total_batch_size']
            batch_sizes = [1, total_batch // 4, total_batch // 2, total_batch, total_batch * 2]
        
        throughput_results = []
        
        for batch_size in batch_sizes:
            print(f"\n测试批次大小 {batch_size} (运行 {duration_seconds} 秒)...")
            
            # 准备测试数据
            test_data = [{'id': i, 'data': f'test_{i}'} for i in range(batch_size)]
            
            processed_count = 0
            start_time = time.perf_counter()
            end_time = start_time + duration_seconds
            
            while time.perf_counter() < end_time:
                results = engine.process_batch_parallel(test_data, strategy='data_parallel')
                processed_count += len(results)
            
            elapsed_time = time.perf_counter() - start_time
            throughput = processed_count / elapsed_time
            
            result = {
                'batch_size': batch_size,
                'processed_count': processed_count,
                'duration_seconds': elapsed_time,
                'throughput_per_second': throughput,
                'avg_batch_time_ms': (elapsed_time / (processed_count / batch_size)) * 1000
            }
            
            throughput_results.append(result)
            
            print(f"  - 处理数量: {processed_count}")
            print(f"  - 吞吐量: {throughput:.2f} 样本/秒")
            print(f"  - 平均批次时间: {result['avg_batch_time_ms']:.2f} ms")
        
        return throughput_results
    
    def run_parallel_efficiency_test(self, engine: MultiGPUParallelEngine):
        """并行效率测试"""
        print("\n运行并行效率测试...")
        
        strategies = ['round_robin', 'load_balance', 'data_parallel']
        batch_size = self.results['config']['total_batch_size']
        test_data = [{'id': i, 'data': f'test_{i}'} for i in range(batch_size * 10)]
        
        efficiency_results = []
        
        for strategy in strategies:
            print(f"  测试策略: {strategy}")
            
            # 预热
            _ = engine.process_batch_parallel(test_data[:batch_size], strategy=strategy)
            
            # 正式测试
            start_time = time.perf_counter()
            results = engine.process_batch_parallel(test_data, strategy=strategy)
            end_time = time.perf_counter()
            
            elapsed_time = end_time - start_time
            throughput = len(results) / elapsed_time
            
            result = {
                'strategy': strategy,
                'elapsed_time': elapsed_time,
                'throughput': throughput,
                'samples_processed': len(results)
            }
            
            efficiency_results.append(result)
            
            print(f"    - 时间: {elapsed_time:.2f} 秒")
            print(f"    - 吞吐量: {throughput:.2f} 样本/秒")
        
        return efficiency_results
    
    def run_memory_stress_test(self, engine: MultiGPUParallelEngine):
        """内存压力测试"""
        print("\n运行内存压力测试...")
        
        max_batch = self.results['config']['total_batch_size']
        test_sizes = [max_batch, max_batch * 2, max_batch * 4]
        
        memory_results = []
        
        for test_size in test_sizes:
            print(f"  测试大小: {test_size} 样本")
            
            # 清理内存
            gc.collect()
            torch.cuda.empty_cache()
            
            # 记录初始内存
            initial_memory = {}
            for gpu_id in engine.config.gpu_ids:
                initial_memory[gpu_id] = torch.cuda.memory_allocated(gpu_id) / (1024**3)
            
            try:
                # 运行测试
                test_data = [{'id': i, 'data': f'test_{i}'} for i in range(test_size)]
                start_time = time.perf_counter()
                results = engine.process_batch_parallel(test_data, strategy='data_parallel')
                end_time = time.perf_counter()
                
                # 记录峰值内存
                peak_memory = {}
                for gpu_id in engine.config.gpu_ids:
                    peak_memory[gpu_id] = torch.cuda.max_memory_allocated(gpu_id) / (1024**3)
                
                result = {
                    'test_size': test_size,
                    'success': True,
                    'elapsed_time': end_time - start_time,
                    'initial_memory_gb': initial_memory,
                    'peak_memory_gb': peak_memory,
                    'memory_increase_gb': {
                        gpu_id: peak_memory[gpu_id] - initial_memory[gpu_id] 
                        for gpu_id in engine.config.gpu_ids
                    }
                }
                
                print(f"    - 成功: 耗时 {result['elapsed_time']:.2f} 秒")
                for gpu_id in engine.config.gpu_ids:
                    print(f"    - GPU {gpu_id} 内存增加: {result['memory_increase_gb'][gpu_id]:.2f} GB")
                
            except Exception as e:
                result = {
                    'test_size': test_size,
                    'success': False,
                    'error': str(e)
                }
                print(f"    - 失败: {e}")
            
            memory_results.append(result)
            
            # 清理
            gc.collect()
            torch.cuda.empty_cache()
        
        return memory_results
    
    def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("\n" + "="*60)
        print("开始GPU基准测试")
        print("="*60)
        
        # 创建配置
        config = self.create_engine_config()
        
        # 创建引擎
        print("\n初始化Multi-GPU引擎...")
        engine = MultiGPUParallelEngine(config)
        
        try:
            # 运行各项测试
            benchmark_results = {}
            
            # 1. 延迟测试
            print("\n[1/4] 延迟测试")
            benchmark_results['latency'] = self.run_latency_test(engine)
            
            # 2. 吞吐量测试
            print("\n[2/4] 吞吐量测试")
            benchmark_results['throughput'] = self.run_throughput_test(engine)
            
            # 3. 并行效率测试
            print("\n[3/4] 并行效率测试")
            benchmark_results['parallel_efficiency'] = self.run_parallel_efficiency_test(engine)
            
            # 4. 内存压力测试
            print("\n[4/4] 内存压力测试")
            benchmark_results['memory_stress'] = self.run_memory_stress_test(engine)
            
            # 获取性能报告
            performance_report = engine.get_performance_report()
            
            # 汇总结果
            self.results['benchmarks'] = benchmark_results
            self.results['performance_report'] = performance_report
            
            # 计算总结
            self._calculate_summary()
            
            # 打印总结
            self._print_summary()
            
            # 保存结果
            self._save_results()
            
        finally:
            # 清理
            engine.cleanup()
    
    def _calculate_summary(self):
        """计算总结统计"""
        benchmarks = self.results['benchmarks']
        
        # 找出最佳吞吐量
        best_throughput = max(
            benchmarks['throughput'], 
            key=lambda x: x['throughput_per_second']
        )
        
        # 找出最佳策略
        best_strategy = max(
            benchmarks['parallel_efficiency'],
            key=lambda x: x['throughput']
        )
        
        self.results['summary'] = {
            'config_name': self.config_name,
            'num_gpus': len(self.results['config']['gpu_ids']),
            'total_batch_size': self.results['config']['total_batch_size'],
            'avg_latency_ms': benchmarks['latency']['mean_ms'],
            'p99_latency_ms': benchmarks['latency']['p99_ms'],
            'best_throughput': best_throughput['throughput_per_second'],
            'best_batch_size': best_throughput['batch_size'],
            'best_strategy': best_strategy['strategy'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("基准测试总结")
        print("="*60)
        
        summary = self.results['summary']
        
        print(f"\n配置: {summary['config_name']}")
        print(f"GPU数量: {summary['num_gpus']}")
        print(f"总批次大小: {summary['total_batch_size']}")
        
        print(f"\n性能指标:")
        print(f"  - 平均延迟: {summary['avg_latency_ms']:.2f} ms")
        print(f"  - P99延迟: {summary['p99_latency_ms']:.2f} ms")
        print(f"  - 最佳吞吐量: {summary['best_throughput']:.2f} 样本/秒")
        print(f"  - 最佳批次大小: {summary['best_batch_size']}")
        print(f"  - 最佳并行策略: {summary['best_strategy']}")
        
        # 性能等级评估
        if summary['avg_latency_ms'] < 50 and summary['best_throughput'] > 100:
            grade = "优秀 (生产就绪)"
        elif summary['avg_latency_ms'] < 100 and summary['best_throughput'] > 50:
            grade = "良好 (可用于生产)"
        elif summary['avg_latency_ms'] < 200 and summary['best_throughput'] > 20:
            grade = "中等 (需要优化)"
        else:
            grade = "需要改进"
        
        print(f"\n性能等级: {grade}")
    
    def _save_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{self.config_name}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存到: {filename}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GPU基准测试')
    parser.add_argument('--config', type=str, default='auto',
                       choices=['auto', 'single_4090d_48gb', 'quad_4090_24gb', 'custom'],
                       help='GPU配置类型')
    parser.add_argument('--quick', action='store_true',
                       help='快速测试模式（减少测试样本）')
    
    args = parser.parse_args()
    
    # 创建基准测试
    benchmark = GPUBenchmark(config_name=args.config)
    
    # 运行测试
    try:
        benchmark.run_all_benchmarks()
        print("\n✅ 基准测试完成!")
    except Exception as e:
        print(f"\n❌ 基准测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())