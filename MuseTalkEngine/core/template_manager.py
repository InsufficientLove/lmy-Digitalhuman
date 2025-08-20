#!/usr/bin/env python3
"""
模板管理器 - 通用核心功能
处理模板的预处理、删除、验证等操作
"""

import os
import sys
import json
import shutil
import pickle
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 默认缓存目录 - 从环境变量或使用默认值
DEFAULT_TEMPLATE_CACHE_DIR = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')

def preprocess_template(template_id, image_path, output_dir=None, bbox_shift=0):
    """预处理模板"""
    try:
        from core.preprocessing import OptimizedPreprocessor
        
        if output_dir is None:
            output_dir = DEFAULT_TEMPLATE_CACHE_DIR
        
        print(f"🔄 开始预处理模板: {template_id}")
        
        # 创建预处理器并初始化模型
        preprocessor = OptimizedPreprocessor()
        preprocessor.initialize_models()
        
        # 执行预处理
        success = preprocessor.preprocess_template_ultra_fast(
            template_path=image_path,
            output_dir=output_dir,
            template_id=template_id
        )
        
        if success:
            print(f"✅ 预处理成功: {template_id}")
        else:
            print(f"❌ 预处理失败: {template_id}")
        
        return success
        
    except Exception as e:
        print(f"❌ 预处理异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_template(template_id, templates_dir=None):
    """删除模板及其预处理数据"""
    if templates_dir is None:
        templates_dir = DEFAULT_TEMPLATE_CACHE_DIR
    
    template_dir = os.path.join(templates_dir, template_id)
    
    if os.path.exists(template_dir):
        try:
            shutil.rmtree(template_dir)
            print(f"✅ 已删除模板: {template_id}")
            return True
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            return False
    else:
        print(f"⚠️ 模板不存在: {template_id}")
        return False

def verify_template(template_id, templates_dir=None):
    """验证模板预处理数据是否完整"""
    if templates_dir is None:
        templates_dir = DEFAULT_TEMPLATE_CACHE_DIR
    
    template_dir = os.path.join(templates_dir, template_id)
    
    # 检查必要文件
    required_files = [
        f"{template_id}_preprocessed.pkl",
        f"{template_id}_metadata.json",
        "model_state.pkl"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(template_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 模板 {template_id} 缺少文件: {missing_files}")
        return False
    
    print(f"✅ 模板 {template_id} 验证通过")
    return True

def list_templates(templates_dir=None):
    """列出所有已预处理的模板"""
    if templates_dir is None:
        templates_dir = DEFAULT_TEMPLATE_CACHE_DIR
    
    if not os.path.exists(templates_dir):
        print(f"⚠️ 模板目录不存在: {templates_dir}")
        return []
    
    templates = []
    for item in os.listdir(templates_dir):
        item_path = os.path.join(templates_dir, item)
        if os.path.isdir(item_path):
            # 验证是否为有效模板
            if verify_template(item, templates_dir):
                templates.append(item)
    
    return templates

def main():
    parser = argparse.ArgumentParser(description='模板管理工具')
    parser.add_argument('action', choices=['preprocess', 'delete', 'verify', 'list'],
                        help='要执行的操作')
    parser.add_argument('--template_id', help='模板ID')
    parser.add_argument('--image_path', help='模板图片路径')
    parser.add_argument('--output_dir', help='输出目录', default=DEFAULT_TEMPLATE_CACHE_DIR)
    parser.add_argument('--bbox_shift', type=int, default=0, help='边界框偏移')
    
    args = parser.parse_args()
    
    if args.action == 'preprocess':
        if not args.template_id or not args.image_path:
            print("❌ 预处理需要提供 --template_id 和 --image_path")
            sys.exit(1)
        success = preprocess_template(args.template_id, args.image_path, args.output_dir, args.bbox_shift)
        sys.exit(0 if success else 1)
    
    elif args.action == 'delete':
        if not args.template_id:
            print("❌ 删除需要提供 --template_id")
            sys.exit(1)
        success = delete_template(args.template_id, args.output_dir)
        sys.exit(0 if success else 1)
    
    elif args.action == 'verify':
        if not args.template_id:
            print("❌ 验证需要提供 --template_id")
            sys.exit(1)
        success = verify_template(args.template_id, args.output_dir)
        sys.exit(0 if success else 1)
    
    elif args.action == 'list':
        templates = list_templates(args.output_dir)
        print(f"📋 找到 {len(templates)} 个模板:")
        for t in templates:
            print(f"  - {t}")

if __name__ == "__main__":
    main()