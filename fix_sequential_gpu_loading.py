#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import shutil
from datetime import datetime

def backup_original_file(file_path):
    """备份原始文件"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ 原文件已备份到: {backup_path}")
    return backup_path

def fix_ultra_fast_service():
    """修复Ultra Fast Service的并行加载问题"""
    print("MuseTalk Ultra Fast Service 并行加载修复工具")
    print("=" * 50)
    
    script_dir = Path(__file__).parent
    service_file = script_dir / "MuseTalkEngine" / "ultra_fast_realtime_inference_v2.py"
    
    if not service_file.exists():
        print(f"❌ 服务文件不存在: {service_file}")
        return False
    
    print(f"✅ 找到服务文件: {service_file}")
    
    # 备份原文件
    backup_path = backup_original_file(service_file)
    
    try:
        # 读取原文件内容
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经修复过
        if "# SEQUENTIAL_LOADING_FIXED" in content:
            print("✅ 文件已经修复过，无需重复修复")
            return True
        
        # 替换并行初始化为顺序初始化
        old_parallel_code = '''            # 真正的并行初始化 - 允许部分GPU失败
            print(f"开始并行初始化{self.gpu_count}个GPU...")
            successful_gpus = []
            with ThreadPoolExecutor(max_workers=self.gpu_count) as executor:
                futures = {executor.submit(init_gpu_model, i): i for i in range(self.gpu_count)}
                
                for future in as_completed(futures, timeout=300):  # 5分钟超时
                    gpu_id = futures[future]
                    try:
                        result = future.result()
                        if result is not None:
                            successful_gpus.append(gpu_id)
                            print(f"GPU{gpu_id} 就绪 ({len(successful_gpus)}/{self.gpu_count})")
                        else:
                            print(f"GPU{gpu_id} 初始化失败，跳过")
                    except Exception as e:
                        print(f"GPU{gpu_id} 初始化异常: {e}")'''
        
        new_sequential_code = '''            # SEQUENTIAL_LOADING_FIXED: 顺序初始化避免并发冲突
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
                            print(f"❌ GPU{i} 重试异常: {retry_e}")'''
        
        # 执行替换
        if old_parallel_code in content:
            content = content.replace(old_parallel_code, new_sequential_code)
            print("✅ 已将并行初始化替换为顺序初始化")
        else:
            print("⚠️ 未找到预期的并行初始化代码，尝试其他替换方式...")
            
            # 尝试替换关键部分
            if "with ThreadPoolExecutor(max_workers=self.gpu_count) as executor:" in content:
                # 找到并替换ThreadPoolExecutor部分
                lines = content.split('\n')
                new_lines = []
                in_executor_block = False
                indent_level = 0
                
                for line in lines:
                    if "with ThreadPoolExecutor(max_workers=self.gpu_count) as executor:" in line:
                        # 替换为顺序初始化
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * indent + '# SEQUENTIAL_LOADING_FIXED: 改为顺序初始化')
                        new_lines.append(' ' * indent + 'for i in range(self.gpu_count):')
                        new_lines.append(' ' * indent + '    print(f"正在初始化GPU {i}/{self.gpu_count}...")')
                        new_lines.append(' ' * indent + '    try:')
                        new_lines.append(' ' * indent + '        torch.cuda.set_device(i)')
                        new_lines.append(' ' * indent + '        torch.cuda.empty_cache()')
                        new_lines.append(' ' * indent + '        result = init_gpu_model(i)')
                        new_lines.append(' ' * indent + '        if result is not None:')
                        new_lines.append(' ' * indent + '            successful_gpus.append(i)')
                        new_lines.append(' ' * indent + '            print(f"✅ GPU{i} 就绪 ({len(successful_gpus)}/{self.gpu_count})")')
                        new_lines.append(' ' * indent + '        else:')
                        new_lines.append(' ' * indent + '            print(f"❌ GPU{i} 初始化失败，跳过")')
                        new_lines.append(' ' * indent + '    except Exception as e:')
                        new_lines.append(' ' * indent + '        print(f"❌ GPU{i} 初始化异常: {e}")')
                        new_lines.append(' ' * indent + '        if "meta tensor" in str(e):')
                        new_lines.append(' ' * indent + '            print(f"检测到meta tensor错误，清理内存后重试...")')
                        new_lines.append(' ' * indent + '            torch.cuda.empty_cache()')
                        new_lines.append(' ' * indent + '            import gc; gc.collect()')
                        in_executor_block = True
                        indent_level = indent
                        continue
                    
                    if in_executor_block:
                        # 跳过executor块内的内容
                        current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 4
                        if current_indent <= indent_level and line.strip():
                            in_executor_block = False
                            new_lines.append(line)
                        # 继续跳过executor块内容
                    else:
                        new_lines.append(line)
                
                content = '\n'.join(new_lines)
                print("✅ 已使用备用方法替换并行初始化")
        
        # 添加导入必要模块
        if "import gc" not in content:
            # 在其他import语句附近添加gc导入
            content = content.replace("import warnings", "import warnings\nimport gc")
        
        # 写入修复后的文件
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 文件修复完成")
        print(f"备份文件: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        # 恢复备份
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, service_file)
            print("已恢复原文件")
        return False

def create_single_gpu_config():
    """创建单GPU配置文件"""
    print("\n=== 创建单GPU配置 ===")
    
    script_dir = Path(__file__).parent
    config_file = script_dir / "single_gpu_config.py"
    
    config_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单GPU配置 - 如果4GPU并行仍有问题，可以使用此配置
"""

import os
import sys

def modify_for_single_gpu():
    """修改为单GPU配置"""
    # 设置环境变量，只使用第一个GPU
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    
    print("已设置为单GPU模式 (GPU 0)")
    print("重启服务后将只使用第一个GPU")

if __name__ == "__main__":
    modify_for_single_gpu()
'''
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ 单GPU配置已创建: {config_file}")
    print("如果4GPU顺序加载仍有问题，可以运行此脚本切换到单GPU模式")

def main():
    print("开始修复MuseTalk GPU并行加载问题...")
    
    if fix_ultra_fast_service():
        print("\n🎉 修复完成！")
        print("\n建议步骤:")
        print("1. 重新启动MuseTalk服务")
        print("2. 观察4GPU是否能正常顺序初始化")
        print("3. 如果仍有问题，可以尝试单GPU模式")
        
        # 创建单GPU配置作为备选方案
        create_single_gpu_config()
        
    else:
        print("\n❌ 修复失败")
        print("请检查错误信息或手动修改配置文件")
    
    print("\n按任意键退出...")
    try:
        input()
    except:
        pass

if __name__ == "__main__":
    main()