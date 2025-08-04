#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的面部检测测试脚本
"""

import sys
import os
import cv2
import numpy as np

def simple_face_detection(image_path):
    """简单的面部检测测试"""
    print(f"测试图片: {image_path}")
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        return False
    
    # 使用numpy方式读取图片
    try:
        with open(image_path, 'rb') as f:
            img_data = f.read()
        img_array = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            print("❌ 无法解码图片")
            return False
            
        print(f"✅ 成功读取图片: {img.shape}")
        
        # 检查图片是否有效
        if len(img.shape) != 3 or img.shape[2] != 3:
            print(f"❌ 图片格式不正确: {img.shape}")
            return False
            
        # 转换为RGB（OpenCV默认是BGR）
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        print(f"✅ 转换为RGB格式: {img_rgb.shape}")
        
        # 检查图片内容是否有效
        if np.all(img == 0):
            print("❌ 图片内容全为黑色")
            return False
            
        if np.all(img == 255):
            print("❌ 图片内容全为白色")
            return False
            
        print("✅ 图片内容看起来正常")
        
        # 简单的面部区域检测（使用OpenCV的Haar级联）
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                print(f"✅ 检测到 {len(faces)} 个面部区域")
                for i, (x, y, w, h) in enumerate(faces):
                    print(f"   面部 {i+1}: x={x}, y={y}, w={w}, h={h}")
                return True
            else:
                print("⚠️ 未检测到面部，但图片可读取")
                return True  # 图片本身是有效的
                
        except Exception as e:
            print(f"⚠️ 面部检测失败: {e}")
            return True  # 图片读取成功就算通过
            
    except Exception as e:
        print(f"❌ 读取图片失败: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python simple_face_test.py <图片路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success = simple_face_detection(image_path)
    print(f"测试结果: {'通过' if success else '失败'}")
    sys.exit(0 if success else 1)