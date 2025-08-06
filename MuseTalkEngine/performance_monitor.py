#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Monitor and Optimizer
实时性能监控和优化器 - 确保毫秒级响应
"""

import os
import sys
import time
import threading
import psutil
import torch
import GPUtil
import json
from collections import deque, defaultdict
import statistics
import warnings
warnings.filterwarnings("ignore")

class PerformanceMonitor:
    """性能监控器 - 实时跟踪和优化"""
    
    def __init__(self, max_history=100):
        self.max_history = max_history
        
        # 性能指标历史
        self.inference_times = deque(maxlen=max_history)
        self.compose_times = deque(maxlen=max_history)
        self.video_times = deque(maxlen=max_history)
        self.total_times = deque(maxlen=max_history)
        
        # GPU使用率历史
        self.gpu_usage_history = defaultdict(lambda: deque(maxlen=max_history))
        self.gpu_memory_history = defaultdict(lambda: deque(maxlen=max_history))
        
        # 系统资源历史
        self.cpu_usage_history = deque(maxlen=max_history)
        self.memory_usage_history = deque(maxlen=max_history)
        
        # 性能阈值
        self.target_total_time = 3.0  # 目标总时间 3秒
        self.warning_total_time = 5.0  # 警告阈值 5秒
        self.critical_total_time = 10.0  # 严重阈值 10秒
        
        # 优化建议
        self.optimization_suggestions = []
        
        # 监控线程
        self.monitoring_thread = None
        self.is_monitoring = False
        
    def start_monitoring(self, interval=1.0):
        """启动性能监控"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        print("🔍 性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        print("🛑 性能监控已停止")
    
    def _monitoring_loop(self, interval):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 监控CPU使用率
                cpu_usage = psutil.cpu_percent(interval=0.1)
                self.cpu_usage_history.append(cpu_usage)
                
                # 监控内存使用率
                memory_info = psutil.virtual_memory()
                self.memory_usage_history.append(memory_info.percent)
                
                # 监控GPU使用率
                try:
                    gpus = GPUtil.getGPUs()
                    for i, gpu in enumerate(gpus):
                        self.gpu_usage_history[i].append(gpu.load * 100)
                        self.gpu_memory_history[i].append(gpu.memoryUtil * 100)
                except:
                    pass
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"⚠️ 监控异常: {str(e)}")
                time.sleep(interval)
    
    def record_inference_time(self, inference_time, compose_time, video_time, total_time):
        """记录推理时间"""
        self.inference_times.append(inference_time)
        self.compose_times.append(compose_time)
        self.video_times.append(video_time)
        self.total_times.append(total_time)
        
        # 分析性能
        self._analyze_performance()
    
    def _analyze_performance(self):
        """分析性能并生成建议"""
        if len(self.total_times) < 5:
            return
            
        recent_times = list(self.total_times)[-5:]
        avg_time = statistics.mean(recent_times)
        
        # 清空旧建议
        self.optimization_suggestions.clear()
        
        # 性能分析
        if avg_time > self.critical_total_time:
            self.optimization_suggestions.append("🚨 严重性能问题：平均处理时间超过10秒")
            self._generate_critical_optimizations()
        elif avg_time > self.warning_total_time:
            self.optimization_suggestions.append("⚠️ 性能警告：平均处理时间超过5秒")
            self._generate_warning_optimizations()
        elif avg_time > self.target_total_time:
            self.optimization_suggestions.append("📊 性能提示：处理时间超过目标3秒")
            self._generate_target_optimizations()
        else:
            self.optimization_suggestions.append("✅ 性能良好：处理时间在目标范围内")
        
        # GPU使用率分析
        self._analyze_gpu_usage()
        
        # 内存使用率分析
        self._analyze_memory_usage()
    
    def _generate_critical_optimizations(self):
        """生成严重性能问题的优化建议"""
        self.optimization_suggestions.extend([
            "🔧 建议1: 减少批次大小到8或更小",
            "🔧 建议2: 启用模型量化（FP16）",
            "🔧 建议3: 增加GPU内存清理频率",
            "🔧 建议4: 检查是否有其他程序占用GPU",
            "🔧 建议5: 考虑降低视频分辨率或帧率"
        ])
    
    def _generate_warning_optimizations(self):
        """生成性能警告的优化建议"""
        self.optimization_suggestions.extend([
            "🔧 建议1: 优化批次大小到12-16",
            "🔧 建议2: 启用并行图像合成",
            "🔧 建议3: 使用更快的视频编码器",
            "🔧 建议4: 检查GPU负载均衡"
        ])
    
    def _generate_target_optimizations(self):
        """生成目标性能的优化建议"""
        self.optimization_suggestions.extend([
            "🔧 建议1: 可以尝试增加批次大小到20-24",
            "🔧 建议2: 启用模型编译优化",
            "🔧 建议3: 优化内存缓存策略"
        ])
    
    def _analyze_gpu_usage(self):
        """分析GPU使用率"""
        try:
            for gpu_id, usage_history in self.gpu_usage_history.items():
                if len(usage_history) >= 5:
                    recent_usage = list(usage_history)[-5:]
                    avg_usage = statistics.mean(recent_usage)
                    
                    if avg_usage < 50:
                        self.optimization_suggestions.append(
                            f"📊 GPU{gpu_id}使用率偏低({avg_usage:.1f}%)，可以增加负载"
                        )
                    elif avg_usage > 95:
                        self.optimization_suggestions.append(
                            f"⚠️ GPU{gpu_id}使用率过高({avg_usage:.1f}%)，可能需要负载均衡"
                        )
        except:
            pass
    
    def _analyze_memory_usage(self):
        """分析内存使用率"""
        if len(self.memory_usage_history) >= 5:
            recent_memory = list(self.memory_usage_history)[-5:]
            avg_memory = statistics.mean(recent_memory)
            
            if avg_memory > 90:
                self.optimization_suggestions.append(
                    f"⚠️ 系统内存使用率过高({avg_memory:.1f}%)，建议增加内存或优化缓存"
                )
            elif avg_memory > 80:
                self.optimization_suggestions.append(
                    f"📊 系统内存使用率较高({avg_memory:.1f}%)，注意内存管理"
                )
    
    def get_performance_report(self):
        """获取性能报告"""
        if not self.total_times:
            return "📊 暂无性能数据"
        
        # 基本统计
        recent_times = list(self.total_times)[-10:] if len(self.total_times) >= 10 else list(self.total_times)
        avg_time = statistics.mean(recent_times)
        min_time = min(recent_times)
        max_time = max(recent_times)
        
        # GPU信息
        gpu_info = ""
        try:
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                gpu_info += f"GPU{i}: {gpu.load*100:.1f}% 使用率, {gpu.memoryUtil*100:.1f}% 显存\n"
        except:
            gpu_info = "GPU信息获取失败\n"
        
        report = f"""
📊 性能报告 (最近{len(recent_times)}次推理)
{'='*50}
⏱️  平均处理时间: {avg_time:.3f}秒
⚡ 最快处理时间: {min_time:.3f}秒
🐌 最慢处理时间: {max_time:.3f}秒
🎯 目标时间: {self.target_total_time:.1f}秒

📈 系统资源使用率:
💻 CPU使用率: {list(self.cpu_usage_history)[-1] if self.cpu_usage_history else 0:.1f}%
🧠 内存使用率: {list(self.memory_usage_history)[-1] if self.memory_usage_history else 0:.1f}%
{gpu_info}

🔧 优化建议:
"""
        
        for i, suggestion in enumerate(self.optimization_suggestions, 1):
            report += f"{suggestion}\n"
        
        return report
    
    def get_performance_json(self):
        """获取JSON格式的性能数据"""
        if not self.total_times:
            return {}
        
        recent_times = list(self.total_times)[-10:] if len(self.total_times) >= 10 else list(self.total_times)
        
        data = {
            "performance": {
                "average_time": statistics.mean(recent_times),
                "min_time": min(recent_times),
                "max_time": max(recent_times),
                "target_time": self.target_total_time,
                "sample_count": len(recent_times)
            },
            "system_resources": {
                "cpu_usage": list(self.cpu_usage_history)[-1] if self.cpu_usage_history else 0,
                "memory_usage": list(self.memory_usage_history)[-1] if self.memory_usage_history else 0
            },
            "gpu_resources": {},
            "optimizations": self.optimization_suggestions
        }
        
        # GPU数据
        try:
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                data["gpu_resources"][f"gpu_{i}"] = {
                    "usage": gpu.load * 100,
                    "memory": gpu.memoryUtil * 100,
                    "temperature": gpu.temperature
                }
        except:
            pass
        
        return data
    
    def save_performance_log(self, filename="performance_log.json"):
        """保存性能日志"""
        try:
            log_data = {
                "timestamp": time.time(),
                "performance_data": self.get_performance_json(),
                "inference_times": list(self.inference_times),
                "compose_times": list(self.compose_times),
                "video_times": list(self.video_times),
                "total_times": list(self.total_times)
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"📊 性能日志已保存: {filename}")
            
        except Exception as e:
            print(f"❌ 保存性能日志失败: {str(e)}")

# 全局性能监控器实例
global_monitor = PerformanceMonitor()

def start_performance_monitoring():
    """启动全局性能监控"""
    global_monitor.start_monitoring()

def stop_performance_monitoring():
    """停止全局性能监控"""
    global_monitor.stop_monitoring()

def record_performance(inference_time, compose_time, video_time, total_time):
    """记录性能数据"""
    global_monitor.record_inference_time(inference_time, compose_time, video_time, total_time)

def get_performance_report():
    """获取性能报告"""
    return global_monitor.get_performance_report()

def print_performance_report():
    """打印性能报告"""
    print(global_monitor.get_performance_report())

if __name__ == "__main__":
    # 测试性能监控器
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # 模拟一些性能数据
    import random
    for i in range(10):
        inference_time = random.uniform(0.5, 2.0)
        compose_time = random.uniform(1.0, 5.0)
        video_time = random.uniform(0.5, 2.0)
        total_time = inference_time + compose_time + video_time
        
        monitor.record_inference_time(inference_time, compose_time, video_time, total_time)
        time.sleep(1)
    
    print(monitor.get_performance_report())
    monitor.save_performance_log()
    monitor.stop_monitoring()