#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板管理器 - 处理模板预处理、删除、验证
"""

import os
import sys
import json
import shutil
import pickle
import argparse
from pathlib import Path

# 添加MuseTalk路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MuseTalk'))

# 获取统一的模板缓存目录
DEFAULT_TEMPLATE_CACHE_DIR = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')

def preprocess_template(template_id, image_path, output_dir=None):
    """预处理模板，生成缓存文件"""
    try:
        print(f"🔄 开始预处理模板: {template_id}")
        
        # 导入预处理模块
        from optimized_preprocessing_v2 import OptimizedPreprocessor
        
        # 使用默认目录如果未指定
        if output_dir is None:
            output_dir = DEFAULT_TEMPLATE_CACHE_DIR
            
        # 创建输出目录
        template_dir = os.path.join(output_dir, template_id)
        os.makedirs(template_dir, exist_ok=True)
        
        # 执行预处理
        cache_file = os.path.join(template_dir, f"{template_id}_preprocessed.pkl")
        
        # 如果已存在，先备份
        if os.path.exists(cache_file):
            backup_file = cache_file + ".bak"
            shutil.copy2(cache_file, backup_file)
            print(f"📦 备份现有缓存: {backup_file}")
        
        # 创建预处理器实例并调用预处理
        preprocessor = OptimizedPreprocessor()
        preprocessor.initialize_models()  # 初始化模型
        success = preprocessor.preprocess_template_ultra_fast(
            template_path=image_path,
            output_dir=output_dir,
            template_id=template_id
        )
        
        if success:
            print(f"✅ 预处理成功: {cache_file}")
            # 生成元数据
            metadata_file = os.path.join(template_dir, f"{template_id}_metadata.json")
            metadata = {
                "template_id": template_id,
                "image_path": image_path,
                "cache_file": cache_file,
                "created_at": str(Path(cache_file).stat().st_mtime)
            }
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"📝 元数据已保存: {metadata_file}")
            return True
        else:
            print(f"❌ 预处理失败")
            return False
            
    except Exception as e:
        print(f"❌ 预处理异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_template(template_id, templates_dir=None):
    """删除模板及其所有缓存文件"""
    try:
        print(f"🗑️ 删除模板: {template_id}")
        
        # 使用默认目录如果未指定
        if templates_dir is None:
            templates_dir = DEFAULT_TEMPLATE_CACHE_DIR
            
        template_dir = os.path.join(templates_dir, template_id)
        
        if not os.path.exists(template_dir):
            print(f"⚠️ 模板目录不存在: {template_dir}")
            return False
        
        # 列出将要删除的文件
        files_to_delete = []
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                files_to_delete.append(os.path.join(root, file))
        
        print(f"📋 将删除 {len(files_to_delete)} 个文件:")
        for file in files_to_delete:
            print(f"  - {os.path.basename(file)}")
        
        # 删除整个目录
        shutil.rmtree(template_dir)
        print(f"✅ 模板已删除: {template_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        return False

def verify_template(template_id, templates_dir=None):
    """验证模板缓存是否完整"""
    try:
        print(f"🔍 验证模板: {template_id}")
        
        # 使用默认目录如果未指定
        if templates_dir is None:
            templates_dir = DEFAULT_TEMPLATE_CACHE_DIR
            
        template_dir = os.path.join(templates_dir, template_id)
        cache_file = os.path.join(template_dir, f"{template_id}_preprocessed.pkl")
        
        if not os.path.exists(template_dir):
            print(f"❌ 模板目录不存在: {template_dir}")
            return False
        
        if not os.path.exists(cache_file):
            print(f"❌ 缓存文件不存在: {cache_file}")
            return False
        
        # 尝试加载缓存
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 检查必要的键
            required_keys = [
                'coord_list_cycle',
                'frame_list_cycle', 
                'input_latent_list_cycle',
                'mask_coords_list_cycle',
                'mask_list_cycle'
            ]
            
            missing_keys = []
            for key in required_keys:
                if key not in cache_data:
                    missing_keys.append(key)
            
            if missing_keys:
                print(f"❌ 缓存缺少必要数据: {missing_keys}")
                return False
            
            print(f"✅ 模板验证通过")
            print(f"  - 缓存文件: {cache_file}")
            print(f"  - 文件大小: {os.path.getsize(cache_file) / 1024 / 1024:.2f} MB")
            print(f"  - 包含帧数: {len(cache_data.get('frame_list_cycle', []))}")
            
            return True
            
        except Exception as e:
            print(f"❌ 缓存加载失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 验证异常: {e}")
        return False

def list_templates(templates_dir=None):
    """列出所有模板"""
    try:
        # 使用默认目录如果未指定
        if templates_dir is None:
            templates_dir = DEFAULT_TEMPLATE_CACHE_DIR
            
        print(f"📋 模板列表 ({templates_dir}):")
        
        if not os.path.exists(templates_dir):
            print(f"⚠️ 模板目录不存在")
            return []
        
        templates = []
        for item in os.listdir(templates_dir):
            item_path = os.path.join(templates_dir, item)
            if os.path.isdir(item_path):
                cache_file = os.path.join(item_path, f"{item}_preprocessed.pkl")
                if os.path.exists(cache_file):
                    size_mb = os.path.getsize(cache_file) / 1024 / 1024
                    templates.append({
                        "id": item,
                        "path": item_path,
                        "cache_file": cache_file,
                        "size_mb": size_mb
                    })
                    print(f"  ✅ {item} ({size_mb:.2f} MB)")
                else:
                    print(f"  ⚠️ {item} (未预处理)")
        
        return templates
        
    except Exception as e:
        print(f"❌ 列出模板失败: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='模板管理器')
    parser.add_argument('action', choices=['preprocess', 'delete', 'verify', 'list'],
                       help='操作类型')
    parser.add_argument('--template_id', type=str, help='模板ID')
    parser.add_argument('--image_path', type=str, help='模板图片路径')
    parser.add_argument('--output_dir', type=str, 
                       default=None,
                       help='输出目录（默认使用环境变量MUSE_TEMPLATE_CACHE_DIR）')
    
    args = parser.parse_args()
    
    if args.action == 'preprocess':
        if not args.template_id or not args.image_path:
            print("❌ 预处理需要 --template_id 和 --image_path")
            sys.exit(1)
        success = preprocess_template(args.template_id, args.image_path, args.output_dir)
        sys.exit(0 if success else 1)
        
    elif args.action == 'delete':
        if not args.template_id:
            print("❌ 删除需要 --template_id")
            sys.exit(1)
        success = delete_template(args.template_id, args.output_dir)
        sys.exit(0 if success else 1)
        
    elif args.action == 'verify':
        if not args.template_id:
            print("❌ 验证需要 --template_id")
            sys.exit(1)
        success = verify_template(args.template_id, args.output_dir)
        sys.exit(0 if success else 1)
        
    elif args.action == 'list':
        templates = list_templates(args.output_dir)
        print(f"共 {len(templates)} 个模板")
        sys.exit(0)

if __name__ == "__main__":
    main()