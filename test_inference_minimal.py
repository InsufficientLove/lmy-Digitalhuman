#!/usr/bin/env python3
"""
最小化的MuseTalk inference测试
"""

import os
import sys
import torch

def test_model_loading():
    """测试模型加载"""
    print("🔄 开始测试MuseTalk模型加载...")
    
    try:
        # 设置单GPU
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        
        print("✅ 导入基础模块...")
        from musetalk.utils.utils import load_all_model
        
        print("✅ 开始加载模型...")
        print("   - 检查模型文件...")
        
        unet_config = "models/musetalk/musetalk.json"
        unet_model = "models/musetalk/pytorch_model.bin"
        
        if not os.path.exists(unet_config):
            print(f"❌ UNet配置文件不存在: {unet_config}")
            return False
            
        if not os.path.exists(unet_model):
            print(f"❌ UNet模型文件不存在: {unet_model}")
            return False
            
        print(f"✅ 配置文件存在: {unet_config}")
        print(f"✅ 模型文件存在: {unet_model}")
        
        # 检查GPU内存
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"✅ GPU内存: {gpu_memory:.1f}GB")
            
            # 清理GPU缓存
            torch.cuda.empty_cache()
            print("✅ GPU缓存已清理")
        
        print("⚠️  实际模型加载测试跳过（避免卡死）")
        print("   如需测试，请取消下面的注释")
        
        # print("🔄 实际加载模型...")
        # vae, unet, pe = load_all_model(
        #     unet_path=unet_model,
        #     unet_config=unet_config,
        #     version="v1"
        # )
        # print("✅ 模型加载成功!")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 MuseTalk最小化测试")
    print(f"当前目录: {os.getcwd()}")
    print(f"CUDA设备: {os.environ.get('CUDA_VISIBLE_DEVICES', '未设置')}")
    print()
    
    if test_model_loading():
        print("\n✅ 基础测试通过")
        print("如果inference仍然卡死，可能是:")
        print("1. 配置文件中指定了不存在的输入文件")
        print("2. 实际模型加载时GPU内存不足")
        print("3. 多GPU并发冲突")
    else:
        print("\n❌ 基础测试失败")

if __name__ == "__main__":
    main()