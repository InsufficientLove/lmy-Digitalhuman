#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时系统测试脚本
验证预处理 + 推理流程
"""

import os
import sys
import time
import requests
from pathlib import Path

def test_preprocessing():
    """测试预处理功能"""
    print("\n" + "=" * 60)
    print("测试 1: 视频预处理")
    print("=" * 60)
    
    # 检查是否有测试视频
    test_video = Path("./data/video/idle.mp4")
    if not test_video.exists():
        print(f"⚠️ 测试视频不存在: {test_video}")
        print("请先准备测试视频")
        return False
    
    # 运行预处理
    import subprocess
    cmd = [
        "python", "preprocess_assets.py",
        "--video", str(test_video),
        "--output", "./data/preprocessed"
    ]
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    start = time.time()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start
    
    print(result.stdout)
    if result.stderr:
        print("错误输出:", result.stderr)
    
    if result.returncode == 0:
        print(f"✅ 预处理成功 (耗时: {elapsed:.2f}s)")
        
        # 检查输出文件
        pkl_file = Path("./data/preprocessed/idle_bbox.pkl")
        json_file = Path("./data/preprocessed/idle_bbox.json")
        
        if pkl_file.exists() and json_file.exists():
            print(f"✅ 输出文件已生成:")
            print(f"   - {pkl_file} ({pkl_file.stat().st_size / 1024:.1f} KB)")
            print(f"   - {json_file} ({json_file.stat().st_size / 1024:.1f} KB)")
            return True
        else:
            print("❌ 输出文件未生成")
            return False
    else:
        print(f"❌ 预处理失败 (返回码: {result.returncode})")
        return False


def test_service_startup():
    """测试服务启动"""
    print("\n" + "=" * 60)
    print("测试 2: 服务启动")
    print("=" * 60)
    
    print("⚠️ 请在另一个终端手动启动服务:")
    print("   python main_realtime.py")
    print()
    print("然后按回车继续测试...")
    input()
    
    # 测试健康检查
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 服务运行中:")
            print(f"   - 状态: {data.get('status')}")
            print(f"   - 设备: {data.get('device')}")
            print(f"   - 数据类型: {data.get('dtype')}")
            print(f"   - 已加载资产: {data.get('loaded_assets')}")
            return True
        else:
            print(f"❌ 服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        return False


def test_inference():
    """测试推理功能"""
    print("\n" + "=" * 60)
    print("测试 3: 推理功能")
    print("=" * 60)
    
    # 检查测试音频
    test_audio = Path("./test_audio.wav")
    if not test_audio.exists():
        print(f"⚠️ 测试音频不存在: {test_audio}")
        print("跳过推理测试")
        return None
    
    # 发送推理请求
    try:
        print(f"📤 发送推理请求...")
        start = time.time()
        
        with open(test_audio, 'rb') as f:
            files = {'audio': ('test.wav', f, 'audio/wav')}
            data = {
                'asset_id': 'idle',
                'fps': 25,
                'batch_size': 8
            }
            
            response = requests.post(
                "http://localhost:8000/stream",
                files=files,
                data=data,
                stream=True,
                timeout=60
            )
        
        if response.status_code == 200:
            # 保存前几帧用于验证
            output_file = Path("./test_output.mjpeg")
            with open(output_file, 'wb') as f:
                count = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    count += 1
                    if count > 100:  # 只保存前 100 个块
                        break
            
            elapsed = time.time() - start
            print(f"✅ 推理成功 (耗时: {elapsed:.2f}s)")
            print(f"   输出文件: {output_file} ({output_file.stat().st_size / 1024:.1f} KB)")
            return True
        else:
            print(f"❌ 推理失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ 推理请求异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_asset_loading():
    """测试资产加载"""
    print("\n" + "=" * 60)
    print("测试 4: 资产管理")
    print("=" * 60)
    
    try:
        # 列出资产
        response = requests.get("http://localhost:8000/assets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            assets = data.get('assets', [])
            print(f"✅ 当前已加载 {len(assets)} 个资产:")
            for asset in assets:
                print(f"   - {asset['id']}: {asset['frame_count']} 帧, {asset['fps']} FPS")
            return True
        else:
            print(f"❌ 获取资产列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 资产管理测试失败: {e}")
        return False


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("🧪 MuseTalk 实时系统测试")
    print("=" * 60)
    
    results = {
        "预处理": None,
        "服务启动": None,
        "推理功能": None,
        "资产管理": None
    }
    
    # 测试 1: 预处理
    results["预处理"] = test_preprocessing()
    
    # 测试 2: 服务启动
    results["服务启动"] = test_service_startup()
    
    if results["服务启动"]:
        # 测试 3: 推理
        results["推理功能"] = test_inference()
        
        # 测试 4: 资产管理
        results["资产管理"] = test_asset_loading()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    for name, result in results.items():
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️ 跳过"
        print(f"  {name}: {status}")
    
    # 统计
    passed = sum(1 for r in results.values() if r is True)
    total = len([r for r in results.values() if r is not None])
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print("\n⚠️ 部分测试未通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
