#!/usr/bin/env python3
"""
面部检测测试脚本
用于验证MuseTalk面部检测功能是否正常工作
"""

import os
import sys
import cv2
import numpy as np

# 动态添加MuseTalk路径到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
musetalk_dir = os.path.join(current_dir, "MuseTalk")

if os.path.exists(musetalk_dir) and musetalk_dir not in sys.path:
    sys.path.insert(0, musetalk_dir)
    print(f"Added MuseTalk path: {musetalk_dir}")

def test_musetalk_imports():
    """测试MuseTalk模块导入"""
    try:
        from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
        print("✅ get_landmark_and_bbox 导入成功")
        
        from musetalk.utils.blending import get_image_prepare_material, get_image_blending
        print("✅ get_image_prepare_material 导入成功")
        
        from musetalk.utils.utils import load_all_model
        print("✅ load_all_model 导入成功")
        
        return True
    except ImportError as e:
        print(f"❌ MuseTalk导入失败: {e}")
        return False

def test_face_detection(image_path):
    """测试面部检测功能"""
    try:
        from musetalk.utils.preprocessing import get_landmark_and_bbox
        
        if not os.path.exists(image_path):
            print(f"❌ 图片文件不存在: {image_path}")
            return False
        
        print(f"📸 测试图片: {image_path}")
        
        # 检查图片是否可以读取
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ 无法读取图片: {image_path}")
            return False
        
        print(f"✅ 图片读取成功，尺寸: {img.shape}")
        
        # 调用面部检测
        print("🎯 调用get_landmark_and_bbox进行面部检测...")
        coord_list, frame_list = get_landmark_and_bbox([image_path], 0)
        
        print(f"📊 检测结果:")
        print(f"  - coord_list长度: {len(coord_list) if coord_list else 0}")
        print(f"  - frame_list长度: {len(frame_list) if frame_list else 0}")
        
        if coord_list and len(coord_list) > 0:
            bbox = coord_list[0]
            x1, y1, x2, y2 = bbox
            print(f"  - 边界框: ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
            
            if x1 < x2 and y1 < y2 and bbox != (0.0, 0.0, 0.0, 0.0):
                print("✅ 面部检测成功！")
                return True
            else:
                print("⚠️ 检测到无效的面部边界框")
                return False
        else:
            print("⚠️ 未检测到面部区域")
            return False
            
    except Exception as e:
        print(f"❌ 面部检测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 开始MuseTalk面部检测测试...")
    
    # 测试模块导入
    print("\n1. 测试模块导入...")
    if not test_musetalk_imports():
        print("❌ 模块导入失败，请检查MuseTalk安装")
        return 1
    
    # 测试面部检测（如果有测试图片）
    test_images = [
        "LmyDigitalHuman/wwwroot/templates/xiaoha.jpg",
        "test_image.jpg",
        "sample.jpg"
    ]
    
    print("\n2. 测试面部检测...")
    success = False
    
    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\n📁 找到测试图片: {image_path}")
            if test_face_detection(image_path):
                success = True
                break
        else:
            print(f"⚪ 测试图片不存在: {image_path}")
    
    if not success:
        print("\n⚠️ 没有找到可用的测试图片或面部检测失败")
        print("请确保有包含清晰人脸的图片用于测试")
        return 1
    
    print("\n✅ 所有测试通过！")
    return 0

if __name__ == "__main__":
    exit(main())