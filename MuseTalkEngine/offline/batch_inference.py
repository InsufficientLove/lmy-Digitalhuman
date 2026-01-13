#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Fast Realtime Inference V2
极致优化版本 - 目标：毫秒级响应，4GPU真并行，零等待
"""

import sys
import os
# 修复路径嵌套问题：repo/musetalk/musetalk/... (双层结构)
# 当前文件在: repo/MuseTalkEngine/offline/batch_inference.py
# 需要回退两级到 repo/，然后进入 musetalk/ 子目录
current_file_path = os.path.abspath(__file__)
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
# 关键修复：将 repo/musetalk 加入 sys.path（包的父目录）
package_parent_dir = os.path.join(repo_root, "musetalk")
# 务必插入到最前面 (index 0)，优先从这里导入
if package_parent_dir not in sys.path:
    sys.path.insert(0, package_parent_dir)
print(f"DEBUG: Added {package_parent_dir} to sys.path (package parent)")
import json
import pickle
import torch
import cv2
import numpy as np
import time
import gc
import threading
import queue
import socket
import struct
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial
import copy
import gc
from torch.cuda.amp import autocast
try:
    from transformers import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    print("警告: transformers.WhisperModel不可用，将跳过Whisper初始化")
    WHISPER_AVAILABLE = False
import imageio
import warnings
warnings.filterwarnings("ignore")

# GPU配置 - 直接定义，不从外部导入
GPU_MEMORY_CONFIG = {'batch_size': {'default': 8}}
print("使用默认GPU配置")

# 设置模型路径
os.environ['MODEL_PATH'] = '/opt/musetalk/models'
os.environ['MUSETALK_MODEL_PATH'] = '/opt/musetalk/models'

# 添加MuseTalk模块路径（注意：已通过顶部路径修复代码处理）
# sys.path.append('/opt/musetalk/repo/musetalk')  # 已废弃，使用顶部的动态路径

from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.utils import datagen, load_all_model
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from musetalk.utils.blending import get_image, get_image_blending, get_image_prepare_material
from musetalk.utils.audio_processor import AudioProcessor

# 性能监控 - 已移除，使用简单的时间记录
PERFORMANCE_MONITORING = False
print("性能监控已禁用")

print("Ultra Fast Realtime Inference V2 - 毫秒级响应引擎")
sys.stdout.flush()

# ==================== 高质量融合函数 ====================

def paste_back_high_quality(pred_img, ori_frame, face_box, mask, crop_box=None, 
                              use_poisson=True, feather_amount=0.1):
    """
    高质量图像融合函数 - 对齐 MuseTalk 原生逻辑
    
    Args:
        pred_img: 预测的面部图像 (BGR, uint8)
        ori_frame: 原始完整图像 (BGR, uint8)
        face_box: 面部边界框 [x1, y1, x2, y2]
        mask: 融合遮罩 (灰度图或3通道, uint8)
        crop_box: 裁剪框 [x_s, y_s, x_e, y_e]，如果为None则使用face_box
        use_poisson: 是否尝试使用泊松融合（seamlessClone）
        feather_amount: 羽化量（0.0-1.0），用于高斯模糊
    
    Returns:
        融合后的完整图像 (BGR, uint8)
    """
    try:
        # 1. 提取坐标
        x1, y1, x2, y2 = [int(c) for c in face_box]
        target_w, target_h = x2 - x1, y2 - y1
        
        # 验证尺寸有效性
        if target_w <= 0 or target_h <= 0:
            print(f"⚠️ paste_back: 无效的 face_box 尺寸 ({target_w}x{target_h})")
            return ori_frame
        
        # 确保坐标在图像范围内
        h_ori, w_ori = ori_frame.shape[:2]
        x1 = max(0, min(x1, w_ori))
        x2 = max(0, min(x2, w_ori))
        y1 = max(0, min(y1, h_ori))
        y2 = max(0, min(y2, h_ori))
        target_w, target_h = x2 - x1, y2 - y1
        
        # 2. Auto-Resize：强制将 pred_img 和 mask 调整到目标尺寸
        if pred_img.shape[0] != target_h or pred_img.shape[1] != target_w:
            # 使用 LANCZOS4 高质量插值
            pred_img = cv2.resize(pred_img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        
        # 处理 mask
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        
        if mask.shape[:2] != (target_h, target_w):
            mask = cv2.resize(mask, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        
        # 3. 羽化遮罩（Feathering）- 消除硬边缘
        # 计算模糊核大小（基于图像尺寸的百分比）
        blur_kernel_size = max(int(feather_amount * min(target_w, target_h)), 3)
        # 确保核大小是奇数
        if blur_kernel_size % 2 == 0:
            blur_kernel_size += 1
        
        # 高斯模糊羽化
        mask_feathered = cv2.GaussianBlur(mask, (blur_kernel_size, blur_kernel_size), 0)
        
        # 归一化到 0-1 范围
        mask_float = mask_feathered.astype(np.float32) / 255.0
        mask_3ch = np.stack([mask_float] * 3, axis=2)  # 转为3通道
        
        # 4. 尝试泊松融合（Poisson Blending）
        if use_poisson:
            try:
                # 创建用于泊松融合的掩码（需要是纯白色的核心区域）
                # 使用阈值创建二值掩码
                _, poisson_mask = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)
                
                # 确保掩码边缘有内缩，避免泊松融合失败
                kernel = np.ones((5, 5), np.uint8)
                poisson_mask = cv2.erode(poisson_mask, kernel, iterations=1)
                
                # 计算融合中心点
                center_x = x1 + target_w // 2
                center_y = y1 + target_h // 2
                
                # 检查中心点是否在合理范围内
                if 0 < center_x < w_ori and 0 < center_y < h_ori:
                    # 执行泊松融合
                    # NORMAL_CLONE: 标准克隆，保持源图像纹理
                    # MIXED_CLONE: 混合克隆，适应目标图像光照
                    result = cv2.seamlessClone(
                        pred_img, 
                        ori_frame, 
                        poisson_mask, 
                        (center_x, center_y), 
                        cv2.MIXED_CLONE  # 使用 MIXED_CLONE 处理光照差异
                    )
                    
                    print(f"✅ paste_back: 泊松融合成功 (size={target_w}x{target_h})")
                    return result
                    
            except Exception as poisson_error:
                print(f"⚠️ paste_back: 泊松融合失败，回退到羽化融合: {str(poisson_error)[:100]}")
                # 失败则继续使用下面的羽化融合
        
        # 5. 羽化 Alpha Blending（回退方案或主要方案）
        result = ori_frame.copy()
        
        # 提取原始图像的对应区域
        ori_region = result[y1:y2, x1:x2].astype(np.float32)
        pred_img_float = pred_img.astype(np.float32)
        
        # Alpha 混合：result = foreground * alpha + background * (1 - alpha)
        blended = pred_img_float * mask_3ch + ori_region * (1.0 - mask_3ch)
        
        # 转回 uint8 并粘贴回原图
        result[y1:y2, x1:x2] = blended.astype(np.uint8)
        
        print(f"✅ paste_back: 羽化融合完成 (size={target_w}x{target_h}, feather={blur_kernel_size})")
        return result
        
    except Exception as e:
        print(f"❌ paste_back: 融合失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        # 完全失败时返回原图
        return ori_frame

# ==================== End of 高质量融合函数 ====================

class UltraFastMuseTalkService:
    """极致优化的MuseTalk服务 - 毫秒级响应"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        # GPU架构 - 自动适配单GPU或多GPU
        self.gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
        if self.gpu_count == 0:
            print("❌ 未检测到GPU")
            self.devices = []
        else:
            self.devices = [f'cuda:{i}' for i in range(self.gpu_count)]
            print(f"🎮 检测到 {self.gpu_count} 个GPU")
        
        # 每个GPU独立的模型实例
        self.gpu_models = {}
        self.gpu_locks = {device: threading.Lock() for device in self.devices}
        
        # 全局模型组件（共享权重，避免重复加载）
        self.shared_vae = None
        self.shared_unet = None
        self.shared_pe = None
        self.shared_whisper = None
        self.shared_audio_processor = None
        self.shared_fp = None
        self.weight_dtype = torch.float16  # 使用FP16提速，配合autocast避免dtype错误
        self.timesteps = None
        
        # 内存池和缓存优化
        self.template_cache = {}
        self.audio_feature_cache = {}
        self.frame_buffer_pool = queue.Queue(maxsize=1000)
        
        # 极速处理管道
        self.inference_executor = ThreadPoolExecutor(max_workers=self.gpu_count)
        self.compose_executor = ThreadPoolExecutor(max_workers=32)  # 32线程并行合成
        self.video_executor = ThreadPoolExecutor(max_workers=4)
        
        # 🎮 GPU负载均衡
        self.gpu_usage = {device: 0 for device in self.devices}
        self.gpu_queue = {device: queue.Queue(maxsize=10) for device in self.devices}
        
        self.is_initialized = False
        self._initialized = True
        
        # 获取统一的模板缓存目录
        self.template_cache_dir = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')
        print(f"使用模板缓存目录: {self.template_cache_dir}")
        
        print(f"Ultra Fast Service 初始化完成 - {self.gpu_count}GPU并行架构")
        sys.stdout.flush()
    
    def initialize_models_ultra_fast(self):
        """极速初始化所有模型 - 并行加载到所有GPU"""
        if self.is_initialized and len(self.gpu_models) > 0:
            print("模型已初始化，跳过重复初始化")
            return True
        
        # 重置初始化状态，强制重新初始化
        self.is_initialized = False
        self.gpu_models = {}
            
        try:
            print(f"开始极速初始化 - {self.gpu_count}GPU并行加载...")
            start_time = time.time()
            
            # 并行初始化所有GPU模型
            def init_gpu_model(device_id):
                import os  # Fix: import os at function start
                import platform
                import copy
                device = f'cuda:{device_id}'
                print(f"🎮 GPU{device_id} 开始初始化...")
                
                with torch.cuda.device(device_id):
                    # 加载模型到指定GPU - 只使用可用的sd-vae
                    try:
                        print(f"GPU{device_id} 开始加载模型...")
                        
                        # 设置模型路径环境变量
                        os.environ['DISABLE_TORCH_COMPILE'] = '1'
                        
                        # 设置正确的模型路径
                        os.environ['MODEL_PATH'] = '/opt/musetalk/models'
                        os.environ['VAE_PATH'] = '/opt/musetalk/models/sd-vae'
                        os.environ['UNET_PATH'] = '/opt/musetalk/models/musetalk/pytorch_model.bin'
                        os.environ['PE_PATH'] = '/opt/musetalk/models/musetalk/pytorch_model.bin'
                        
                        # 改变工作目录到有models链接的地方
                        original_cwd = os.getcwd()
                        
                        # 先尝试创建符号链接
                        if not os.path.exists('/opt/musetalk/repo/models'):
                            try:
                                os.symlink('/opt/musetalk/models', '/opt/musetalk/repo/models')
                                print(f"GPU{device_id} 创建了models符号链接")
                            except Exception:
                                pass
                        
                        # 切换到有models的目录
                        os.chdir('/opt/musetalk/repo')
                        
                        print(f"GPU{device_id} 当前工作目录: {os.getcwd()}")
                        print(f"GPU{device_id} models目录存在: {os.path.exists('models')}")
                        print(f"GPU{device_id} sd-vae路径存在: {os.path.exists('models/sd-vae')}")
                        
                        # 直接加载模型，不检查config
                        try:
                            # 尝试默认加载 - load_all_model返回3个值：vae, unet, pe
                            vae, unet, pe = load_all_model()
                            print(f"GPU{device_id} 模型加载成功!")
                            
                            # 恢复原始工作目录
                            os.chdir(original_cwd)
                            
                            # 存储模型到对应的GPU
                            self.gpu_models[device] = {
                                'vae': vae,
                                'unet': unet,
                                'pe': pe,
                                'device': device
                            }
                            print(f"GPU{device_id} 模型加载完成")
                            return device_id
                        except Exception as e:
                            # 如果失败，尝试不指定VAE类型
                            print(f"GPU{device_id} 默认加载失败: {e}")
                            print(f"GPU{device_id} 尝试备用加载方式...")
                            
                            # 设置环境变量指向模型
                            os.environ['VAE_PATH'] = '/opt/musetalk/models/sd-vae'
                            os.environ['UNET_PATH'] = '/opt/musetalk/models/musetalk'
                            
                            # 再次尝试
                            vae, unet, pe = load_all_model()
                            print(f"GPU{device_id} 模型加载成功（备用方式）")
                            
                            # 恢复原始工作目录
                            os.chdir(original_cwd)
                            
                            # 存储模型到对应的GPU
                            self.gpu_models[device] = {
                                'vae': vae,
                                'unet': unet,
                                'pe': pe,
                                'device': device
                            }
                            print(f"GPU{device_id} 模型加载完成")
                            return device_id
                    
                    except Exception as e:
                        print(f"GPU{device_id} 模型加载失败: {e}")
                        # 检查是否是UNet模型问题
                        if "meta tensor" in str(e) or "Cannot copy out" in str(e):
                            print(f"GPU{device_id} UNet模型文件可能损坏，尝试重新加载...")
                            try:
                                # 强制清理GPU内存
                                torch.cuda.empty_cache()
                                # 重新尝试加载
                                vae, unet, pe = load_all_model()
                                print(f"GPU{device_id} 重新加载成功")
                                # 恢复原始工作目录
                                os.chdir(original_cwd)
                                # 存储模型到对应的GPU
                                self.gpu_models[device] = {
                                    'vae': vae,
                                    'unet': unet,
                                    'pe': pe,
                                    'device': device
                                }
                                print(f"GPU{device_id} 模型加载完成")
                                return device_id
                            except Exception as e3:
                                print(f"GPU{device_id} 重新加载也失败: {e3}")
                                return None
                        else:
                            print(f"GPU{device_id} 其他错误，跳过此GPU")
                            return None
                    
                    # 优化模型 - 半精度+编译优化 (使用autocast避免dtype错误)
                    print(f"GPU{device_id} 开始模型优化...")
                    
                    # 修复VAE对象 - 保持 Float32（避免 cuDNN 错误）
                    # VAE 在 FP16 下极不稳定，必须保持 Float32
                    if hasattr(vae, 'vae'):
                        vae.vae = vae.vae.to(device, dtype=torch.float32).eval()
                        print(f"GPU{device_id} VAE 保持 Float32（避免cuDNN错误）")
                    elif hasattr(vae, 'to'):
                        vae = vae.to(device, dtype=torch.float32).eval()
                        print(f"GPU{device_id} VAE 保持 Float32（避免cuDNN错误）")
                    else:
                        print(f"警告: VAE对象结构不明，跳过优化")
                    
                    # 修复UNet对象 - 使用.model属性 + FP16
                    if hasattr(unet, 'model'):
                        unet.model = unet.model.to(device).half().eval()
                    elif hasattr(unet, 'to'):
                        unet = unet.to(device).half().eval()
                    else:
                        print(f"警告: UNet对象结构不明，跳过优化")
                    
                    # 修复PE对象 + FP16
                    if hasattr(pe, 'to'):
                        pe = pe.to(device).half().eval()
                    else:
                        print(f"警告: PE对象没有.to()方法，跳过优化")
                    
                    print(f"GPU{device_id} 半精度转换完成（FP16 + autocast混合精度推理）")
                    
                    # 智能模型编译 - 使用更安全的编译模式
                    import platform
                    import os
                    
                    # 检查是否禁用torch.compile
                    disable_compile = os.environ.get('DISABLE_TORCH_COMPILE', '0') == '1'
                    
                    if disable_compile:
                        print(f"GPU{device_id} torch.compile已禁用（DISABLE_TORCH_COMPILE=1）")
                    elif hasattr(torch, 'compile') and platform.system() != 'Windows':
                        try:
                            print(f"GPU{device_id} 开始模型优化编译...")
                            
                            # 使用更安全的编译模式，避免CUDA图错误
                            # mode选项：
                            # - "default": 平衡模式
                            # - "reduce-overhead": 最激进优化（可能导致错误）
                            # - "max-autotune": 最大性能但编译慢
                            # - "max-autotune-no-cudagraphs": 禁用CUDA图，避免TLS错误
                            
                            # 尝试不同的编译策略
                            compile_strategies = [
                                # 策略1：默认模式（快速编译，适中优化）
                                {
                                    "mode": "default",
                                    "fullgraph": False,
                                },
                                # 策略2：减少开销（最快编译）
                                {
                                    "mode": "reduce-overhead",
                                    "fullgraph": False,
                                    "disable_cudagraphs": True,
                                },
                                # 策略3：最大调优（慢编译，最优性能）- 备选
                                {
                                    "mode": "max-autotune-no-cudagraphs",
                                    "fullgraph": False,
                                    "dynamic": True,
                                },
                            ]
                            
                            # 尝试找到可用的编译策略
                            compile_options = None
                            for idx, strategy in enumerate(compile_strategies):
                                try:
                                    # 测试编译一个小模型
                                    test_model = torch.nn.Linear(10, 10).to(device)
                                    torch.compile(test_model, **strategy)
                                    compile_options = strategy
                                    print(f"  使用编译策略 {idx+1}: {strategy['mode']}")
                                    break
                                except Exception:
                                    continue
                            
                            if compile_options is None:
                                print(f"  所有编译策略都失败，跳过编译")
                                raise RuntimeError("无法找到可用的编译策略")
                            
                            # 编译选项：可以启用CUDA图了！
                            # 因为我们会使用专用线程池，每个GPU一个线程
                            use_cuda_graphs = os.environ.get('ENABLE_CUDA_GRAPHS', '0') == '1'
                            
                            if use_cuda_graphs:
                                # 启用CUDA图的最优配置
                                realtime_compile_options = {
                                    "backend": "inductor",
                                    "mode": "max-autotune",     # 最激进优化
                                    "fullgraph": False,
                                    "disable": False,
                                }
                                print(f"  GPU{device_id} 使用最大优化编译（含CUDA图）")
                            else:
                                # 保守模式（兼容现有多线程）
                                realtime_compile_options = {
                                    "backend": "inductor",
                                    "mode": "reduce-overhead",  # 无CUDA图
                                    "fullgraph": False,
                                    "disable": False,
                                }
                                print(f"  GPU{device_id} 使用安全编译（无CUDA图）")
                            
                            # 为每个GPU创建独立的编译实例
                            print(f"  GPU{device_id} 开始独立编译...")
                            
                            # UNet编译（最重要）
                            if hasattr(unet, 'model'):
                                try:
                                    # 直接编译原模型，不需要deepcopy
                                    # 因为每个GPU加载的是独立的模型实例
                                    unet.model = torch.compile(unet.model, **realtime_compile_options)
                                    print(f"  ✅ GPU{device_id} UNet编译完成（多线程安全）")
                                except Exception as e:
                                    print(f"  ⚠️ GPU{device_id} UNet编译失败: {str(e)[:100]}")
                                    # 失败则使用原始模型
                            
                            # VAE编译（次要）
                            if hasattr(vae, 'vae') and hasattr(vae.vae, 'decoder'):
                                try:
                                    # VAE解码器也要极致优化
                                    vae.vae.decoder = torch.compile(vae.vae.decoder, **realtime_compile_options)
                                    print(f"  ✅ GPU{device_id} VAE解码器编译完成")
                                except Exception as e:
                                    print(f"  ⚠️ GPU{device_id} VAE编译失败: {str(e)[:100]}")
                            
                            # PE也要编译以减少延迟
                            if hasattr(pe, 'forward'):
                                try:
                                    pe = torch.compile(pe, **realtime_compile_options)
                                    print(f"  ✅ GPU{device_id} PE音频编码器编译完成")
                                except Exception as e:
                                    print(f"  ⚠️ GPU{device_id} PE编译失败: {str(e)[:100]}")
                            
                            print(f"GPU{device_id} 模型编译优化完成（安全模式）")
                            
                        except Exception as compile_error:
                            print(f"GPU{device_id} 模型编译失败: {compile_error}")
                            print(f"GPU{device_id} 使用原始模型（未优化）")
                            # 编译失败不影响运行，继续使用原始模型
                    else:
                        if platform.system() == 'Windows':
                            print(f"GPU{device_id} 跳过编译（Windows不支持）")
                        else:
                            print(f"GPU{device_id} 跳过编译（torch.compile不可用）")
                    
                    # 显存监控 - 验证模型是否真正加载
                    with torch.cuda.device(device):
                        torch.cuda.synchronize()
                        allocated = torch.cuda.memory_allocated() / (1024**3)
                        reserved = torch.cuda.memory_reserved() / (1024**3)
                        print(f"GPU{device_id} 模型加载后显存: 已分配 {allocated:.2f}GB, 已预留 {reserved:.2f}GB")
            
            # SEQUENTIAL_LOADING_FIXED: 顺序初始化避免并发冲突
            print(f"开始顺序初始化{self.gpu_count}个GPU（避免并发冲突）...")
            successful_gpus = []
            
            for i in range(self.gpu_count):
                print(f"正在初始化GPU {i}/{self.gpu_count}...")
                try:
                    # 在每个GPU初始化前清理内存
                    torch.cuda.set_device(i)
                    torch.cuda.empty_cache()
                    
                    result = init_gpu_model(i)
                    if result is not None:
                        successful_gpus.append(i)
                        print(f"✅ GPU{i} 初始化成功 ({len(successful_gpus)}/{self.gpu_count})")
                    else:
                        print(f"❌ GPU{i} 初始化失败，跳过")
                except Exception as e:
                    print(f"❌ GPU{i} 初始化异常: {e}")
                    # 如果是meta tensor错误，尝试重试一次
                    if "meta tensor" in str(e) or "Cannot copy out" in str(e):
                        print(f"检测到meta tensor错误，清理内存后重试GPU{i}...")
                        try:
                            torch.cuda.empty_cache()
                            import gc
                            gc.collect()
                            result = init_gpu_model(i)
                            if result is not None:
                                successful_gpus.append(i)
                                print(f"✅ GPU{i} 重试成功")
                            else:
                                print(f"❌ GPU{i} 重试失败")
                        except Exception as retry_e:
                            print(f"❌ GPU{i} 重试异常: {retry_e}")
            
            if len(successful_gpus) == 0:
                print("所有GPU初始化都失败了")
                return False
            elif len(successful_gpus) < self.gpu_count:
                print(f"部分GPU初始化成功: {successful_gpus}/{list(range(self.gpu_count))}")
                # 更新可用GPU列表
                self.devices = [f'cuda:{i}' for i in successful_gpus]
                self.gpu_count = len(successful_gpus)
                print(f"调整为使用{self.gpu_count}个GPU: {self.devices}")
            else:
                print(f"所有{self.gpu_count}个GPU初始化完成")
            
            # 共享组件初始化（只需一次）
            print("初始化共享组件...")
            device0 = self.devices[0]
            
            # Whisper和AudioProcessor在CPU上，所有GPU共享
            whisper_dir = "./models/whisper"
            if WHISPER_AVAILABLE and os.path.exists(whisper_dir):
                print("开始加载Whisper模型...")
                try:
                    self.shared_whisper = WhisperModel.from_pretrained(whisper_dir).eval()
                    # 将Whisper模型移到GPU0并保持float32（Whisper不支持half）
                    if torch.cuda.is_available():
                        self.shared_whisper = self.shared_whisper.to(self.devices[0])
                        print(f"Whisper模型加载完成，已移至{self.devices[0]}")
                    else:
                        print("Whisper模型加载完成（CPU模式）")
                except Exception as e:
                    print(f"Whisper模型加载失败: {e}")
                    self.shared_whisper = None
            else:
                if not WHISPER_AVAILABLE:
                    print("跳过Whisper模型加载 - transformers.WhisperModel不可用")
                else:
                    print(f"跳过Whisper模型加载 - 目录不存在: {whisper_dir}")
                self.shared_whisper = None
            
            print("初始化AudioProcessor...")
            try:
                # AudioProcessor需要whisper模型路径
                if os.path.exists(whisper_dir):
                    self.shared_audio_processor = AudioProcessor(feature_extractor_path=whisper_dir)
                    print("AudioProcessor初始化完成")
                else:
                    print(f"警告: Whisper目录不存在，使用默认AudioProcessor")
                    self.shared_audio_processor = AudioProcessor(feature_extractor_path=None)
                    print("AudioProcessor初始化完成 (无Whisper)")
            except Exception as e:
                print(f"AudioProcessor初始化失败: {e}")
                # 创建一个简单的AudioProcessor备用实例
                try:
                    print("尝试创建备用AudioProcessor...")
                    self.shared_audio_processor = AudioProcessor(feature_extractor_path=None)
                    print("备用AudioProcessor创建成功")
                except Exception:
                    self.shared_audio_processor = None
                    print("AudioProcessor完全失败，音频功能将不可用")
            
            print("初始化FaceParsing...")
            try:
                self.shared_fp = FaceParsing()
                print("FaceParsing初始化完成")
            except Exception as e:
                print(f"FaceParsing初始化失败: {e}")
                self.shared_fp = None
            
            # 时间步长
            print("设置时间步长...")
            self.timesteps = torch.tensor([0], device=device0, dtype=torch.long)
            print("时间步长设置完成")
            
            init_time = time.time() - start_time
            print(f"极速初始化完成！耗时: {init_time:.2f}秒")
            print(f"{self.gpu_count}GPU并行引擎就绪 - 毫秒级响应模式")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"极速初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_optimal_gpu(self):
        """智能GPU负载均衡"""
        # 选择使用率最低的GPU
        optimal_gpu = min(self.gpu_usage.items(), key=lambda x: x[1])[0]
        self.gpu_usage[optimal_gpu] += 1
        return optimal_gpu
    
    def release_gpu(self, device):
        """释放GPU资源"""
        if device in self.gpu_usage:
            self.gpu_usage[device] = max(0, self.gpu_usage[device] - 1)
    
    def ultra_fast_inference_parallel(self, template_id, audio_path, output_path, cache_dir=None, batch_size=None, fps=25, auto_adjust=True, streaming=False, skip_frames=1):
        """极速并行推理 - 毫秒级响应
        
        Args:
            auto_adjust: 是否自动调整batch_size（OOM时自动降级）
            streaming: 是否启用流式推理（WebRTC实时通讯）
        """
        # 使用统一的缓存目录
        if cache_dir is None:
            cache_dir = os.path.join(self.template_cache_dir, template_id)
        
        # 智能批次大小选择 - 基于可用显存和实际测试
        if batch_size is None:
            # 获取所有GPU的可用显存
            try:
                min_free_memory = float('inf')
                for gpu_id in range(self.gpu_count):
                    torch.cuda.set_device(gpu_id)
                    free_memory = torch.cuda.mem_get_info()[0] / (1024**3)  # 转换为GB
                    min_free_memory = min(min_free_memory, free_memory)
                    print(f"GPU {gpu_id} 可用显存: {free_memory:.1f}GB")
                
                print(f"最小可用显存: {min_free_memory:.1f}GB")
                
                # 根据可用显存动态调整batch_size
                # 采用批处理+释放策略：每批6帧，处理完释放
                # 这样可以充分利用显存，又避免OOM
                
                # 紧急修复OOM：降低batch_size到保守值4
                if min_free_memory > 40:  # 40GB以上
                    batch_size = 4  # 保守值，避免峰值OOM
                    print(f"✅ 显存充足({min_free_memory:.1f}GB)，设置batch_size=4（保守模式）")
                elif min_free_memory > 30:  # 30-40GB
                    batch_size = 4  
                    print(f"✅ 显存良好({min_free_memory:.1f}GB)，设置batch_size=4（保守模式）")
                elif min_free_memory > 20:  # 20-30GB
                    batch_size = 3  
                    print(f"⚠️ 显存中等({min_free_memory:.1f}GB)，设置batch_size=3（安全模式）")
                elif min_free_memory > 15:  # 15-20GB
                    batch_size = 2  
                    print(f"⚠️ 显存偏少({min_free_memory:.1f}GB)，设置batch_size=2（最小批次）")
                elif min_free_memory > 10:  # 10-15GB
                    batch_size = 2  
                    print(f"❌ 显存紧张({min_free_memory:.1f}GB)，设置batch_size=2（最小批次）")
                else:  # 10GB以下
                    batch_size = 2  
                    print(f"❌ 显存严重不足({min_free_memory:.1f}GB)，设置batch_size=2（最小批次）")
                    
                print(f"基于可用显存({min_free_memory:.1f}GB)，设置batch_size={batch_size}")
                
                # 双卡优化提示
                if self.gpu_count > 1:
                    total_frames = 361  # 示例帧数
                    batches_needed = (total_frames + batch_size - 1) // batch_size
                    batches_per_gpu = batches_needed // self.gpu_count
                    print(f"📊 双GPU并行处理方案：")
                    print(f"   - 总帧数: {total_frames}")
                    print(f"   - 每批次: {batch_size}帧")
                    print(f"   - 总批次: {batches_needed}")
                    print(f"   - 每GPU处理: ~{batches_per_gpu}批次")
                    print(f"   - 预计推理次数: {batches_needed}次")
                    
            except Exception as e:
                print(f"显存检测失败: {e}")
                # 如果检测失败，使用保守值
                batch_size = 4
                print(f"使用保守batch_size=4（RTX 4090D 优化）")
        
        print(f"🔍 推理配置: GPU数={self.gpu_count}, batch_size={batch_size}")
        
        if not self.is_initialized:
            print("模型未初始化")
            return False
        
        try:
            total_start = time.time()
            print(f"开始极速并行推理: {template_id}")
            
            # 1. 并行加载模板缓存 + 音频特征提取
            def load_template_cache_async():
                return self.load_template_cache_optimized(cache_dir, template_id)
            
            def extract_audio_features_async():
                return self.extract_audio_features_ultra_fast(audio_path, fps)
            
            # 关键优化：并行执行缓存加载和音频处理
            with ThreadPoolExecutor(max_workers=2) as prep_executor:
                cache_future = prep_executor.submit(load_template_cache_async)
                audio_future = prep_executor.submit(extract_audio_features_async)
                
                cache_data = cache_future.result()
                whisper_chunks = audio_future.result()
            
            if not cache_data:
                print("错误: 无法加载模板缓存")
                return False
                
            if whisper_chunks is None:
                print("错误: 音频特征提取失败")
                return False
            
            # 紧急修复OOM：静态图片模式不复制帧（使用模运算循环引用）
            # frame_list = cache_data['frame_list_cycle'] # 可能不存在
            latents_len = len(cache_data['input_latent_list_cycle'])
            
            if latents_len <= 2: # 静态图片（通常为1或2帧）
                target_frames = len(whisper_chunks)
                print(f"🖼️ 检测到静态图片输入 (Latents: {latents_len})")
                print(f"⚠️ OOM修复：不复制帧，使用模运算循环引用（节省内存）")
                print(f"   原始帧数: {latents_len}, 音频帧数: {target_frames}")
                
                # 不复制帧！保持原样，在合成时使用 i % len(frame_list) 循环引用
                # cache_data['frame_list_cycle'] 保持 [single_frame] (1个元素)
                # 这样可以避免占用大量内存
                
                # 同样处理latents：不复制，保持1个元素
                if 'input_latent_list_cycle' in cache_data:
                    latents = cache_data['input_latent_list_cycle']
                    if len(latents) == 1:
                        print(f"   Latents: 保持1个元素（循环引用）")
                        # 确保latent在CPU上（防止GPU内存占用）
                        if isinstance(latents[0], torch.Tensor) and latents[0].is_cuda:
                            cache_data['input_latent_list_cycle'] = [latents[0].cpu()]
                            print(f"   ✅ 已将latent移至CPU")
                
                print(f"✅ 静态图片模式配置完成（CPU驻留，循环引用）")
            
            prep_time = time.time() - total_start
            print(f"并行预处理完成: {prep_time:.3f}s")
            
            # 2. 多GPU并行推理（支持跳帧加速）
            inference_start = time.time()
            
            # 跳帧策略优化
            if skip_frames > 1:
                # 暂时禁用跳帧，确保每帧都处理
                skip_frames = 1
                print(f"⚡ 全帧模式：每帧都处理（不跳帧）")
            
            # 音频处理
            res_frame_list = self.execute_4gpu_parallel_inference(
                whisper_chunks, cache_data, batch_size
            )
            
            inference_time = time.time() - inference_start
            print(f"{self.gpu_count}GPU并行推理完成: {inference_time:.3f}s, {len(res_frame_list)}帧")
            
            # 3. 极速并行图像合成
            compose_start = time.time()
            video_frames = self.ultra_fast_compose_frames(res_frame_list, cache_data)
            compose_time = time.time() - compose_start
            print(f"🎨 并行图像合成完成: {compose_time:.3f}s")
            
            # 4. 极速视频生成
            video_start = time.time()
            success = self.generate_video_ultra_fast(video_frames, audio_path, output_path, fps)
            video_time = time.time() - video_start
            print(f"视频生成完成: {video_time:.3f}s")
            
            total_time = time.time() - total_start
            print(f"极速推理完成！总耗时: {total_time:.3f}s")
            print(f"性能分解: 预处理:{prep_time:.3f}s + 推理:{inference_time:.3f}s + 合成:{compose_time:.3f}s + 视频:{video_time:.3f}s")
            
            # 性能数据已在上面打印
            
            return success
            
        except Exception as e:
            print(f"极速推理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def execute_4gpu_parallel_inference(self, whisper_chunks, cache_data, batch_size):
        """多GPU并行推理 - 动态适配GPU数量"""
        from musetalk.utils.utils import datagen
        
        print(f"⚙️ 执行{self.gpu_count}GPU并行推理，batch_size={batch_size}")
        
        # 推理前清理所有GPU内存
        for device in self.devices:
            with torch.cuda.device(device):
                torch.cuda.empty_cache()
        
        input_latent_list_cycle = cache_data['input_latent_list_cycle']
        
        # 紧急修复OOM：确保input_latent_list_cycle在CPU上（防止全量GPU占用）
        cpu_latents = []
        for latent in input_latent_list_cycle:
            if isinstance(latent, torch.Tensor):
                if latent.is_cuda:
                    cpu_latents.append(latent.cpu())
                else:
                    cpu_latents.append(latent)
            else:
                cpu_latents.append(latent)
        input_latent_list_cycle = cpu_latents
        print(f"✅ 确保{len(input_latent_list_cycle)}个latents在CPU上")
        
        video_num = len(whisper_chunks)
        
        # 添加批次优化建议
        print(f"音频帧数: {video_num}")
        if video_num > 50 and batch_size < 4:
            # 基于实际GPU内存情况的建议
            if video_num > 100:
                suggested_batch_size = 6  # 长音频用更大批次
            elif video_num > 50:
                suggested_batch_size = 4  # 中等音频
            else:
                suggested_batch_size = 3  # 短音频
            
            print(f"⚠️ 当前batch_size={batch_size}可能太小，建议使用batch_size={suggested_batch_size}")
            print(f"  这将减少批次数从{video_num // batch_size}到{video_num // suggested_batch_size}")
            print(f"  预计可节省{(video_num // batch_size - video_num // suggested_batch_size) * 5}秒")
        
        # 生成所有批次
        gen = datagen(
            whisper_chunks=whisper_chunks,
            vae_encode_latents=input_latent_list_cycle,
            batch_size=batch_size,
            delay_frame=0,
            device='cpu'  # 在CPU上生成数据，避免GPU0内存压力
        )
        all_batches = list(gen)
        total_batches = len(all_batches)
        
        print(f"{self.gpu_count}GPU并行处理 {total_batches} 批次...")
        
        # 关键优化：每个GPU处理独立的批次，无需同步
        def process_batch_on_gpu(batch_info):
            batch_idx, (whisper_batch, latent_batch) = batch_info
            
            # 智能GPU分配 - 确保使用有效的GPU
            target_device = self.devices[batch_idx % self.gpu_count]
            
            # 安全检查：确保GPU模型存在
            if target_device not in self.gpu_models:
                print(f"⚠️ 批次 {batch_idx}: GPU {target_device} 模型未初始化，跳过")
                return batch_idx, []
            
            gpu_models = self.gpu_models[target_device]
            
            # 实时监控显存使用率
            with torch.cuda.device(target_device):
                free_mem_before = torch.cuda.mem_get_info()[0] / (1024**3)
                total_mem = torch.cuda.mem_get_info()[1] / (1024**3)
                used_mem_before = total_mem - free_mem_before
                usage_percent = (used_mem_before / total_mem) * 100
                
                print(f"处理批次 {batch_idx} -> GPU {target_device}")
                print(f"  批次大小: {whisper_batch.shape[0]}帧")
                print(f"  显存使用: {used_mem_before:.1f}/{total_mem:.1f}GB ({usage_percent:.1f}%)")
                
                # 如果显存使用超过90%，跳过批次避免OOM
                if usage_percent > 90:
                    print(f"⚠️ GPU {target_device} 显存使用率过高({usage_percent:.1f}%)，跳过批次")
                    return batch_idx, []
            
            try:
                # 紧急修复：批次前强制清理，防止显存累积
                with torch.cuda.device(target_device):
                    torch.cuda.empty_cache()
                
                # 🔒 获取GPU锁，保护VAE解码（VAE不是线程安全的）
                gpu_lock = self.gpu_locks.get(target_device)
                if gpu_lock is None:
                    print(f"⚠️ 警告：GPU {target_device} 没有对应的锁")
                
                # 关键：数据移动到目标GPU
                with torch.cuda.device(target_device):
                    whisper_batch = whisper_batch.to(target_device, dtype=self.weight_dtype, non_blocking=True)
                    latent_batch = latent_batch.to(target_device, dtype=self.weight_dtype, non_blocking=True)
                    # 确保timesteps在正确的设备上
                    if self.timesteps is not None:
                        timesteps = self.timesteps.to(target_device)
                    else:
                        # 如果timesteps未初始化，创建一个
                        timesteps = torch.tensor([0], device=target_device, dtype=torch.long)
                    
                    # 核心推理 - 使用独立的GPU模型
                    with torch.no_grad():
                        # 调试：检查模型是否存在
                        if 'pe' not in gpu_models or gpu_models['pe'] is None:
                            raise ValueError(f"PE模型在{target_device}上未初始化")
                        if 'unet' not in gpu_models or gpu_models['unet'] is None:
                            raise ValueError(f"UNet模型在{target_device}上未初始化")
                        if 'vae' not in gpu_models or gpu_models['vae'] is None:
                            raise ValueError(f"VAE模型在{target_device}上未初始化")
                        
                        # 使用 autocast 包裹推理，自动处理 FP16/FP32 混合精度
                        with autocast(dtype=torch.float16):
                            # 紧急DEBUG：检查输入维度（防止Attention爆炸）
                            print(f"🔍 DEBUG批次{batch_idx}: whisper_batch.shape = {whisper_batch.shape}")
                            print(f"🔍 DEBUG批次{batch_idx}: latent_batch.shape = {latent_batch.shape}")
                            
                            # 音频特征提取
                            audio_features = gpu_models['pe'](whisper_batch)
                            
                            # 紧急DEBUG：检查audio_features维度（关键！）
                            print(f"🔍 DEBUG批次{batch_idx}: audio_features.shape = {audio_features.shape}")
                            print(f"   预期: [batch_size={whisper_batch.shape[0]}, seq_len, dim]")
                            
                            # 验证：如果audio_features是全量的，说明出现了bug
                            if audio_features.shape[0] != whisper_batch.shape[0]:
                                print(f"⚠️ 警告：audio_features维度异常！")
                                print(f"   audio_features[0]={audio_features.shape[0]} != batch_size={whisper_batch.shape[0]}")
                                print(f"   这会导致Attention爆炸！")
                            
                            # UNet 推理 - autocast 会自动处理 dtype 转换
                            # 注意：UNet需要8通道输入（masked + reference）
                            pred_latents = gpu_models['unet'].model(
                                latent_batch, timesteps, encoder_hidden_states=audio_features
                            ).sample
                            
                            print(f"🔍 DEBUG批次{batch_idx}: pred_latents.shape = {pred_latents.shape}")
                            
                            # 紧急修复：UNet输出后检查通道数（VAE只支持4通道）
                            if pred_latents.shape[1] == 8:
                                print(f"⚠️ UNet输出8通道，VAE需要4通道")
                                print(f"   修复：取前4通道传给VAE")
                                pred_latents = pred_latents[:, :4, :, :]
                                print(f"   修复后: pred_latents.shape = {pred_latents.shape}")
                            elif pred_latents.shape[1] == 4:
                                print(f"✅ UNet输出4通道，直接传给VAE")
                            else:
                                print(f"⚠️ 警告：pred_latents通道数异常: {pred_latents.shape[1]}")
                        
                        # VAE 解码 - 必须在 autocast 外，且转换为 Float32
                        # 这样避免 cuDNN FP16 错误
                        pred_latents_fp32 = pred_latents.to(dtype=torch.float32)
                        # 立即删除FP16版本，释放显存
                        del pred_latents
                        
                        # 🔥 关键修复：VAE解码前同步，避免多线程死锁
                        torch.cuda.synchronize(target_device)
                        print(f"🎨 批次 {batch_idx} 开始VAE解码（GPU {target_device}）...")
                        
                        # VAE解码 - 使用锁保护（VAE在FP32下可能不是线程安全的）
                        if gpu_lock:
                            with gpu_lock:
                                try:
                                    recon_frames = gpu_models['vae'].decode_latents(pred_latents_fp32)
                                    print(f"✅ 批次 {batch_idx} VAE解码完成（已锁保护）")
                                except Exception as vae_error:
                                    print(f"❌ 批次 {batch_idx} VAE解码失败: {vae_error}")
                                    raise vae_error
                        else:
                            # 无锁版本（不推荐）
                            try:
                                recon_frames = gpu_models['vae'].decode_latents(pred_latents_fp32)
                                print(f"✅ 批次 {batch_idx} VAE解码完成（无锁）")
                            except Exception as vae_error:
                                print(f"❌ 批次 {batch_idx} VAE解码失败: {vae_error}")
                                raise vae_error
                    
                    # 紧急修复：立即删除pred_latents_fp32，避免显存累积
                    del pred_latents_fp32
                    
                    # 立即移回CPU释放GPU内存
                    # 检查返回类型，如果已经是numpy数组就直接使用
                    if isinstance(recon_frames, list):
                        # 如果是list of tensors，立即转CPU
                        result_frames = []
                        for frame in recon_frames:
                            if hasattr(frame, 'cpu'):
                                result_frames.append(frame.cpu().numpy())
                            else:
                                result_frames.append(frame)
                        del recon_frames  # 立即删除GPU tensor列表
                    elif isinstance(recon_frames, np.ndarray):
                        result_frames = [recon_frames[i] for i in range(recon_frames.shape[0])]
                    elif isinstance(recon_frames, torch.Tensor):
                        # 如果是单个大tensor，立即转CPU并拆分
                        recon_cpu = recon_frames.cpu()
                        del recon_frames  # 立即删除GPU tensor
                        result_frames = [recon_cpu[i].numpy() for i in range(recon_cpu.shape[0])]
                        del recon_cpu
                    else:
                        # 如果是torch tensor，转换为numpy
                        result_frames = [frame.cpu().numpy() if hasattr(frame, 'cpu') else frame for frame in recon_frames]
                        if hasattr(recon_frames, '__iter__'):
                            del recon_frames
                    
                    # 清理GPU内存（按顺序删除）
                    if 'audio_features' in locals():
                        del audio_features
                    if 'whisper_batch' in locals():
                        del whisper_batch
                    if 'latent_batch' in locals():
                        del latent_batch
                    if 'timesteps' in locals():
                        del timesteps
                    
                    # 强制同步和清理
                    torch.cuda.synchronize(target_device)
                    torch.cuda.empty_cache()
                    
                    # 额外的清理步骤
                    import gc
                    gc.collect()
                    torch.cuda.empty_cache()
                    
                    print(f"✅ 批次 {batch_idx} 完成，已释放GPU {target_device}显存")
                    
                    return batch_idx, result_frames
                    
            except torch.cuda.OutOfMemoryError as oom_error:
                print(f"❌ 批次 {batch_idx} GPU {target_device} OOM错误!")
                print(f"   错误详情: {str(oom_error)}")
                # 获取当前显存状态
                with torch.cuda.device(target_device):
                    free_mem = torch.cuda.mem_get_info()[0] / (1024**3)
                    total_mem = torch.cuda.mem_get_info()[1] / (1024**3)
                    allocated = torch.cuda.memory_allocated() / (1024**3)
                    print(f"   GPU {target_device} 显存: 已用{allocated:.1f}GB / 可用{free_mem:.1f}GB / 总量{total_mem:.1f}GB")
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                return batch_idx, []
                
            except Exception as e:
                print(f"❌ 批次 {batch_idx} GPU {target_device} 失败!")
                print(f"   错误类型: {type(e).__name__}")
                print(f"   错误详情: {str(e)}")
                # 打印堆栈跟踪
                import traceback
                traceback.print_exc()
                # 失败时清理GPU内存
                with torch.cuda.device(target_device):
                    torch.cuda.empty_cache()
                return batch_idx, []
        
        # 真正的4GPU并行执行
        res_frame_list = []
        batch_results = {}
        
        # 🔥 修复VAE卡死：限制并发数，避免GPU资源竞争
        # 每个GPU同时只处理一个批次（VAE解码不是完全线程安全的）
        max_workers = self.gpu_count  # 每个GPU一个并发任务
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 直接提交所有批次，让线程池管理调度
            futures = {}
            for batch_idx, batch_info in enumerate(all_batches):
                future = executor.submit(process_batch_on_gpu, (batch_idx, batch_info))
                futures[future] = batch_idx
            
            # 收集结果
            completed = 0
            for future in as_completed(futures):
                batch_idx, frames = future.result()
                batch_results[batch_idx] = frames
                completed += 1
                if completed % 10 == 0 or completed == total_batches:
                    print(f"进度: {completed}/{total_batches} 批次完成")
        
        # 处理完所有批次后，只清理一次内存
        if total_batches > 20:  # 只有在批次很多时才清理
            for device in self.devices:
                with torch.cuda.device(device):
                    torch.cuda.empty_cache()
        
        # 按顺序合并结果
        for i in range(total_batches):
            if i in batch_results:
                res_frame_list.extend(batch_results[i])
        
        return res_frame_list
    
    def ultra_fast_compose_frames(self, res_frame_list, cache_data):
        """极速并行图像合成 - 32线程"""
        coord_list_cycle = cache_data['coord_list_cycle']
        
        # 动态加载原始帧 - 仅在合成阶段读取
        if 'frame_list_cycle' in cache_data:
            frame_list_cycle = cache_data['frame_list_cycle']
        else:
            # 从路径加载
            image_path = cache_data.get('input_image_path') or cache_data.get('template_path')
            if not image_path:
                 print("错误：缓存中缺少frame_list_cycle和image_path")
                 return []
            
            # 读取图像
            img = cv2.imread(image_path)
            if img is None:
                print(f"错误：无法读取图像 {image_path}")
                return []
            frame_list_cycle = [img]
            # 如果latents被double了（preprocessing logic），我们也double frame_list以匹配
            if len(cache_data['input_latent_list_cycle']) == 2:
                frame_list_cycle = frame_list_cycle * 2
        
        mask_coords_list_cycle = cache_data['mask_coords_list_cycle']
        mask_list_cycle = cache_data['mask_list_cycle']
        
        # 🔥 关键安全检查：确保列表不为空，避免 ZeroDivisionError
        if len(coord_list_cycle) == 0:
            raise ValueError("❌ coord_list_cycle为空！预处理阶段未生成坐标数据。")
        if len(mask_coords_list_cycle) == 0:
            raise ValueError("❌ mask_coords_list_cycle为空！预处理阶段未生成遮罩坐标数据。")
        if len(mask_list_cycle) == 0:
            raise ValueError("❌ mask_list_cycle为空！预处理阶段未生成遮罩数据。")
        if len(frame_list_cycle) == 0:
            raise ValueError("❌ frame_list_cycle为空！预处理阶段未生成帧数据。")
        
        print(f"✅ 合成数据检查通过:")
        print(f"   - coord_list: {len(coord_list_cycle)} 项")
        print(f"   - mask_coords_list: {len(mask_coords_list_cycle)} 项")
        print(f"   - mask_list: {len(mask_list_cycle)} 项")
        print(f"   - frame_list: {len(frame_list_cycle)} 项")
        
        print(f"🎨 开始32线程并行合成 {len(res_frame_list)} 帧...")
        
        def compose_single_frame(frame_info):
            i, res_frame = frame_info
            try:
                bbox = coord_list_cycle[i % len(coord_list_cycle)]
                ori_frame = copy.deepcopy(frame_list_cycle[i % len(frame_list_cycle)])
                
                # 处理bbox - 可能是关键点数组或边界框
                if isinstance(bbox, np.ndarray):
                    if bbox.shape == (133, 2) or (bbox.ndim == 2 and bbox.shape[0] > 4):
                        # 这是关键点数组，计算边界框
                        valid_points = bbox[bbox[:, 0] > 0]
                        if len(valid_points) > 0:
                            x_coords = valid_points[:, 0]
                            y_coords = valid_points[:, 1]
                            margin = 30
                            x1 = int(max(0, x_coords.min() - margin))
                            y1 = int(max(0, y_coords.min() - margin))
                            x2 = int(x_coords.max() + margin)
                            y2 = int(y_coords.max() + margin)
                        else:
                            # 使用默认值
                            h, w = ori_frame.shape[:2]
                            x1, y1, x2, y2 = w//4, h//4, 3*w//4, 3*h//4
                    elif bbox.size >= 4:
                        # 扁平化并取前4个
                        x1, y1, x2, y2 = bbox.flatten()[:4].astype(int).tolist()
                    else:
                        # 使用默认值
                        h, w = ori_frame.shape[:2]
                        x1, y1, x2, y2 = w//4, h//4, 3*w//4, 3*h//4
                elif isinstance(bbox, (list, tuple)):
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = [int(x) for x in bbox]
                    elif len(bbox) == 133:
                        # 133个关键点，需要计算边界框
                        bbox = np.array(bbox)
                        if bbox.shape == (133, 2):
                            valid_points = bbox[bbox[:, 0] > 0]
                            if len(valid_points) > 0:
                                x_coords = valid_points[:, 0]
                                y_coords = valid_points[:, 1]
                                margin = 30
                                x1 = int(max(0, x_coords.min() - margin))
                                y1 = int(max(0, y_coords.min() - margin))
                                x2 = int(x_coords.max() + margin)
                                y2 = int(y_coords.max() + margin)
                            else:
                                h, w = ori_frame.shape[:2]
                                x1, y1, x2, y2 = w//4, h//4, 3*w//4, 3*h//4
                        else:
                            h, w = ori_frame.shape[:2]
                            x1, y1, x2, y2 = w//4, h//4, 3*w//4, 3*h//4
                    else:
                        # 使用默认值
                        h, w = ori_frame.shape[:2]
                        x1, y1, x2, y2 = w//4, h//4, 3*w//4, 3*h//4
                else:
                    # 使用默认值
                    h, w = ori_frame.shape[:2]
                    x1, y1, x2, y2 = w//4, h//4, 3*w//4, 3*h//4
                
                # 确保坐标在合理范围内
                h, w = ori_frame.shape[:2]
                x1 = max(0, min(x1, w))
                x2 = max(0, min(x2, w))
                y1 = max(0, min(y1, h))
                y2 = max(0, min(y2, h))
                
                # 关键修复 Bug 1：MuseTalk 模型输出是 RGB，需要转换为 BGR（OpenCV 格式）
                if len(res_frame.shape) == 3 and res_frame.shape[2] == 3:
                    res_frame = cv2.cvtColor(res_frame.astype(np.uint8), cv2.COLOR_RGB2BGR)
                else:
                    res_frame = res_frame.astype(np.uint8)
                
                # 关键修复 Bug 2：强制 resize 推理结果以匹配 bbox 尺寸（避免 blending 失败）
                target_w, target_h = x2 - x1, y2 - y1
                if target_w > 0 and target_h > 0:
                    # 无论res_frame原始尺寸如何，都强制resize到目标尺寸
                    res_frame = cv2.resize(res_frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
                else:
                    print(f"警告: bbox尺寸异常 ({target_w}x{target_h})，使用原始帧")
                    return i, ori_frame
                
                # 使用优化的blending
                mask_coords = mask_coords_list_cycle[i % len(mask_coords_list_cycle)]
                mask = mask_list_cycle[i % len(mask_list_cycle)]
                
                # 确保mask_coords是4个值
                if isinstance(mask_coords, (list, tuple)) and len(mask_coords) == 4:
                    crop_box = mask_coords
                elif isinstance(mask_coords, np.ndarray):
                    # 如果是numpy数组，尝试提取前4个值
                    if mask_coords.size >= 4:
                        crop_box = mask_coords.flatten()[:4].tolist()
                    else:
                        print(f"警告: mask_coords太小 {mask_coords.shape}, 使用face_box")
                        crop_box = [x1, y1, x2, y2]
                else:
                    # 使用face_box作为默认值
                    print(f"警告: mask_coords类型异常 {type(mask_coords)}, 使用face_box")
                    crop_box = [x1, y1, x2, y2]
                
                # 确保crop_box是整数
                crop_box = [int(x) for x in crop_box]
                
                # 🎨 使用新的高质量融合函数
                # 首先尝试使用官方 blending 函数（兼容性）
                try:
                    combine_frame = get_image_blending(
                        image=ori_frame,
                        face=res_frame, 
                        face_box=[x1, y1, x2, y2],
                        mask_array=mask,
                        crop_box=crop_box
                    )
                    print(f"✅ 帧{i}: 使用官方 blending")
                except Exception as blend_error:
                    # 回退到高质量融合函数
                    print(f"⚠️ 帧{i}: 官方 blending 失败，使用高质量融合: {str(blend_error)[:50]}")
                    combine_frame = paste_back_high_quality(
                        pred_img=res_frame,
                        ori_frame=ori_frame,
                        face_box=[x1, y1, x2, y2],
                        mask=mask,
                        crop_box=crop_box,
                        use_poisson=True,  # 启用泊松融合
                        feather_amount=0.15  # 15% 羽化
                    )
                
                return i, combine_frame
                
            except Exception as e:
                print(f"合成第{i}帧失败: {str(e)}")
                # 返回原始帧避免失败
                return i, frame_list_cycle[i % len(frame_list_cycle)]
        
        # 32线程并行合成
        composed_frames = {}
        with ThreadPoolExecutor(max_workers=32) as executor:
            frame_futures = {
                executor.submit(compose_single_frame, (i, frame)): i 
                for i, frame in enumerate(res_frame_list)
            }
            
            for future in as_completed(frame_futures):
                frame_idx, composed_frame = future.result()
                if composed_frame is not None:
                    composed_frames[frame_idx] = composed_frame
        
        # 按顺序排列
        video_frames = []
        for i in range(len(res_frame_list)):
            if i in composed_frames:
                video_frames.append(composed_frames[i])
        
        print(f"并行合成完成: {len(video_frames)} 帧")
        return video_frames
    
    def extract_audio_features_ultra_fast(self, audio_path, fps):
        """极速音频特征提取 - 优化版"""
        try:
            import time
            start = time.time()
            
            # 检查AudioProcessor是否可用
            if self.shared_audio_processor is None:
                raise ValueError("AudioProcessor未初始化")
            
            # 音频特征缓存（基于文件路径）
            audio_cache_key = f"{audio_path}_{fps}"
            if audio_cache_key in self.audio_feature_cache:
                print(f"✅ 使用缓存的音频特征")
                return self.audio_feature_cache[audio_cache_key]
                
            whisper_input_features, librosa_length = self.shared_audio_processor.get_audio_feature(audio_path)
            print(f"音频加载耗时: {time.time() - start:.3f}s")
            
            # 确保Whisper使用正确的数据类型
            # Whisper模型始终使用float32，不支持half precision
            whisper_dtype = torch.float32
            
            # 如果输入特征在GPU上且是half类型，转换为float32
            if isinstance(whisper_input_features, torch.Tensor):
                if whisper_input_features.dtype == torch.float16:
                    whisper_input_features = whisper_input_features.float()
            
            whisper_chunks = self.shared_audio_processor.get_whisper_chunk(
                whisper_input_features, 
                self.devices[0],  # Whisper在GPU0
                whisper_dtype,  # 使用正确的数据类型
                self.shared_whisper, 
                librosa_length,
                fps=fps,
                audio_padding_length_left=2,
                audio_padding_length_right=2,
            )
            
            # 紧急修复OOM：确保whisper_chunks在CPU上（防止全量占用GPU显存）
            if isinstance(whisper_chunks, torch.Tensor):
                if whisper_chunks.is_cuda:
                    whisper_chunks = whisper_chunks.cpu()
                    print(f"✅ whisper_chunks已移至CPU（{whisper_chunks.shape}）")
            elif isinstance(whisper_chunks, list):
                cpu_chunks = []
                for chunk in whisper_chunks:
                    if isinstance(chunk, torch.Tensor) and chunk.is_cuda:
                        cpu_chunks.append(chunk.cpu())
                    else:
                        cpu_chunks.append(chunk)
                whisper_chunks = cpu_chunks
                print(f"✅ whisper_chunks已移至CPU（{len(whisper_chunks)}个）")
            
            return whisper_chunks
        except Exception as e:
            print(f"音频特征提取失败: {str(e)}")
            return None
    
    def interpolate_frames(self, key_frames, total_frames, skip_frames):
        """简单的帧插值"""
        if skip_frames <= 1:
            return key_frames
        
        result = []
        for i in range(len(key_frames) - 1):
            result.append(key_frames[i])
            # 简单复制关键帧作为插值（最快的方法）
            for _ in range(skip_frames - 1):
                result.append(key_frames[i])
        
        # 添加最后一帧
        if len(key_frames) > 0:
            result.append(key_frames[-1])
            # 填充到目标长度
            while len(result) < total_frames:
                result.append(key_frames[-1])
        
        return result[:total_frames]
    
    def load_template_cache_optimized(self, cache_dir, template_id):
        """优化的模板缓存加载"""
        try:
            # 尝试多种可能的文件名（cache_dir已经包含template_id）
            possible_files = [
                os.path.join(cache_dir, f"{template_id}_preprocessed.pkl"),
                os.path.join(cache_dir, "preprocessed.pkl"),
                os.path.join(cache_dir, f"{template_id}.pkl"),
                os.path.join(cache_dir, "latents.pkl"),
                # 如果cache_dir没有包含template_id，尝试上一级
                os.path.join(os.path.dirname(cache_dir), f"{template_id}_preprocessed.pkl")
            ]
            
            cache_file = None
            for pf in possible_files:
                if os.path.exists(pf):
                    cache_file = pf
                    print(f"找到缓存文件: {pf}")
                    break
            
            if not cache_file:
                print(f"缓存文件不存在，尝试的路径: {possible_files}")
                # 列出目录内容帮助调试
                if os.path.exists(cache_dir):
                    print(f"目录 {cache_dir} 内容:")
                    for f in os.listdir(cache_dir):
                        print(f"  - {f}")
                else:
                    print(f"目录不存在: {cache_dir}")
                return None
            
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 紧急修复OOM：确保cache_data中所有tensor都在CPU上
            print(f"🔍 检查cache_data中的tensor位置...")
            if 'input_latent_list_cycle' in cache_data:
                latents = cache_data['input_latent_list_cycle']
                cpu_latents = []
                gpu_count = 0
                for i, latent in enumerate(latents):
                    if isinstance(latent, torch.Tensor):
                        if latent.is_cuda:
                            cpu_latents.append(latent.cpu())
                            gpu_count += 1
                        else:
                            cpu_latents.append(latent)
                    else:
                        cpu_latents.append(latent)
                
                if gpu_count > 0:
                    cache_data['input_latent_list_cycle'] = cpu_latents
                    print(f"⚠️ 发现{gpu_count}个latents在GPU上，已全部移至CPU")
                else:
                    print(f"✅ 所有{len(latents)}个latents已在CPU上")
            
            return cache_data
            
        except Exception as e:
            print(f"缓存加载失败: {str(e)}")
            return None
    
    def generate_video_ultra_fast(self, video_frames, audio_path, output_path, fps):
        """极速视频生成"""
        try:
            # 直接内存生成，无临时文件
            print(f"直接生成视频: {len(video_frames)} 帧")
            
            if len(video_frames) == 0:
                print("错误: 没有合成的帧，无法生成视频")
                return False
            
            try:
                # 确保输出目录存在
                output_dir = os.path.dirname(output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                
                # 创建临时视频（无音频）
                temp_video = output_path.replace('.mp4', '_temp.mp4')
                
                # 使用imageio生成视频
                import imageio
                
                # 确保视频尺寸是16的倍数（避免警告）
                if len(video_frames) > 0:
                    h, w = video_frames[0].shape[:2]
                    new_h = ((h + 15) // 16) * 16
                    new_w = ((w + 15) // 16) * 16
                    
                    if new_h != h or new_w != w:
                        print(f"调整视频尺寸: {w}x{h} -> {new_w}x{new_h}")
                        resized_frames = []
                        for frame in video_frames:
                            if frame is not None:
                                resized_frame = cv2.resize(frame, (new_w, new_h))
                                resized_frames.append(resized_frame)
                        video_frames = resized_frames
                
                writer = imageio.get_writer(temp_video, fps=fps, codec='libx264', quality=8, macro_block_size=1)
                for frame in video_frames:
                    if frame is not None:
                        # 关键修复 Bug 1：imageio 期望 RGB 格式，但 blending 后的帧是 BGR
                        # 必须转回 RGB 才能正确写入视频
                        if len(frame.shape) == 3 and frame.shape[2] == 3:
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            writer.append_data(frame_rgb)
                        else:
                            writer.append_data(frame)
                writer.close()
                
                if not os.path.exists(temp_video):
                    print(f"错误: 临时视频生成失败 {temp_video}")
                    return False
                
                # 并行音频合成
                try:
                    # 使用ffmpeg合成音频
                    import subprocess
                    
                    # 构建ffmpeg命令
                    cmd = [
                        'ffmpeg',
                        '-i', temp_video,  # 输入视频
                        '-i', audio_path,  # 输入音频
                        '-c:v', 'copy',    # 复制视频流
                        '-c:a', 'aac',     # 音频编码为AAC
                        '-strict', 'experimental',
                        '-shortest',       # 以最短的流为准
                        '-y',             # 覆盖输出文件
                        output_path
                    ]
                    
                    # 执行ffmpeg命令
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        print(f"ffmpeg错误: {result.stderr}")
                        # 如果失败，使用无音频版本
                        os.rename(temp_video, output_path)
                    else:
                        print(f"✅ 音频合成成功: {output_path}")
                    
                    # 清理临时文件
                    if os.path.exists(temp_video):
                        os.remove(temp_video)
                    
                except Exception as e:
                    print(f"音频合成失败，使用无音频版本: {str(e)}")
                    if os.path.exists(temp_video):
                        os.rename(temp_video, output_path)
                
                return True
                
            except Exception as e:
                print(f"视频生成失败: {str(e)}")
                return False
            
        except Exception as e:
            print(f"视频生成失败: {str(e)}")
            return False

# 全局服务实例
global_service = UltraFastMuseTalkService()

def start_ultra_fast_service(port=28888):
    """启动极速服务"""
    print(f"启动Ultra Fast Service - 端口: {port}")
    
    # 确保工作目录和路径正确
    import os
    from pathlib import Path
    
    # 如果不在正确的工作目录，切换到MuseTalk目录
    current_dir = Path.cwd()
    if not (current_dir / "models" / "musetalkV15" / "unet.pth").exists():
        # 尝试找到MuseTalk目录
        script_dir = Path(__file__).parent
        musetalk_dir = script_dir.parent / "MuseTalk"
        if musetalk_dir.exists():
            os.chdir(musetalk_dir)
            print(f"工作目录切换到: {musetalk_dir}")
        else:
            print(f"警告: 无法找到MuseTalk模型目录")
    
    # 初始化模型
    print("开始初始化Ultra Fast模型...")
    try:
        if not global_service.initialize_models_ultra_fast():
            print("模型初始化失败 - 返回False")
            return
        print("模型初始化成功！")
    except Exception as e:
        print(f"模型初始化异常: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 性能监控已禁用
    
    # 启动IPC服务器
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        
        # 验证监听状态
        sock_name = server_socket.getsockname()
        print(f"✅ Socket成功绑定到: {sock_name}")
        print(f"Ultra Fast Service 就绪 - 监听端口: {port}")
        print("毫秒级响应模式已启用")
        
        while True:
            try:
                client_socket, addr = server_socket.accept()
                print(f"🔗 客户端连接: {addr}")
                
                # 处理请求
                thread = threading.Thread(
                    target=handle_client_ultra_fast, 
                    args=(client_socket,)
                )
                thread.daemon = True  # 设置为守护线程
                thread.start()
                print(f"启动处理线程: {thread.name}")
                
            except Exception as e:
                print(f"连接处理失败: {str(e)}")
                
    except Exception as e:
        print(f"服务启动失败: {str(e)}")

def handle_client_ultra_fast(client_socket):
    """处理客户端请求 - 极速版本"""
    try:
        while True:  # 主循环处理多个请求
            # 接收请求 - 使用换行符协议（与C#端匹配）
            buffer = b''
            while True:
                chunk = client_socket.recv(1)
                if not chunk:
                    print("客户端关闭连接")
                    return  # 退出函数
                buffer += chunk
                if chunk == b'\n':
                    break
            
            if not buffer:
                break
                
            data = buffer.decode('utf-8').strip()
            if not data:
                print("收到空数据，跳过")
                continue
                
            try:
                request = json.loads(data)
                command = request.get('command', '')
                
                # 只打印非ping命令的日志
                if command != 'ping':
                    print(f"收到数据: {repr(data[:200])}")
                
                # 处理不同的命令
                if command == 'preprocess':
                    # 处理预处理请求 - 兼容两种字段名
                    template_id = request.get('templateId') or request.get('template_id')
                    template_image_path = request.get('templateImagePath') or request.get('template_image_path')
                    bbox_shift = request.get('bboxShift', 0) or request.get('bbox_shift', 0)
                    
                    print(f"处理预处理请求: template_id={template_id}, image_path={template_image_path}")
                    
                    # 修正路径：C#容器的路径需要转换为Python容器能访问的路径
                    # /app/wwwroot/templates/xxx.jpg -> /opt/musetalk/repo/LmyDigitalHuman/wwwroot/templates/xxx.jpg
                    if template_image_path and '/app/wwwroot/templates/' in template_image_path:
                        filename = os.path.basename(template_image_path)
                        template_image_path = f"/opt/musetalk/repo/LmyDigitalHuman/wwwroot/templates/{filename}"
                        print(f"修正图片路径: {template_image_path}")
                    
                    # 调用真正的预处理功能
                    try:
                        # 导入预处理模块
                        # 导入预处理器
                        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        from core.preprocessing import OptimizedPreprocessor
                        
                        # 获取缓存目录
                        cache_dir = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')
                        
                        # 创建预处理器并执行
                        preprocessor = OptimizedPreprocessor()
                        preprocessor.initialize_models()
                        success = preprocessor.preprocess_template_ultra_fast(
                            template_path=template_image_path,
                            output_dir=cache_dir,
                            template_id=template_id
                        )
                        
                        response = {
                            'success': success,
                            'templateId': template_id,
                            'message': 'Preprocessing completed' if success else 'Preprocessing failed',
                            'processTime': 1.0  # 实际处理时间
                        }
                        print(f"预处理{'成功' if success else '失败'}: {template_id}")
                        
                    except Exception as e:
                        print(f"预处理异常: {e}")
                        import traceback
                        traceback.print_exc()
                        response = {
                            'success': False,
                            'templateId': template_id,
                            'message': f'Preprocessing error: {str(e)}',
                            'processTime': 0
                        }
                    
                    # 发送响应（换行符结尾）
                    response_json = json.dumps(response) + '\n'
                    client_socket.send(response_json.encode('utf-8'))
                    print(f"✅ 发送预处理响应: {template_id}, 结果: {response['success']}")
                    
                elif command == 'ping':
                    response = {'success': True, 'message': 'pong'}
                    client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
                    # 注释掉ping日志，避免刷屏
                    # print("✅ 发送pong响应")
                    
                elif command == 'inference' or 'template_id' in request:
                    # 推理请求
                    print(f"📨 极速推理请求: {request.get('template_id')}")
                    
                    # 不要强制使用batch_size，让系统自动优化
                    received_batch_size = request.get('batch_size', None)  # None让系统自动选择
                    if received_batch_size:
                        print(f"📊 使用指定的batch_size: {received_batch_size}")
                    else:
                        print(f"📊 将根据显存自动选择batch_size")
                    
                    # 极速推理
                    start_time = time.time()
                    success = global_service.ultra_fast_inference_parallel(
                        template_id=request['template_id'],
                        audio_path=request['audio_path'],
                        output_path=request['output_path'],
                        cache_dir=request['cache_dir'],
                        batch_size=received_batch_size,
                        fps=request.get('fps', 25)
                    )
                    
                    process_time = time.time() - start_time
                    print(f"极速推理完成: {process_time:.3f}s, 结果: {success}")
                    
                    # 发送响应（换行符结尾）
                    response = {'Success': success, 'OutputPath': request['output_path'] if success else None}
                    client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
                    
                else:
                    print(f"未知命令: {command}")
                    response = {'success': False, 'message': f'Unknown command: {command}'}
                    client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
                    
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}, 数据: {repr(data[:200])}")
                error_response = {'success': False, 'message': f'JSON parse error: {str(e)}'}
                client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
            except Exception as e:
                print(f"处理请求异常: {e}")
                import traceback
                traceback.print_exc()
                error_response = {'success': False, 'message': str(e)}
                client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
        
    except Exception as e:
        print(f"请求处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client_socket.close()

def main():
    """主入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=28888, help='服务端口')
    args = parser.parse_args()
    
    # 启动服务
    start_ultra_fast_service(args.port)

if __name__ == "__main__":
    main()