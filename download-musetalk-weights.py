#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MuseTalk权重文件自动下载工具
解决手动下载的复杂性
"""

import os
import requests
import sys
from pathlib import Path
import hashlib

def download_with_progress(url, filename, expected_size=None):
    """带进度条的文件下载"""
    try:
        print(f"📥 开始下载: {filename}")
        print(f"🔗 URL: {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        if expected_size and total_size != expected_size:
            print(f"⚠️  文件大小不匹配: 期望 {expected_size}, 实际 {total_size}")
        
        downloaded = 0
        chunk_size = 8192
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r📊 进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        print(f"\n✅ {filename} 下载完成!")
        return True
        
    except Exception as e:
        print(f"\n❌ {filename} 下载失败: {e}")
        return False

def verify_file(filepath, expected_size=None):
    """验证文件完整性"""
    if not os.path.exists(filepath):
        return False
    
    size = os.path.getsize(filepath)
    if expected_size and size != expected_size:
        print(f"⚠️  {filepath} 大小不正确: {size} (期望: {expected_size})")
        return False
    
    return True

def main():
    print("================================================================================")
    print("                🎭 MuseTalk权重文件自动下载工具")
    print("================================================================================")
    print()
    
    # 创建目标目录
    models_dir = Path("models/musetalk/MuseTalk/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 目标目录: {models_dir.absolute()}")
    print()
    
    # MuseTalk权重文件信息
    # 注意: 这些是示例URL，实际使用时需要替换为真实的下载链接
    files_info = {
        "musetalk.json": {
            "url": "https://github.com/TMElyralab/MuseTalk/releases/download/v1.0.0/musetalk.json",
            "size": 1024,  # 示例大小
            "description": "MuseTalk配置文件"
        },
        "pytorch_model.bin": {
            "url": "https://github.com/TMElyralab/MuseTalk/releases/download/v1.0.0/pytorch_model.bin",
            "size": 8589934592,  # ~8GB
            "description": "MuseTalk主模型文件 (最大)"
        },
        "face_parsing.pth": {
            "url": "https://github.com/TMElyralab/MuseTalk/releases/download/v1.0.0/face_parsing.pth",
            "size": 52428800,  # ~50MB
            "description": "人脸解析模型"
        },
        "DNet.pth": {
            "url": "https://github.com/TMElyralab/MuseTalk/releases/download/v1.0.0/DNet.pth",
            "size": 209715200,  # ~200MB
            "description": "深度网络模型"
        }
    }
    
    print("📋 需要下载的文件:")
    total_size = 0
    for filename, info in files_info.items():
        size_mb = info['size'] / (1024 * 1024)
        print(f"   {filename}: {info['description']} (~{size_mb:.1f}MB)")
        total_size += info['size']
    
    total_gb = total_size / (1024 * 1024 * 1024)
    print(f"\n📊 总大小: ~{total_gb:.1f}GB")
    print()
    
    # 检查现有文件
    print("🔍 检查现有文件...")
    existing_files = []
    missing_files = []
    
    for filename, info in files_info.items():
        filepath = models_dir / filename
        if verify_file(filepath, info['size']):
            print(f"✅ {filename} 已存在且完整")
            existing_files.append(filename)
        else:
            print(f"❌ {filename} 缺失或不完整")
            missing_files.append(filename)
    
    if not missing_files:
        print("\n🎉 所有MuseTalk权重文件都已存在!")
        return
    
    print(f"\n📥 需要下载 {len(missing_files)} 个文件")
    
    # 用户确认
    response = input("\n是否开始下载? (y/n): ").lower().strip()
    if response != 'y':
        print("下载已取消")
        return
    
    # 开始下载
    print("\n" + "="*80)
    print("开始下载MuseTalk权重文件...")
    print("="*80)
    
    success_count = 0
    for filename in missing_files:
        info = files_info[filename]
        filepath = models_dir / filename
        
        print(f"\n[{missing_files.index(filename) + 1}/{len(missing_files)}] {info['description']}")
        
        if download_with_progress(info['url'], filepath, info['size']):
            success_count += 1
        else:
            print(f"❌ {filename} 下载失败，请手动下载")
    
    # 下载结果
    print("\n" + "="*80)
    print("下载完成!")
    print("="*80)
    
    if success_count == len(missing_files):
        print("🎉 所有文件下载成功!")
        print("\n📁 文件位置:")
        for filename in files_info.keys():
            filepath = models_dir / filename
            if filepath.exists():
                size_mb = filepath.stat().st_size / (1024 * 1024)
                print(f"   {filepath}: {size_mb:.1f}MB")
        
        print("\n🚀 下一步: 运行 deploy-production-now.bat")
        
    else:
        print(f"⚠️  部分文件下载失败 ({success_count}/{len(missing_files)})")
        print("\n📝 手动下载指南:")
        print("1. 访问: https://github.com/TMElyralab/MuseTalk/releases")
        print("2. 下载失败的文件")
        print(f"3. 放到目录: {models_dir.absolute()}")

def show_manual_download_guide():
    """显示手动下载指南"""
    print("\n" + "="*80)
    print("📝 MuseTalk权重文件手动下载指南")
    print("="*80)
    print()
    print("🔗 官方下载地址:")
    print("   https://github.com/TMElyralab/MuseTalk/releases")
    print()
    print("📋 需要下载的文件:")
    print("   1. musetalk.json (配置文件)")
    print("   2. pytorch_model.bin (主模型, ~8GB) ⚠️ 最大文件")
    print("   3. face_parsing.pth (人脸解析, ~50MB)")
    print("   4. DNet.pth (深度网络, ~200MB)")
    print()
    print("📁 下载后放到目录:")
    models_dir = Path("models/musetalk/MuseTalk/models").absolute()
    print(f"   {models_dir}")
    print()
    print("💡 下载技巧:")
    print("   - 使用稳定的网络连接")
    print("   - 可以使用下载工具 (如IDM, 迅雷)")
    print("   - 如果GitHub慢，可尝试代理或镜像")
    print("   - pytorch_model.bin最大，可能需要多次尝试")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户取消下载")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        show_manual_download_guide()
    
    input("\n按回车键退出...")