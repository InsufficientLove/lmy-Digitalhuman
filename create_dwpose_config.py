#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建缺失的DWPose配置文件
用于修复MuseTalk的DWPose依赖问题
"""

import os
from pathlib import Path

def create_rtmpose_config():
    """创建RTMPose配置文件"""
    config_content = '''# RTMPose-l Configuration for DWPose
# Based on RTMPose: Real-Time Multi-Person Pose Estimation

model = dict(
    type='TopdownPoseEstimator',
    data_preprocessor=dict(
        type='PoseDataPreprocessor',
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375],
        bgr_to_rgb=True),
    backbone=dict(
        type='CSPNeXt',
        arch='P5',
        expand_ratio=0.5,
        deepen_factor=1.0,
        widen_factor=1.0,
        channel_attention=True,
        norm_cfg=dict(type='SyncBN'),
        act_cfg=dict(type='SiLU', inplace=True)),
    neck=dict(
        type='CSPNeXtPAFPN',
        in_channels=[256, 512, 1024],
        out_channels=256,
        num_csp_blocks=2,
        expand_ratio=0.5,
        norm_cfg=dict(type='SyncBN'),
        act_cfg=dict(type='SiLU', inplace=True)),
    head=dict(
        type='RTMCCHead',
        in_channels=256,
        out_channels=133,  # 133 keypoints for wholebody
        input_size=(384, 288),
        in_featuremap_size=(12, 9),
        simcc_split_ratio=2.0,
        final_layer_kernel_size=7,
        gau_cfg=dict(
            hidden_dims=256,
            s=128,
            expansion_factor=2,
            dropout_rate=0.,
            drop_path=0.,
            act_fn='SiLU',
            use_rel_bias=False,
            pos_enc=False)),
    test_cfg=dict(
        flip_test=True,
        flip_mode='heatmap',
        shift_heatmap=False))

# dataset settings
dataset_info = dict(
    dataset_name='coco_wholebody',
    paper_info=dict(
        author='Jin, Sheng and Xu, Lumin and Xu, Jin and '
        'Wang, Can and Liu, Wentao and Qian, Chen and Ouyang, Wanli and Luo, Ping',
        title='Whole-Body Human Pose Estimation in the Wild',
        container='Proceedings of the European '
        'Conference on Computer Vision (ECCV)',
        year='2020',
        homepage='https://github.com/jin-s13/COCO-WholeBody/',
    ),
    keypoint_info={
        'num_keypoints': 133,
        'keypoint_names': [
            'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
            'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
        ] + [f'face_{i}' for i in range(68)] + 
           [f'lefthand_{i}' for i in range(21)] + 
           [f'righthand_{i}' for i in range(21)] +
           [f'foot_{i}' for i in range(6)],
        'joint_weights': [1.] * 133,
        'sigmas': []
    })

train_cfg = dict(max_epochs=270, val_interval=10)
randomness = dict(seed=21)
'''
    return config_content

def create_directories_and_files():
    """创建必要的目录和文件"""
    print("创建MuseTalk DWPose配置文件...")
    
    # 假设在项目根目录运行
    base_dir = Path("MuseTalk")
    if not base_dir.exists():
        print(f"错误: {base_dir} 目录不存在!")
        print("请确保在包含MuseTalk目录的位置运行此脚本")
        return False
    
    # 创建必要的目录
    dirs_to_create = [
        "musetalk/utils/dwpose",
        "configs/dwpose"
    ]
    
    for dir_path in dirs_to_create:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {full_path}")
    
    # 创建配置文件
    config_file = base_dir / "musetalk/utils/dwpose/rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py"
    config_content = create_rtmpose_config()
    
    config_file.write_text(config_content, encoding='utf-8')
    print(f"✅ 创建配置文件: {config_file}")
    
    # 创建__init__.py文件
    init_files = [
        base_dir / "musetalk/__init__.py",
        base_dir / "musetalk/utils/__init__.py", 
        base_dir / "musetalk/utils/dwpose/__init__.py"
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.write_text('# MuseTalk package\n', encoding='utf-8')
            print(f"✅ 创建__init__.py: {init_file}")
    
    print("\n🎉 DWPose配置文件创建完成!")
    print("\n建议:")
    print("1. 如果问题仍然存在，请考虑下载完整的官方MuseTalk仓库")
    print("2. 检查虚拟环境中是否安装了所有必要的依赖")
    
    return True

if __name__ == "__main__":
    success = create_directories_and_files()
    if success:
        print("\n✅ 配置文件创建成功!")
    else:
        print("\n❌ 配置文件创建失败!")
    
    input("\n按回车键退出...")