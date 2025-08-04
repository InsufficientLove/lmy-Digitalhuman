#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Python读取中文文件名的脚本
"""

import os
import sys
import cv2
import argparse

def test_chinese_file(file_path):
    """测试读取中文文件名的文件"""
    print(f"测试文件路径: {file_path}")
    print(f"文件路径编码: {file_path.encode('utf-8')}")
    
    # 检查文件是否存在
    if os.path.exists(file_path):
        print("✅ 文件存在")
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        print(f"文件大小: {file_size} bytes")
        
        # 尝试用OpenCV读取图片
        try:
            img = cv2.imread(file_path)
            if img is not None:
                print(f"✅ OpenCV成功读取图片: {img.shape}")
                return True
            else:
                print("❌ OpenCV无法读取图片")
                return False
        except Exception as e:
            print(f"❌ OpenCV读取失败: {e}")
            return False
    else:
        print("❌ 文件不存在")
        
        # 列出目录中的文件
        dir_path = os.path.dirname(file_path)
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            print(f"目录中的文件: {files}")
        
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试中文文件名读取")
    parser.add_argument("--file_path", required=True, help="要测试的文件路径")
    
    args = parser.parse_args()
    
    print("Python环境信息:")
    print(f"Python版本: {sys.version}")
    print(f"默认编码: {sys.getdefaultencoding()}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    
    success = test_chinese_file(args.file_path)
    sys.exit(0 if success else 1)