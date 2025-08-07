#!/usr/bin/env python3
"""
清理Python缓存文件
"""

import os
import shutil
import sys

def clean_python_cache(root_dir='.'):
    """清理所有Python缓存文件和目录"""
    cleaned_count = 0
    
    # 清理 __pycache__ 目录
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames:
            cache_dir = os.path.join(dirpath, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                print(f"删除缓存目录: {cache_dir}")
                cleaned_count += 1
            except Exception as e:
                print(f"删除失败: {cache_dir} - {e}")
    
    # 清理 .pyc 文件
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.pyc'):
                pyc_file = os.path.join(dirpath, filename)
                try:
                    os.remove(pyc_file)
                    print(f"删除缓存文件: {pyc_file}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"删除失败: {pyc_file} - {e}")
    
    print(f"\n✅ 清理完成，共删除 {cleaned_count} 个缓存文件/目录")
    
    # 强制Python重新编译
    print("\n⚠️ 请重启Python服务以确保使用最新代码")

if __name__ == "__main__":
    # 清理当前目录和MuseTalk目录
    print("开始清理Python缓存...")
    clean_python_cache('.')
    if os.path.exists('../MuseTalk'):
        clean_python_cache('../MuseTalk')
    
    print("\n建议执行以下步骤：")
    print("1. 停止所有Python进程")
    print("2. 运行此脚本清理缓存")
    print("3. 重启应用程序")