#!/usr/bin/env python3
import pickle
import numpy as np

# 检查xiaoha模板缓存
cache_file = "/opt/musetalk/template_cache/xiaoha/xiaoha_preprocessed.pkl"

try:
    with open(cache_file, 'rb') as f:
        data = pickle.load(f)
    
    print("缓存内容：")
    for key in data.keys():
        if isinstance(data[key], np.ndarray):
            print(f"  {key}: shape={data[key].shape}, dtype={data[key].dtype}")
        elif isinstance(data[key], list):
            print(f"  {key}: list长度={len(data[key])}")
            if len(data[key]) > 0:
                item = data[key][0]
                if isinstance(item, np.ndarray):
                    print(f"    第一项: shape={item.shape}")
                else:
                    print(f"    第一项: {item}")
        else:
            print(f"  {key}: {type(data[key])}")
    
    # 检查bbox
    if 'coord_list' in data:
        print("\nBBox信息：")
        for i, bbox in enumerate(data['coord_list'][:3]):
            print(f"  帧{i}: {bbox}")
    
    # 检查原图尺寸
    if 'frame_list' in data and len(data['frame_list']) > 0:
        print(f"\n原图尺寸: {data['frame_list'][0].shape}")
        
except Exception as e:
    print(f"错误: {e}")