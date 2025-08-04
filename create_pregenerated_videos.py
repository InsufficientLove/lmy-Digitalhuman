#!/usr/bin/env python3
"""
🚀 MuseTalk预生成视频库创建工具
解决实时通讯性能瓶颈的关键方案

用法:
python create_pregenerated_videos.py --avatar_dir ./wwwroot/templates --output_dir ./wwwroot/videos/pregenerated
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def create_sample_audios():
    """创建常用的示例音频文件"""
    sample_texts = [
        "你好，我是数字人助手。",
        "很高兴为您服务。", 
        "请问有什么可以帮助您的吗？",
        "好的，我明白了。",
        "让我来为您解答这个问题。",
        "感谢您的提问。",
        "这是一个很好的问题。",
        "我需要思考一下。",
        "根据我的理解。",
        "希望这个回答对您有帮助。"
    ]
    
    audio_dir = Path("temp_sample_audios")
    audio_dir.mkdir(exist_ok=True)
    
    created_audios = []
    
    for i, text in enumerate(sample_texts):
        audio_file = audio_dir / f"sample_{i:02d}.mp3"
        
        # 使用Edge-TTS生成音频
        cmd = [
            "edge-tts",
            "--voice", "zh-CN-XiaoxiaoNeural",
            "--text", text,
            "--write-media", str(audio_file)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            created_audios.append(str(audio_file))
            print(f"✅ 创建音频: {text[:10]}... -> {audio_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 音频创建失败: {text[:10]}... -> {e}")
    
    return created_audios

def generate_pregenerated_videos(avatar_dir, output_dir, musetalk_dir):
    """为每个avatar生成预生成视频库"""
    
    avatar_dir = Path(avatar_dir)
    output_dir = Path(output_dir)
    musetalk_dir = Path(musetalk_dir)
    
    # 查找所有avatar图片
    avatar_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        avatar_files.extend(avatar_dir.glob(ext))
    
    if not avatar_files:
        print(f"❌ 在 {avatar_dir} 中未找到avatar图片")
        return
    
    # 创建示例音频
    print("🎵 创建示例音频文件...")
    sample_audios = create_sample_audios()
    
    if not sample_audios:
        print("❌ 无法创建示例音频文件")
        return
    
    # 为每个avatar生成视频
    for avatar_file in avatar_files:
        avatar_name = avatar_file.stem
        avatar_output_dir = output_dir / avatar_name
        avatar_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🎬 为avatar '{avatar_name}' 生成预生成视频库...")
        
        for i, audio_file in enumerate(sample_audios):
            output_video = avatar_output_dir / f"pregenerated_{i:02d}.mp4"
            
            if output_video.exists():
                print(f"⏭️  跳过已存在的视频: {output_video.name}")
                continue
            
            # 创建MuseTalk推理配置
            config_content = f"""task_0:
 video_path: "{avatar_file}"
 audio_path: "{audio_file}"
 bbox_shift: 0
"""
            
            config_file = Path("temp_config.yaml")
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # 执行MuseTalk推理
            cmd = [
                sys.executable, "-m", "scripts.inference",
                "--inference_config", str(config_file),
                "--result_dir", str(avatar_output_dir.parent),
                "--output_vid_name", output_video.name,
                "--use_float16",
                "--batch_size", "8",
                "--fps", "25",
                "--version", "v1",
                "--use_saved_coord"
            ]
            
            try:
                print(f"🚀 生成视频: {output_video.name}")
                result = subprocess.run(
                    cmd, 
                    cwd=musetalk_dir,
                    check=True, 
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                # 移动生成的视频到正确位置
                temp_video_dir = avatar_output_dir.parent / "v1"
                if temp_video_dir.exists():
                    for temp_video in temp_video_dir.glob("*.mp4"):
                        temp_video.rename(output_video)
                        print(f"✅ 视频生成完成: {output_video.name}")
                        break
                
            except subprocess.TimeoutExpired:
                print(f"⏰ 视频生成超时: {output_video.name}")
            except subprocess.CalledProcessError as e:
                print(f"❌ 视频生成失败: {output_video.name}")
                print(f"错误输出: {e.stderr}")
            finally:
                # 清理临时文件
                if config_file.exists():
                    config_file.unlink()
    
    # 清理临时音频文件
    print("\n🧹 清理临时文件...")
    for audio_file in sample_audios:
        try:
            os.unlink(audio_file)
        except:
            pass
    
    try:
        os.rmdir("temp_sample_audios")
    except:
        pass
    
    print(f"\n🎉 预生成视频库创建完成！")
    print(f"📁 输出目录: {output_dir}")
    print(f"💡 现在您的数字人可以实现真正的实时响应了！")

def main():
    parser = argparse.ArgumentParser(description="创建MuseTalk预生成视频库")
    parser.add_argument("--avatar_dir", required=True, help="Avatar图片目录")
    parser.add_argument("--output_dir", required=True, help="预生成视频输出目录")
    parser.add_argument("--musetalk_dir", default="../MuseTalk", help="MuseTalk代码目录")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.avatar_dir):
        print(f"❌ Avatar目录不存在: {args.avatar_dir}")
        return
    
    if not os.path.exists(args.musetalk_dir):
        print(f"❌ MuseTalk目录不存在: {args.musetalk_dir}")
        return
    
    generate_pregenerated_videos(args.avatar_dir, args.output_dir, args.musetalk_dir)

if __name__ == "__main__":
    main()