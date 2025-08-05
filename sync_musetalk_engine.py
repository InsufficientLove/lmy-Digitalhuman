#!/usr/bin/env python3
"""
MuseTalk Engine 同步脚本
用于在 MuseTalkEngine 和 MuseTalk 目录之间同步代码文件

使用方法:
python sync_musetalk_engine.py --to-musetalk      # 将 MuseTalkEngine 的文件同步到 MuseTalk
python sync_musetalk_engine.py --from-musetalk    # 将 MuseTalk 的文件同步到 MuseTalkEngine
python sync_musetalk_engine.py --status           # 显示同步状态

作者: Claude Sonnet
版本: 1.0
"""

import os
import shutil
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

class MuseTalkEngineSync:
    """MuseTalk Engine 同步管理器"""
    
    def __init__(self):
        self.workspace_root = Path(__file__).parent
        self.musetalk_dir = self.workspace_root / "MuseTalk"
        self.engine_dir = self.workspace_root / "MuseTalkEngine"
        
        # 需要同步的文件列表
        self.sync_files = [
            "enhanced_musetalk_inference_v4.py",
            "enhanced_musetalk_preprocessing.py", 
            "integrated_musetalk_service.py",
            "ultra_fast_realtime_inference.py",
            "optimized_musetalk_inference_v3.py",
            "start_persistent_service.py"
        ]
        
        # 确保目录存在
        self.engine_dir.mkdir(exist_ok=True)
    
    def get_file_hash(self, file_path):
        """获取文件的MD5哈希值"""
        if not file_path.exists():
            return None
        
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def compare_files(self):
        """比较两个目录中的文件"""
        comparison = {}
        
        for filename in self.sync_files:
            engine_file = self.engine_dir / filename
            musetalk_file = self.musetalk_dir / filename
            
            engine_hash = self.get_file_hash(engine_file)
            musetalk_hash = self.get_file_hash(musetalk_file)
            
            comparison[filename] = {
                'engine_exists': engine_file.exists(),
                'musetalk_exists': musetalk_file.exists(),
                'engine_hash': engine_hash,
                'musetalk_hash': musetalk_hash,
                'same': engine_hash == musetalk_hash if engine_hash and musetalk_hash else False
            }
        
        return comparison
    
    def sync_to_musetalk(self):
        """将 MuseTalkEngine 的文件同步到 MuseTalk 目录"""
        print("🔄 开始同步 MuseTalkEngine -> MuseTalk")
        
        if not self.musetalk_dir.exists():
            print(f"❌ MuseTalk 目录不存在: {self.musetalk_dir}")
            return False
        
        success_count = 0
        
        for filename in self.sync_files:
            engine_file = self.engine_dir / filename
            musetalk_file = self.musetalk_dir / filename
            
            if not engine_file.exists():
                print(f"⚠️  源文件不存在: {engine_file}")
                continue
            
            try:
                # 备份原文件（如果存在）
                if musetalk_file.exists():
                    backup_file = musetalk_file.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    shutil.copy2(musetalk_file, backup_file)
                    print(f"📦 备份原文件: {backup_file.name}")
                
                # 复制文件并修改路径
                self._copy_and_fix_paths(engine_file, musetalk_file, engine_to_musetalk=True)
                print(f"✅ 同步成功: {filename}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 同步失败 {filename}: {e}")
        
        print(f"\n🎉 同步完成: {success_count}/{len(self.sync_files)} 个文件")
        return success_count == len(self.sync_files)
    
    def sync_from_musetalk(self):
        """将 MuseTalk 的文件同步到 MuseTalkEngine 目录"""
        print("🔄 开始同步 MuseTalk -> MuseTalkEngine")
        
        if not self.musetalk_dir.exists():
            print(f"❌ MuseTalk 目录不存在: {self.musetalk_dir}")
            return False
        
        success_count = 0
        
        for filename in self.sync_files:
            musetalk_file = self.musetalk_dir / filename
            engine_file = self.engine_dir / filename
            
            if not musetalk_file.exists():
                print(f"⚠️  源文件不存在: {musetalk_file}")
                continue
            
            try:
                # 备份原文件（如果存在）
                if engine_file.exists():
                    backup_file = engine_file.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    shutil.copy2(engine_file, backup_file)
                    print(f"📦 备份原文件: {backup_file.name}")
                
                # 复制文件并修改路径
                self._copy_and_fix_paths(musetalk_file, engine_file, engine_to_musetalk=False)
                print(f"✅ 同步成功: {filename}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 同步失败 {filename}: {e}")
        
        print(f"\n🎉 同步完成: {success_count}/{len(self.sync_files)} 个文件")
        return success_count == len(self.sync_files)
    
    def _copy_and_fix_paths(self, source_file, target_file, engine_to_musetalk=True):
        """复制文件并修正路径引用"""
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if engine_to_musetalk:
            # MuseTalkEngine -> MuseTalk: 将 ../MuseTalk/ 路径改为相对路径
            content = content.replace('../MuseTalk/models/musetalk/', 'models/musetalk/')
            content = content.replace('../MuseTalk/models/whisper/', 'models/whisper/')
        else:
            # MuseTalk -> MuseTalkEngine: 将相对路径改为 ../MuseTalk/ 路径
            content = content.replace('models/musetalk/', '../MuseTalk/models/musetalk/')
            content = content.replace('models/whisper/', '../MuseTalk/models/whisper/')
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def show_status(self):
        """显示同步状态"""
        print("📊 MuseTalk Engine 同步状态")
        print("=" * 60)
        
        comparison = self.compare_files()
        
        for filename, info in comparison.items():
            print(f"\n📄 {filename}")
            print(f"   MuseTalkEngine: {'✅ 存在' if info['engine_exists'] else '❌ 不存在'}")
            print(f"   MuseTalk:       {'✅ 存在' if info['musetalk_exists'] else '❌ 不存在'}")
            
            if info['engine_exists'] and info['musetalk_exists']:
                if info['same']:
                    print(f"   状态:           🟢 文件相同")
                else:
                    print(f"   状态:           🟡 文件不同")
            elif info['engine_exists'] or info['musetalk_exists']:
                print(f"   状态:           🔴 仅一侧存在")
            else:
                print(f"   状态:           ⚫ 两侧都不存在")
        
        print("\n" + "=" * 60)
        print("💡 使用说明:")
        print("   --to-musetalk    将 MuseTalkEngine 同步到 MuseTalk")
        print("   --from-musetalk  将 MuseTalk 同步到 MuseTalkEngine")
        print("   --status         显示当前状态")


def main():
    parser = argparse.ArgumentParser(description="MuseTalk Engine 同步工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--to-musetalk", action="store_true", help="同步到 MuseTalk 目录")
    group.add_argument("--from-musetalk", action="store_true", help="从 MuseTalk 目录同步")
    group.add_argument("--status", action="store_true", help="显示同步状态")
    
    args = parser.parse_args()
    
    sync_manager = MuseTalkEngineSync()
    
    if args.to_musetalk:
        sync_manager.sync_to_musetalk()
    elif args.from_musetalk:
        sync_manager.sync_from_musetalk()
    elif args.status:
        sync_manager.show_status()


if __name__ == "__main__":
    main()