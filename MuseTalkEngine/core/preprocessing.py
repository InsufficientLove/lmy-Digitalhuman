#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized Preprocessing V2
优化版预处理 - 修复脸部阴影问题，极速预处理
"""

import os
import sys
import json
import pickle
import torch
import cv2
import numpy as np
import argparse
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import copy
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

# 添加MuseTalk模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MuseTalk'))
sys.path.append('/opt/musetalk/repo/musetalk')  # 添加实际的musetalk路径（小写）

try:
    from musetalk.utils.face_parsing import FaceParsing
    print("成功导入FaceParsing")
    FACE_PARSING_AVAILABLE = True
except ImportError as e:
    print(f"无法导入FaceParsing: {e}")
    FACE_PARSING_AVAILABLE = False

from musetalk.utils.utils import load_all_model
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from musetalk.utils.blending import get_image_prepare_material
from musetalk.utils.audio_processor import AudioProcessor

# 定义coord_placeholder常量
coord_placeholder = (0, 0, 0, 0)  # 表示无效的边界框

print("Optimized Preprocessing V2 - 极速预处理引擎")

# 简单的FaceParsing替代实现
class SimpleFaceParsing:
    """简单的面部解析替代实现"""
    def __init__(self):
        pass
    
    def __call__(self, image, mode=None):
        """返回一个面部分割mask
        返回值应该是分割标签图，其中：
        0 = 背景
        1-5 = 皮肤
        6-10 = 眉毛、眼睛
        11-13 = 鼻子、嘴巴
        14-17 = 头发
        """
        if isinstance(image, np.ndarray):
            h, w = image.shape[:2]
            # 创建分割mask
            mask = np.zeros((h, w), dtype=np.uint8)
            
            # 面部主要区域（皮肤）- 使用标签1
            center_x, center_y = w // 2, h // 2
            
            # 脸部椭圆（皮肤区域）
            face_axes = (int(w * 0.35), int(h * 0.45))
            cv2.ellipse(mask, (center_x, center_y), face_axes, 0, 0, 360, 1, -1)
            
            # 嘴巴区域 - 使用标签11（重要！）
            mouth_y = center_y + int(h * 0.15)
            mouth_axes = (int(w * 0.15), int(h * 0.08))
            cv2.ellipse(mask, (center_x, mouth_y), mouth_axes, 0, 0, 360, 11, -1)
            
            # 鼻子区域 - 使用标签12
            nose_y = center_y
            nose_axes = (int(w * 0.08), int(h * 0.1))
            cv2.ellipse(mask, (center_x, nose_y), nose_axes, 0, 0, 360, 12, -1)
            
            # 眼睛区域 - 使用标签6
            eye_y = center_y - int(h * 0.1)
            eye_offset = int(w * 0.12)
            eye_axes = (int(w * 0.08), int(h * 0.05))
            cv2.ellipse(mask, (center_x - eye_offset, eye_y), eye_axes, 0, 0, 360, 6, -1)
            cv2.ellipse(mask, (center_x + eye_offset, eye_y), eye_axes, 0, 0, 360, 6, -1)
            
            return mask
        return None
    
    def parse(self, image):
        """兼容parse方法"""
        return self.__call__(image)

class OptimizedPreprocessor:
    """
    优化的预处理器 - 修复阴影问题，极速处理
    
    🔥 坐标系统说明（极其重要！）
    ----------------------------------
    在整个预处理流程中，必须严格遵守以下坐标规则：
    
    1. BBox格式：[x1, y1, x2, y2]
       - x1, x2: 水平坐标（列，Column，Width方向）
       - y1, y2: 垂直坐标（行，Row，Height方向）
    
    2. Numpy数组索引：array[row, col] = array[y, x]
       - 第一个索引是 ROW (Y坐标，Height)
       - 第二个索引是 COL (X坐标，Width)
    
    3. 正确的切片方式：
       ✅ 正确：frame[y1:y2, x1:x2]
       ❌ 错误：frame[x1:x2, y1:y2] <- 这会导致裁剪出错误区域！
    
    4. Landmarks格式：[[x, y], [x, y], ...]
       - landmarks[:, 0] 是 X坐标
       - landmarks[:, 1] 是 Y坐标
    
    5. cv2.resize参数：resize(image, (width, height))
       - 第一个参数是 WIDTH (X方向)
       - 第二个参数是 HEIGHT (Y方向)
    """
    
    def __init__(self):
        self.vae = None
        self.unet = None
        self.pe = None
        self.fp = None
        self.device = None
        self.weight_dtype = torch.float16
        self.is_initialized = False
        
        # 🎨 阴影修复参数
        self.shadow_fix_enabled = False  # 默认禁用，避免颜色变化
        self.lighting_adjustment = False  # 禁用光照调整
        self.color_correction = False  # 禁用颜色校正
        self.preserve_original_color = True  # 保持原始颜色
        
    def initialize_models(self, device='cuda:0'):
        """初始化模型"""
        if self.is_initialized:
            return True
            
        try:
            print(f"初始化预处理模型 - 设备: {device}")
            self.device = device
            
            # 加载模型 - 添加错误处理
            try:
                vae, unet, pe = load_all_model()
                print("预处理模型加载成功")
            except Exception as e:
                print(f"预处理模型加载失败: {e}")
                # 尝试使用备用VAE路径
                try:
                    vae, unet, pe = load_all_model(vae_type="sd-vae-ft-mse")
                    print("预处理使用备用VAE模型加载成功")
                except Exception as e2:
                    print(f"预处理备用模型也加载失败: {e2}")
                    raise e2
            
            # 修复模型对象兼容性 - 使用正确的属性结构
            # VAE 必须保持 Float32 避免 cuDNN 错误
            if hasattr(vae, 'vae'):
                vae.vae = vae.vae.to(device, dtype=torch.float32).eval()
                self.vae = vae
            elif hasattr(vae, 'to'):
                self.vae = vae.to(device, dtype=torch.float32).eval()
            else:
                print("警告: VAE对象结构不明，跳过优化")
                self.vae = vae
            
            if hasattr(unet, 'model'):
                unet.model = unet.model.to(device).half().eval()
                self.unet = unet
            elif hasattr(unet, 'to'):
                self.unet = unet.to(device).half().eval()
            else:
                print("警告: UNet对象结构不明，跳过优化")
                self.unet = unet
            
            if hasattr(pe, 'to'):
                self.pe = pe.to(device).half().eval()
            else:
                print("警告: PE对象没有.to()方法，跳过优化")
                self.pe = pe
            
            # 初始化面部解析 - 优先使用真正的FaceParsing
            if FACE_PARSING_AVAILABLE:
                try:
                    self.fp = FaceParsing()
                    print("使用MuseTalk原生FaceParsing")
                except Exception as e:
                    print(f"FaceParsing初始化失败: {e}")
                    self.fp = SimpleFaceParsing()
                    print("降级到SimpleFaceParsing")
            else:
                self.fp = SimpleFaceParsing()
                print("使用SimpleFaceParsing替代实现")
            
            print("预处理模型初始化完成")
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"模型初始化失败: {str(e)}")
            return False
    
    def _create_lower_face_gradient_mask(self, width, height):
        """
        创建下半脸渐变遮罩（兜底方案）
        只保留图像下半部分，边缘羽化，避免方形边框
        """
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # 1. 创建椭圆形面部区域（覆盖下半脸）
        center_x, center_y = width // 2, int(height * 0.6)  # 中心偏下
        axis_x = int(width * 0.35)   # 横向半轴（脸宽）
        axis_y = int(height * 0.25)  # 纵向半轴（嘴部区域）
        
        # 绘制椭圆
        cv2.ellipse(mask, (center_x, center_y), (axis_x, axis_y), 
                    0, 0, 360, 255, -1)
        
        # 2. 高斯模糊羽化边缘（消除硬边）
        blur_kernel = max(int(min(width, height) * 0.1), 51)
        if blur_kernel % 2 == 0:
            blur_kernel += 1
        mask = cv2.GaussianBlur(mask, (blur_kernel, blur_kernel), 0)
        
        # 3. 顶部渐变衰减（只保留下半部分）
        for y in range(int(height * 0.4)):
            alpha = y / (height * 0.4)  # 0 到 1 的渐变
            mask[y, :] = (mask[y, :] * alpha).astype(np.uint8)
        
        print(f"✅ 创建渐变遮罩: {width}x{height}, 中心=({center_x},{center_y}), 椭圆=({axis_x},{axis_y})")
        
        return mask
    
    def fix_face_shadows(self, image):
        """修复面部阴影 - 极速版"""
        try:
            # 如果需要保持原始颜色，直接返回
            if self.preserve_original_color:
                return image
                
            if not self.shadow_fix_enabled:
                return image
        
            # 🎨 1. 光照均衡化
            if self.lighting_adjustment:
                # 转换到LAB色彩空间进行光照调整
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l_channel = lab[:, :, 0]
                
                # 自适应直方图均衡化
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l_channel = clahe.apply(l_channel)
                
                lab[:, :, 0] = l_channel
                image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # 🎨 2. 阴影检测和修复
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 使用形态学操作检测阴影区域
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
            dilated = cv2.dilate(gray, kernel)
            shadow_mask = cv2.absdiff(dilated, gray)
            
            # 阈值处理得到阴影区域
            _, shadow_mask = cv2.threshold(shadow_mask, 30, 255, cv2.THRESH_BINARY)
            
            # 对阴影区域进行亮度提升
            shadow_areas = shadow_mask > 0
            if np.any(shadow_areas):
                # 提升阴影区域亮度
                hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                hsv[:, :, 2][shadow_areas] = np.clip(
                    hsv[:, :, 2][shadow_areas] * 1.3, 0, 255
                ).astype(np.uint8)
                image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            
            # 🎨 3. 颜色校正
            if self.color_correction:
                # 白平衡调整
                image = self.white_balance_correction(image)
                
                # 肤色增强
                image = self.skin_tone_enhancement(image)
            
            return image
            
        except Exception as e:
            print(f"阴影修复失败: {str(e)}")
            return image
    
    def white_balance_correction(self, image):
        """白平衡校正"""
        try:
            # Gray World算法
            b, g, r = cv2.split(image)
            
            b_avg = np.mean(b)
            g_avg = np.mean(g) 
            r_avg = np.mean(r)
            
            # 计算增益
            k = (b_avg + g_avg + r_avg) / 3
            kb = k / b_avg
            kg = k / g_avg
            kr = k / r_avg
            
            # 应用增益
            b = np.clip(b * kb, 0, 255).astype(np.uint8)
            g = np.clip(g * kg, 0, 255).astype(np.uint8)
            r = np.clip(r * kr, 0, 255).astype(np.uint8)
            
            return cv2.merge([b, g, r])
            
        except:
            return image
    
    def skin_tone_enhancement(self, image):
        """肤色增强"""
        try:
            # 转换到YUV色彩空间
            yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            
            # 肤色范围检测
            lower_skin = np.array([0, 133, 77], dtype=np.uint8)
            upper_skin = np.array([255, 173, 127], dtype=np.uint8)
            
            skin_mask = cv2.inRange(yuv, lower_skin, upper_skin)
            
            # 对肤色区域进行微调
            if np.any(skin_mask > 0):
                # 轻微增强红色通道
                bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
                b, g, r = cv2.split(bgr)
                
                skin_areas = skin_mask > 0
                r[skin_areas] = np.clip(r[skin_areas] * 1.05, 0, 255).astype(np.uint8)
                
                return cv2.merge([b, g, r])
            
            return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
            
        except:
            return image
    
    def preprocess_template_ultra_fast(self, template_path, output_dir, template_id):
        """极速预处理模板 - 修复阴影问题，优化性能"""
        try:
            start_time = time.time()  # 添加start_time定义
            print(f"开始极速预处理: {template_id}")
            
            # 确保模型已初始化
            if not self.is_initialized:
                print("模型未初始化，开始初始化...")
                if not self.initialize_models():
                    raise RuntimeError("模型初始化失败")
            
            # 再次检查VAE是否存在
            if self.vae is None:
                print("VAE未加载，尝试重新加载模型...")
                from musetalk.utils.utils import load_all_model
                vae, unet, pe = load_all_model()
                self.vae = vae
                self.unet = unet
                self.pe = pe
                print("模型重新加载完成")
            
            # 版本标识
            print(f"\n{'='*70}")
            print(f"🔍 预处理版本: v2.0 - 坐标验证增强版")
            print(f"  包含严格的 Numpy 切片顺序验证（ROW=Y, COL=X）")
            print(f"{'='*70}\n")
            
            # 创建输出目录
            template_output_dir = os.path.join(output_dir, template_id)
            os.makedirs(template_output_dir, exist_ok=True)
            print(f"使用缓存目录: {template_output_dir}")
            
            # 1. 并行读取和处理图像
            print("读取模板图像...")
            
            # 检查是否是直接的图像文件路径
            template_path_obj = Path(template_path)
            if template_path_obj.is_file() and template_path_obj.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                input_image_path = str(template_path_obj)
                print(f"使用直接图像文件: {input_image_path}")
            else:
                # 在目录中搜索图像文件
                image_files = []
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                    image_files.extend(template_path_obj.glob(ext))
                
                if not image_files:
                    raise ValueError(f"未找到图像文件: {template_path}")
                
                # 选择最佳图像（通常是第一张）
                input_image_path = str(image_files[0])
                print(f"使用目录中的图像: {input_image_path}")
            
            # 🎨 2. 图像预处理和阴影修复
            print("🎨 图像预处理...")
            image = cv2.imread(input_image_path)
            if image is None:
                raise ValueError(f"无法读取图像: {input_image_path}")
            
            # 关键修复：cv2.imread读取的是BGR格式，需要转换为RGB供模型使用
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            print("✅ 输入图像已转换 BGR -> RGB")
            
            # 跳过阴影修复，保持原始颜色
            # image = self.fix_face_shadows(image)
            print("保持原始颜色，跳过阴影修复")
            
            # 3. 面部检测和关键点提取 - 使用 face_alignment 库
            print("👤 面部检测和关键点提取（使用 face_alignment）...")
            
            # 🔥 使用 face_alignment 库进行可靠的人脸检测
            try:
                from face_alignment import FaceAlignment, LandmarksType
                print("✅ 成功导入 face_alignment 库")
            except ImportError as e:
                raise ImportError(
                    "❌ 无法导入 face_alignment 库！\n"
                    "请安装: pip install face-alignment\n"
                    f"错误: {e}"
                )
            
            # 初始化 face_alignment 检测器（S3FD + 2D landmarks）
            try:
                fa = FaceAlignment(
                    LandmarksType.TWO_D, 
                    flip_input=False, 
                    device=self.device.split(':')[0]  # 'cuda' or 'cpu'
                )
                print(f"✅ face_alignment 检测器初始化成功（设备: {self.device}）")
            except Exception as e:
                raise RuntimeError(f"❌ face_alignment 初始化失败: {e}")
            
            # 检测人脸关键点
            # 注意：face_alignment 期望 RGB 格式
            preds = fa.get_landmarks(image)  # image 已经是 RGB 格式
            
            # 🔥 严格验证：如果没有检测到人脸，直接抛出异常
            if preds is None or len(preds) == 0:
                raise ValueError(
                    "❌ 人脸检测失败！未检测到任何人脸。\n"
                    "可能原因：\n"
                    "  1. 图片中没有清晰的正面人脸\n"
                    "  2. 人脸被遮挡或角度过大\n"
                    "  3. 图片质量过低或光线不足\n"
                    "请上传包含清晰正面人脸的图片后重试。"
                )
            
            print(f"✅ DEBUG: 检测到 {len(preds)} 个人脸")
            
            # 使用第一个检测到的人脸
            landmarks = preds[0]  # shape: (68, 2) for dlib, (98, 2) for others
            
            # 调试：打印关键点信息
            print(f"✅ DEBUG: landmarks shape = {landmarks.shape}")
            print(f"✅ DEBUG: X 坐标范围 = {landmarks[:, 0].min():.1f} ~ {landmarks[:, 0].max():.1f}")
            print(f"✅ DEBUG: Y 坐标范围 = {landmarks[:, 1].min():.1f} ~ {landmarks[:, 1].max():.1f}")
            print(f"✅ DEBUG: 前5个关键点 = \n{landmarks[:5]}")
            
            # 再次验证：确保关键点不是全零或异常值
            if np.max(landmarks) < 1.0:
                raise ValueError(
                    f"❌ 检测到的关键点异常（可能是归一化坐标）：\n"
                    f"  max value = {np.max(landmarks)}\n"
                    "这可能是 face_alignment 返回了错误的坐标格式。"
                )
            
            # 构造返回值以兼容后续代码
            coord_list = [landmarks]  # 列表，包含一个 landmarks 数组
            frame_list = [image]      # RGB 格式的图像
            
            # 获取原始尺寸
            original_h, original_w = image.shape[:2]
            original_size = (original_w, original_h)
            
            print(f"✅ 面部检测成功: 图像尺寸={original_w}x{original_h}, 关键点数={landmarks.shape[0]}")
            
            # 4. 面部解析和特征提取
            print("🎭 面部解析和特征提取...")
            mask_coords_list, mask_list = [], []
            face_parsing_masks = []  # 存储面部解析的mask
            
            # 处理检测到的人脸
            for i, (frame, landmarks) in enumerate(zip(frame_list, coord_list)):
                # 🔥 从 landmarks 计算精确的面部边界框
                print(f"📐 计算面部边界框（帧 {i}）...")
                
                # 提取 X, Y 坐标
                x_coords = landmarks[:, 0]
                y_coords = landmarks[:, 1]
                
                # 计算基础边界框
                x_min = int(np.min(x_coords))
                y_min = int(np.min(y_coords))
                x_max = int(np.max(x_coords))
                y_max = int(np.max(y_coords))
                
                print(f"✅ DEBUG: 原始 BBox = [{x_min}, {y_min}, {x_max}, {y_max}]")
                print(f"✅ DEBUG: BBox 尺寸 = {x_max - x_min} x {y_max - y_min}")
                
                # 添加适当的边距（避免裁剪过紧）
                h, w = frame.shape[:2]
                margin_x = int((x_max - x_min) * 0.2)  # 20% 水平边距
                margin_y = int((y_max - y_min) * 0.3)  # 30% 垂直边距（额外包含额头和下巴）
                
                x_min = max(0, x_min - margin_x)
                y_min = max(0, y_min - margin_y)
                x_max = min(w, x_max + margin_x)
                y_max = min(h, y_max + margin_y)
                
                face_box = [x_min, y_min, x_max, y_max]
                
                print(f"✅ DEBUG: 添加边距后 BBox = {face_box}")
                print(f"✅ DEBUG: 最终 BBox 尺寸 = {x_max - x_min} x {y_max - y_min}")
                
                # 验证边界框有效性
                if (x_max - x_min) < 50 or (y_max - y_min) < 50:
                    raise ValueError(
                        f"❌ 计算的边界框过小: {x_max - x_min}x{y_max - y_min}\n"
                        "这可能表示人脸检测质量不佳，请使用更清晰的图片。"
                    )
                
                # 面部解析 - 修复格式不匹配问题
                try:
                    mask_out = None
                    
                    # 优先使用SimpleFaceParsing（更可靠）
                    if isinstance(self.fp, SimpleFaceParsing):
                        mask_out = self.fp(frame)
                        if mask_out is not None:
                            print(f"✅ SimpleFaceParsing成功，mask shape: {mask_out.shape}, unique: {np.unique(mask_out)[:5]}")
                    # 尝试原生FaceParsing
                    elif self.fp is not None:
                        try:
                            # 🔥 修复1：FaceParsing 期望 PIL.Image 输入
                            from PIL import Image
                            
                            # 转换 numpy 数组为 PIL Image
                            # frame 是 RGB 格式的 numpy 数组
                            pil_image = Image.fromarray(frame.astype(np.uint8))
                            
                            print(f"🔍 DEBUG: 调用 FaceParsing，输入类型={type(pil_image)}, 尺寸={pil_image.size}")
                            
                            # 调用 FaceParsing（mode="raw" 用于标准面部解析）
                            result = self.fp(pil_image, mode="raw")
                            
                            print(f"🔍 DEBUG: FaceParsing 返回类型={type(result)}")
                            
                            # 🔥 修复2：FaceParsing 返回 PIL.Image，需要转换为 numpy
                            if hasattr(result, 'size'):  # PIL.Image 对象
                                mask_out = np.array(result)
                                print(f"✅ FaceParsing成功（PIL->numpy），mask shape: {mask_out.shape}, unique: {np.unique(mask_out)[:10]}")
                            elif isinstance(result, np.ndarray):
                                mask_out = result
                                print(f"✅ FaceParsing成功（numpy），mask shape: {mask_out.shape}")
                            elif isinstance(result, tuple) and len(result) > 0:
                                # 如果返回元组，取第一个元素
                                if hasattr(result[0], 'size'):
                                    mask_out = np.array(result[0])
                                else:
                                    mask_out = result[0]
                                print(f"✅ FaceParsing返回tuple，使用第一个元素")
                            else:
                                raise ValueError(f"FaceParsing返回未知类型: {type(result)}")
                                
                        except Exception as fp_error:
                            print(f"❌ FaceParsing调用失败: {fp_error}")
                            print(f"   错误详情: {type(fp_error).__name__}")
                            import traceback
                            traceback.print_exc()
                            
                            # 降级到 SimpleFaceParsing
                            print("   降级到 SimpleFaceParsing...")
                            mask_out = SimpleFaceParsing()(frame)
                    
                    # 🔥 修复3：改进 fallback - 使用下半脸渐变遮罩而不是全白
                    if mask_out is None or not isinstance(mask_out, np.ndarray):
                        print("⚠️ 面部解析完全失败，使用渐变遮罩（下半脸）")
                        h, w = frame.shape[:2]
                        mask_out = self._create_lower_face_gradient_mask(w, h)
                        
                except Exception as e:
                    print(f"❌ 面部解析出错: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # 使用渐变遮罩
                    h, w = frame.shape[:2]
                    mask_out = self._create_lower_face_gradient_mask(w, h)
                
                # 保存面部解析的mask
                face_parsing_masks.append(mask_out)
                
                # 获取面部区域坐标 - 直接使用默认值，避免错误
                # 跳过get_image_prepare_material，因为它一直报错
                h, w = frame.shape[:2]
                mask = np.ones((h, w), dtype=np.uint8) * 255  # 全白mask
                crop_box = face_box  # 使用face_box作为crop_box
                
                # 调试输出
                print(f"使用默认mask和crop_box: {crop_box}")
                
                # 确保crop_box是4个元素的列表
                if isinstance(crop_box, (list, tuple)):
                    if len(crop_box) == 4:
                        mask_coords_list.append(list(crop_box))
                    else:
                        print(f"警告: crop_box长度不是4: {len(crop_box)}, 使用face_box")
                        mask_coords_list.append(list(face_box))
                elif isinstance(crop_box, np.ndarray):
                    if crop_box.size >= 4:
                        mask_coords_list.append(crop_box.flatten()[:4].tolist())
                    else:
                        print(f"警告: crop_box太小: {crop_box.shape}, 使用face_box")
                        mask_coords_list.append(list(face_box))
                else:
                    print(f"警告: crop_box类型异常: {type(crop_box)}, 使用face_box")
                    mask_coords_list.append(list(face_box))
                    
                mask_list.append(mask)
            
            # 5. VAE编码 - 并行处理
            print("VAE编码...")
            input_latent_list = []
            
            # 紧急修复：添加face_box参数，crop到256x256
            def encode_frame(frame, face_box, mask=None):
                with torch.no_grad():
                    # 🔥 关键修复：确保使用正确的Numpy切片顺序！
                    # Numpy格式：array[row, col] = array[H, W] = array[y, x]
                    # BBox格式：[x1, y1, x2, y2]
                    # 因此切片必须是：frame[y1:y2, x1:x2]
                    x1, y1, x2, y2 = face_box
                    
                    # 严格验证坐标合法性
                    h, w = frame.shape[:2]
                    if not (0 <= y1 < y2 <= h and 0 <= x1 < x2 <= w):
                        print(f"❌ 错误：BBox 坐标非法！")
                        print(f"   Frame shape: {frame.shape} (H={h}, W={w})")
                        print(f"   BBox: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
                        print(f"   X range: {x1} to {x2} (width={x2-x1})")
                        print(f"   Y range: {y1} to {y2} (height={y2-y1})")
                        raise ValueError("BBox coordinates out of bounds")
                    
                    # 🔥 核心裁剪：使用 [y1:y2, x1:x2] 顺序（Row=Y, Col=X）
                    face_crop = frame[y1:y2, x1:x2]
                    print(f"✅ 裁剪验证: frame[{y1}:{y2}, {x1}:{x2}] → shape={face_crop.shape}")
                    print(f"   期望尺寸: H={y2-y1}, W={x2-x1} → 实际: H={face_crop.shape[0]}, W={face_crop.shape[1]}")
                    
                    # Resize到256x256（标准MuseTalk输入尺寸）
                    face_256 = cv2.resize(face_crop, (256, 256), interpolation=cv2.INTER_LANCZOS4)
                    print(f"✅ Resize完成: {face_crop.shape} → 256x256")
                    
                    # 转换为tensor
                    frame_tensor = torch.from_numpy(face_256).float().to(self.device) / 127.5 - 1.0
                    frame_tensor = frame_tensor.permute(2, 0, 1).unsqueeze(0)
                    
                    print(f"   Tensor输入VAE: {frame_tensor.shape}")
                    
                    # 编码原始帧得到reference latent (4通道)
                    # VAE可能有不同的编码方法名
                    if hasattr(self.vae, 'encode_latents'):
                        reference_latent = self.vae.encode_latents(frame_tensor)
                    elif hasattr(self.vae, 'encode'):
                        # 标准的VAE encode方法
                        latent_dist = self.vae.encode(frame_tensor)
                        if hasattr(latent_dist, 'latent_dist'):
                            reference_latent = latent_dist.latent_dist.sample() * 0.18215
                        elif hasattr(latent_dist, 'sample'):
                            reference_latent = latent_dist.sample() * 0.18215
                        else:
                            reference_latent = latent_dist * 0.18215
                    else:
                        raise AttributeError(f"VAE对象没有encode方法: {dir(self.vae)}")
                    
                    # 如果有mask，创建masked版本
                    if mask is not None and mask.size > 0:
                        # 🔥 关键修复：mask 尺寸可能与原图不匹配（例如 512x512 vs 1280x1707）
                        # 需要先将 mask resize 到原图尺寸，然后再裁剪
                        h_orig, w_orig = frame.shape[:2]
                        h_mask, w_mask = mask.shape[:2]
                        
                        print(f"📐 Mask 尺寸检查: mask={mask.shape}, frame={frame.shape[:2]}")
                        
                        if (h_mask, w_mask) != (h_orig, w_orig):
                            # Resize mask 到原图尺寸
                            mask_resized = cv2.resize(mask, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)
                            print(f"✅ Mask 已 resize: {mask.shape} → {mask_resized.shape}")
                        else:
                            mask_resized = mask
                        
                        # 现在使用正确尺寸的 mask 进行裁剪
                        # mask也是numpy数组，同样遵循 [row, col] = [y, x] 规则
                        mask_crop = mask_resized[y1:y2, x1:x2]
                        print(f"✅ Mask裁剪: mask_resized[{y1}:{y2}, {x1}:{x2}] → shape={mask_crop.shape}")
                        
                        # 验证裁剪后的尺寸
                        if mask_crop.shape[0] == 0 or mask_crop.shape[1] == 0:
                            raise ValueError(f"Mask 裁剪后尺寸为 0: {mask_crop.shape}")
                        
                        mask_256 = cv2.resize(mask_crop, (256, 256), interpolation=cv2.INTER_LINEAR)
                        print(f"   Mask crop: {mask_crop.shape} → 256x256")
                        
                        # 处理面部解析mask
                        binary_mask = (mask_256 > 0).astype(np.float32)
                        
                        # 平滑处理
                        from scipy.ndimage import gaussian_filter
                        binary_mask = gaussian_filter(binary_mask, sigma=1.0)
                        
                        # 将mask转换为tensor
                        mask_tensor = torch.from_numpy(binary_mask).float().to(self.device)
                        
                        # 调整mask维度以匹配frame_tensor
                        if len(mask_tensor.shape) == 2:  # [H, W]
                            mask_tensor = mask_tensor.unsqueeze(0).unsqueeze(0)  # [1, 1, H, W]
                        
                        # 扩展mask到3通道
                        mask_tensor = mask_tensor.repeat(1, 3, 1, 1)  # [1, 3, H, W]
                        
                        # 创建masked frame（保留面部区域，背景变黑）
                        masked_frame_tensor = frame_tensor * mask_tensor
                        masked_latent = self.vae.encode_latents(masked_frame_tensor)
                        
                        # 拼接masked和reference latent得到8通道
                        combined_latent = torch.cat([masked_latent, reference_latent], dim=1)
                    else:
                        # 如果没有mask，直接复制reference latent
                        print("No face parsing mask available, using duplicated reference latent")
                        combined_latent = torch.cat([reference_latent, reference_latent], dim=1)
                    
                    return combined_latent.cpu()
            
            # 并行编码多帧
            with ThreadPoolExecutor(max_workers=4) as executor:
                # 将frame、face_box和对应的face parsing mask一起传递
                futures = []
                for i, frame in enumerate(frame_list):
                    # 获取对应的face_box（从mask_coords_list中）
                    if i < len(mask_coords_list):
                        face_box = mask_coords_list[i]
                    else:
                        # 使用默认值（全图的中心区域）
                        h, w = frame.shape[:2]
                        face_box = [w//4, h//4, 3*w//4, 3*h//4]
                    
                    face_mask = face_parsing_masks[i] if i < len(face_parsing_masks) else None
                    futures.append(executor.submit(encode_frame, frame, face_box, face_mask))
                
                for future in as_completed(futures):
                    latent = future.result()
                    input_latent_list.append(latent)
            
            # 6. 创建循环数据
            print("🔄 创建循环数据...")
            
            # 验证latent通道数
            if input_latent_list:
                latent_shape = input_latent_list[0].shape
                print(f"✅ Latent形状: {latent_shape} (应该是8通道)")
                if latent_shape[1] != 8:
                    print(f"⚠️ 警告: Latent通道数为{latent_shape[1]}，期望为8通道")
            
            # 🔥 关键修复：确保坐标和mask列表不为空
            if len(mask_coords_list) == 0:
                print("⚠️ 警告: mask_coords_list为空，添加默认值")
                # 使用默认的全图坐标
                h, w = frame_list[0].shape[:2]
                default_coords = [0, 0, w, h]
                mask_coords_list.append(default_coords)
                print(f"   添加默认坐标: {default_coords}")
            
            if len(mask_list) == 0:
                print("⚠️ 警告: mask_list为空，添加默认mask")
                # 使用全白mask
                h, w = frame_list[0].shape[:2]
                default_mask = np.ones((h, w), dtype=np.uint8) * 255
                mask_list.append(default_mask)
                print(f"   添加默认mask: {default_mask.shape}")
            
            if len(coord_list) == 0:
                print("⚠️ 警告: coord_list为空，添加默认值")
                # 使用mask_coords_list的第一个元素
                coord_list.append(mask_coords_list[0])
                print(f"   添加默认coord: {coord_list[0]}")
            
            # 如果只有一帧，复制创建循环
            if len(input_latent_list) == 1:
                input_latent_list_cycle = input_latent_list * 2
                coord_list_cycle = coord_list * 2
                frame_list_cycle = frame_list * 2
                mask_coords_list_cycle = mask_coords_list * 2
                mask_list_cycle = mask_list * 2
            else:
                input_latent_list_cycle = input_latent_list
                coord_list_cycle = coord_list
                frame_list_cycle = frame_list
                mask_coords_list_cycle = mask_coords_list
                mask_list_cycle = mask_list
            
            # 7. 保存预处理缓存
            print("💾 保存预处理缓存...")
            
            cache_data = {
                'input_latent_list_cycle': input_latent_list_cycle,
                'coord_list_cycle': coord_list_cycle,
                # 'frame_list_cycle': frame_list_cycle, # 移除原始帧以减小缓存大小，改为推理时读取
                'mask_coords_list_cycle': mask_coords_list_cycle,
                'mask_list_cycle': mask_list_cycle,
                'original_size': original_size,
                'template_path': template_path,
                'input_image_path': input_image_path # 保存具体使用的图像路径
            }
            
            # 保存缓存文件到模板子目录
            cache_file = os.path.join(template_output_dir, f"{template_id}_preprocessed.pkl")
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            # 保存元数据
            metadata = {
                'template_id': template_id,
                'template_path': template_path,
                'processed_at': time.time(),
                'frame_count': len(frame_list_cycle),
                'shadow_fix_enabled': self.shadow_fix_enabled,
                'lighting_adjustment': self.lighting_adjustment,
                'color_correction': self.color_correction
            }
            
            metadata_file = os.path.join(template_output_dir, f"{template_id}_metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 保存简化的状态文件（兼容性）
            state_file = os.path.join(template_output_dir, "model_state.pkl")
            with open(state_file, 'wb') as f:
                pickle.dump({'status': 'completed', 'template_id': template_id}, f)
            
            total_time = time.time() - start_time
            print(f"极速预处理完成！")
            print(f"处理统计:")
            print(f"   - 模板ID: {template_id}")
            print(f"   - 帧数: {len(frame_list_cycle)}")
            print(f"   - 耗时: {total_time:.2f}秒")
            print(f"   - 阴影修复: {'启用' if self.shadow_fix_enabled else '禁用'}")
            print(f"   - 缓存文件: {cache_file}")
            
            return True
            
        except Exception as e:
            print(f"预处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description='优化版模板预处理')
    parser.add_argument('--template_path', type=str, required=True, help='模板图像路径')
    parser.add_argument('--output_dir', type=str, required=True, help='输出目录')
    parser.add_argument('--template_id', type=str, required=True, help='模板ID')
    parser.add_argument('--device', type=str, default='cuda:0', help='设备')
    parser.add_argument('--disable_shadow_fix', action='store_true', help='禁用阴影修复')
    parser.add_argument('--disable_lighting', action='store_true', help='禁用光照调整')
    parser.add_argument('--disable_color_correction', action='store_true', help='禁用颜色校正')
    
    args = parser.parse_args()
    
    # 创建预处理器
    preprocessor = OptimizedPreprocessor()
    
    # 配置阴影修复选项
    preprocessor.shadow_fix_enabled = not args.disable_shadow_fix
    preprocessor.lighting_adjustment = not args.disable_lighting
    preprocessor.color_correction = not args.disable_color_correction
    
    print(f"🎨 阴影修复配置:")
    print(f"   - 阴影修复: {'启用' if preprocessor.shadow_fix_enabled else '禁用'}")
    print(f"   - 光照调整: {'启用' if preprocessor.lighting_adjustment else '禁用'}")
    print(f"   - 颜色校正: {'启用' if preprocessor.color_correction else '禁用'}")
    
    # 初始化模型
    if not preprocessor.initialize_models(args.device):
        print("模型初始化失败")
        return
    
    # 执行预处理
    success = preprocessor.preprocess_template_ultra_fast(
        args.template_path,
        args.output_dir, 
        args.template_id
    )
    
    if success:
        print("预处理成功完成")
    else:
        print("预处理失败")
        sys.exit(1)

if __name__ == "__main__":
    main()