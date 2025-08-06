#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Fast Performance Test
性能测试脚本 - 验证毫秒级响应
"""

import time
import requests
import json
import statistics

def test_performance():
    base_url = "http://localhost:5001"
    
    print("🧪 开始Ultra Fast性能测试...")
    
    # 测试参数
    test_data = {
        "templateId": "xiaoha",
        "audioText": "你好，我是小哈，欢迎测试Ultra Fast系统！"
    }
    
    response_times = []
    
    # 执行多次测试
    for i in range(5):
        print(f"📊 执行第{i+1}次测试...")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{base_url}/api/conversation/welcome",
                json=test_data,
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if response.status_code == 200:
                print(f"✅ 测试{i+1}成功: {response_time:.3f}秒")
            else:
                print(f"❌ 测试{i+1}失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试{i+1}异常: {str(e)}")
        
        # 等待间隔
        if i < 4:
            time.sleep(2)
    
    # 统计结果
    if response_times:
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print("\n📊 性能测试结果:")
        print("="*50)
        print(f"⏱️  平均响应时间: {avg_time:.3f}秒")
        print(f"⚡ 最快响应时间: {min_time:.3f}秒")
        print(f"🐌 最慢响应时间: {max_time:.3f}秒")
        print(f"🎯 目标时间: 3.000秒")
        
        if avg_time <= 3.0:
            print("🎉 性能测试通过！已达到目标性能")
        elif avg_time <= 5.0:
            print("⚠️ 性能接近目标，建议进一步优化")
        else:
            print("❌ 性能未达标，需要检查系统配置")
    else:
        print("❌ 所有测试都失败了，请检查服务状态")

if __name__ == "__main__":
    test_performance()
