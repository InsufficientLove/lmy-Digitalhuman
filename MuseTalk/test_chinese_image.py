#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中文路径图片读取的简化脚本
"""

import sys
import os
import cv2
import numpy as np

def test_image_read(image_path):
    """测试图片读取"""
    print(f"测试图片路径: {image_path}")
    print(f"路径编码: {image_path.encode('utf-8', errors='ignore')}")
    print(f"文件存在: {os.path.exists(image_path)}")
    
    if not os.path.exists(image_path):
        # 列出目录文件
        dir_path = os.path.dirname(image_path)
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            print(f"目录中的文件: {files}")
        return False
    
    # 方法1: 直接读取
    print("尝试方法1: cv2.imread直接读取")
    img = cv2.imread(image_path)
    
    if img is not None:
        print(f"✅ 方法1成功: 图片尺寸 {img.shape}")
        return True
    
    # 方法2: numpy读取
    print("尝试方法2: numpy + cv2.imdecode")
    try:
        with open(image_path, 'rb') as f:
            img_data = f.read()
        img_array = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is not None:
            print(f"✅ 方法2成功: 图片尺寸 {img.shape}")
            return True
        else:
            print("❌ 方法2失败: 无法解码图片")
            return False
    except Exception as e:
        print(f"❌ 方法2异常: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python test_chinese_image.py <图片路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success = test_image_read(image_path)
    sys.exit(0 if success else 1)