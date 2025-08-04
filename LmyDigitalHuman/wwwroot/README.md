# WWWRoot 目录结构说明

## 📁 目录结构

```
wwwroot/
├── digital-human-test.html    # 数字人系统主测试页面
├── js/                        # JavaScript脚本目录
│   ├── webrtc-realtime.js    # WebRTC实时通信脚本
│   └── improve_video_player.js # 视频播放器增强脚本
├── images/                    # 图片资源目录
│   └── default-avatar.svg    # 默认头像SVG
├── templates/                 # 数字人模板目录
│   ├── sample-female-1.jpg   # 示例女性模板
│   ├── sample-female-2.jpg   # 示例女性模板
│   └── sample-male-1.jpg     # 示例男性模板
├── videos/                    # 生成的视频文件目录
│   └── .gitkeep              # Git保持目录
└── README.md                 # 本说明文件
```

## 🎬 视频播放器增强功能

### improve_video_player.js 功能：
- ✅ **智能文件检测**: 自动检查视频文件是否存在
- ✅ **加载状态指示**: 显示视频生成进度
- ✅ **错误处理**: 友好的错误提示和重试机制
- ✅ **自动播放**: 智能的自动播放处理
- ✅ **样式增强**: 与现有UI完美集成
- ✅ **日志集成**: 使用现有的日志系统

### 使用方法：
脚本会自动初始化，并提供全局函数：
- `window.setVideoSource(videoUrl)` - 设置视频源
- `window.checkVideoExists(videoUrl)` - 检查视频是否存在
- `window.retryVideoLoad()` - 重试加载视频

## 🎭 模板系统

### templates/ 目录：
- 存储数字人模板图片
- 支持 JPG, PNG, WebP 格式
- 建议尺寸：512x512 或更高
- 用于MuseTalk数字人生成

## 📹 视频输出

### videos/ 目录：
- 自动生成的数字人视频存储位置
- 支持Web访问 (`/videos/filename.mp4`)
- 文件命名格式：`video_[guid].mp4`
- 自动清理机制（可配置）

## 🚀 性能优化

### 已实施的优化：
1. **文件检测**: 避免404错误
2. **智能缓存**: 浏览器缓存优化
3. **错误恢复**: 自动重试机制
4. **用户体验**: 加载指示器和进度反馈

## 🔧 维护说明

### 定期清理：
- `videos/` 目录可能需要定期清理旧文件
- 检查模板文件的有效性
- 更新脚本版本时注意兼容性

### 添加新功能：
1. 在 `js/` 目录添加新脚本
2. 在 `digital-human-test.html` 中引用
3. 确保与现有系统集成
4. 更新此README文档