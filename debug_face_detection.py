# -*- coding: utf-8 -*-
"""
调试面部检测脚本
专门用来测试小哈.jpg的面部检测问题
"""
import cv2
import numpy as np
import os
import sys

def test_image_reading(image_path):
    """测试图片读取"""
    print(f"🔍 测试图片读取: {image_path}")
    print(f"📁 文件存在: {os.path.exists(image_path)}")
    
    if not os.path.exists(image_path):
        print("❌ 文件不存在！")
        return None
    
    # 方法1: 直接读取
    print("方法1: cv2.imread 直接读取")
    img1 = cv2.imread(image_path)
    if img1 is not None:
        print(f"✅ 直接读取成功，尺寸: {img1.shape}")
    else:
        print("❌ 直接读取失败")
    
    # 方法2: numpy读取（处理中文路径）
    print("方法2: numpy + cv2.imdecode 读取")
    try:
        with open(image_path, 'rb') as f:
            img_data = f.read()
        img_array = np.frombuffer(img_data, np.uint8)
        img2 = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img2 is not None:
            print(f"✅ numpy读取成功，尺寸: {img2.shape}")
            return img2
        else:
            print("❌ numpy读取失败")
    except Exception as e:
        print(f"❌ numpy读取异常: {e}")
    
    return img1 if img1 is not None else None

def test_opencv_face_detection(img):
    """测试OpenCV面部检测"""
    print("🔍 测试OpenCV面部检测")
    
    # 初始化面部检测器
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            print("❌ Haar级联分类器加载失败")
            return []
        print("✅ Haar级联分类器加载成功")
    except Exception as e:
        print(f"❌ 面部检测器初始化失败: {e}")
        return []
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f"✅ 灰度图转换成功，尺寸: {gray.shape}")
    
    # 多种参数尝试面部检测
    detection_params = [
        {"scaleFactor": 1.1, "minNeighbors": 5, "minSize": (30, 30)},
        {"scaleFactor": 1.05, "minNeighbors": 3, "minSize": (20, 20)},
        {"scaleFactor": 1.2, "minNeighbors": 7, "minSize": (50, 50)},
        {"scaleFactor": 1.3, "minNeighbors": 4, "minSize": (40, 40)},
    ]
    
    for i, params in enumerate(detection_params):
        print(f"🔍 尝试参数组合 {i+1}: {params}")
        faces = face_cascade.detectMultiScale(gray, **params)
        print(f"检测到 {len(faces)} 个面部")
        
        if len(faces) > 0:
            print("✅ 面部检测成功！")
            for j, (x, y, w, h) in enumerate(faces):
                print(f"  面部 {j+1}: x={x}, y={y}, w={w}, h={h}")
                # 计算面部中心和面积
                center_x, center_y = x + w//2, y + h//2
                area = w * h
                print(f"  中心: ({center_x}, {center_y}), 面积: {area}")
            
            # 选择最大的面部
            largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = largest_face
            print(f"🎯 最大面部: x={x}, y={y}, w={w}, h={h}")
            
            # 扩展面部区域
            expand_ratio = 0.3
            expand_w = int(w * expand_ratio)
            expand_h = int(h * expand_ratio)
            
            x1 = max(0, x - expand_w)
            y1 = max(0, y - expand_h)
            x2 = min(img.shape[1], x + w + expand_w)
            y2 = min(img.shape[0], y + h + expand_h)
            
            # 确保是正方形
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            size = max(x2 - x1, y2 - y1)
            half_size = size // 2
            
            x1 = max(0, center_x - half_size)
            y1 = max(0, center_y - half_size)
            x2 = min(img.shape[1], center_x + half_size)
            y2 = min(img.shape[0], center_y + half_size)
            
            actual_size = min(x2 - x1, y2 - y1)
            x2 = x1 + actual_size
            y2 = y1 + actual_size
            
            print(f"🎯 最终坐标: ({x1}, {y1}, {x2}, {y2}), 尺寸: {actual_size}x{actual_size}")
            
            return [(x1, y1, x2, y2)]
    
    print("❌ 所有参数组合都未检测到面部")
    return []

def test_fallback_method(img):
    """测试备用方法"""
    print("🔍 测试备用面部区域计算")
    
    h, w = img.shape[:2]
    print(f"图片尺寸: {w}x{h}")
    
    # 原来的备用方法
    face_size = min(w, h) // 2
    center_x, center_y = w // 2, h // 2
    half_size = face_size // 2
    x1 = max(0, center_x - half_size)
    y1 = max(0, center_y - half_size)
    x2 = min(w, center_x + half_size)
    y2 = min(h, center_y + half_size)
    size = min(x2 - x1, y2 - y1)
    x2, y2 = x1 + size, y1 + size
    
    print(f"备用方法坐标: ({x1}, {y1}, {x2}, {y2}), 尺寸: {size}x{size}")
    
    # 改进的备用方法 - 假设面部在上半部分中央
    face_ratio = 0.6  # 面部占图片的比例
    face_size = int(min(w, h) * face_ratio)
    
    # 面部通常在图片的上半部分
    center_x = w // 2
    center_y = int(h * 0.4)  # 面部中心在图片40%高度处
    
    half_size = face_size // 2
    x1_new = max(0, center_x - half_size)
    y1_new = max(0, center_y - half_size)
    x2_new = min(w, center_x + half_size)
    y2_new = min(h, center_y + half_size)
    
    # 确保是正方形
    size_new = min(x2_new - x1_new, y2_new - y1_new)
    x2_new = x1_new + size_new
    y2_new = y1_new + size_new
    
    print(f"改进备用方法坐标: ({x1_new}, {y1_new}, {x2_new}, {y2_new}), 尺寸: {size_new}x{size_new}")
    
    return [(x1, y1, x2, y2)], [(x1_new, y1_new, x2_new, y2_new)]

def save_debug_image(img, coords_list, output_path):
    """保存调试图片，标记面部区域"""
    debug_img = img.copy()
    
    colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0)]
    
    for i, coords in enumerate(coords_list):
        color = colors[i % len(colors)]
        for x1, y1, x2, y2 in coords:
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(debug_img, f"Method {i+1}", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    cv2.imwrite(output_path, debug_img)
    print(f"✅ 调试图片已保存: {output_path}")

def main():
    # 测试图片路径
    image_path = r"C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\LmyDigitalHuman\wwwroot\templates\小哈.jpg"
    
    print("=" * 60)
    print("🔍 面部检测调试脚本")
    print("=" * 60)
    
    # 1. 测试图片读取
    img = test_image_reading(image_path)
    if img is None:
        print("❌ 无法读取图片，退出调试")
        return
    
    print("\n" + "=" * 60)
    
    # 2. 测试OpenCV面部检测
    opencv_coords = test_opencv_face_detection(img)
    
    print("\n" + "=" * 60)
    
    # 3. 测试备用方法
    fallback_coords, improved_coords = test_fallback_method(img)
    
    print("\n" + "=" * 60)
    
    # 4. 保存调试图片
    all_coords = []
    if opencv_coords:
        all_coords.append(opencv_coords)
    all_coords.append(fallback_coords)
    all_coords.append(improved_coords)
    
    debug_output = "debug_face_detection.jpg"
    save_debug_image(img, all_coords, debug_output)
    
    print("\n" + "=" * 60)
    print("🎉 调试完成！")
    print("请查看 debug_face_detection.jpg 来看面部检测结果")
    print("=" * 60)

if __name__ == "__main__":
    main()