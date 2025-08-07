#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试8通道预处理
验证预处理生成的latent是否为8通道（masked + reference）
"""

import os
import sys
import pickle
import numpy as np
import torch
from pathlib import Path

# 添加MuseTalk模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MuseTalk'))

def test_preprocessed_data(cache_file):
    """测试预处理缓存文件中的数据"""
    print(f"\n📋 测试预处理文件: {cache_file}")
    
    if not os.path.exists(cache_file):
        print(f"❌ 文件不存在: {cache_file}")
        return False
    
    try:
        # 加载缓存数据
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        print("\n✅ 成功加载缓存数据")
        
        # 检查必要的键
        required_keys = ['input_latent_list_cycle', 'coord_list_cycle', 
                        'frame_list_cycle', 'mask_coords_list_cycle', 'mask_list_cycle']
        
        for key in required_keys:
            if key not in cache_data:
                print(f"❌ 缺少必要的键: {key}")
                return False
        
        # 检查latent的形状
        latent_list = cache_data['input_latent_list_cycle']
        print(f"\n📊 Latent列表长度: {len(latent_list)}")
        
        if latent_list:
            # 检查第一个latent
            first_latent = latent_list[0]
            if isinstance(first_latent, torch.Tensor):
                latent_shape = first_latent.shape
            else:
                latent_shape = first_latent.shape if hasattr(first_latent, 'shape') else None
            
            print(f"📐 第一个Latent形状: {latent_shape}")
            
            # 验证通道数
            if latent_shape and len(latent_shape) >= 2:
                channels = latent_shape[1]
                if channels == 8:
                    print(f"✅ 通道数正确: {channels} (期望8通道)")
                else:
                    print(f"❌ 通道数错误: {channels} (期望8通道)")
                    return False
            else:
                print("❌ 无法获取latent形状")
                return False
            
            # 检查所有latent的一致性
            all_same_shape = True
            for i, latent in enumerate(latent_list):
                if isinstance(latent, torch.Tensor):
                    shape = latent.shape
                else:
                    shape = latent.shape if hasattr(latent, 'shape') else None
                
                if shape != latent_shape:
                    print(f"⚠️ 第{i}个latent形状不一致: {shape}")
                    all_same_shape = False
            
            if all_same_shape:
                print("✅ 所有latent形状一致")
            
        # 检查其他数据
        print(f"\n📊 其他数据统计:")
        print(f"  - coord_list长度: {len(cache_data['coord_list_cycle'])}")
        print(f"  - frame_list长度: {len(cache_data['frame_list_cycle'])}")
        print(f"  - mask_coords_list长度: {len(cache_data['mask_coords_list_cycle'])}")
        print(f"  - mask_list长度: {len(cache_data['mask_list_cycle'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 加载缓存文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试8通道预处理')
    parser.add_argument('--cache_dir', type=str, 
                       default='./model_state',
                       help='缓存目录路径')
    parser.add_argument('--template_id', type=str,
                       help='模板ID（如果不指定，将测试所有缓存文件）')
    
    args = parser.parse_args()
    
    print("🧪 8通道预处理测试工具")
    print("=" * 50)
    
    if args.template_id:
        # 测试特定模板
        cache_file = os.path.join(args.cache_dir, f"{args.template_id}_preprocessed.pkl")
        success = test_preprocessed_data(cache_file)
        if success:
            print(f"\n✅ 模板 {args.template_id} 测试通过")
        else:
            print(f"\n❌ 模板 {args.template_id} 测试失败")
    else:
        # 测试所有缓存文件
        cache_files = list(Path(args.cache_dir).glob("*_preprocessed.pkl"))
        print(f"\n找到 {len(cache_files)} 个缓存文件")
        
        success_count = 0
        for cache_file in cache_files:
            if test_preprocessed_data(str(cache_file)):
                success_count += 1
            print("\n" + "=" * 50)
        
        print(f"\n📊 测试结果: {success_count}/{len(cache_files)} 通过")

if __name__ == "__main__":
    main()