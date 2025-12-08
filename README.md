# LMY Digital Human - 实时数字人系统

高性能 AI 数字人实时推理引擎 | 基于 MuseTalk + FastAPI + PyTorch

## 快速开始

```bash
# 1. 安装依赖
cd /opt/musetalk/repo
bash install_dependencies.sh

# 2. 验证环境
python3 MuseTalkEngine/check_env.py

# 3. 启动服务
cd MuseTalkEngine
bash start_realtime_service.sh
```

## 项目结构

```
/opt/musetalk/repo/
├── install_dependencies.sh          # 依赖安装
├── quick_check.sh                   # 快速检查
└── MuseTalkEngine/
    ├── main_realtime.py             # 实时推理服务
    ├── preprocess_assets.py         # 资产预处理
    ├── config_paths.py              # 路径配置
    ├── check_env.py                 # 环境验证
    ├── auto_detect_models.py        # 模型检测
    └── start_realtime_service.sh    # 服务启动
```

## 核心特性

- **FP16 混合精度**：显存占用减少 50%，速度提升 2-3 倍
- **torch.compile JIT**：模型推理加速 30-40%
- **GPU 推理池**：多 GPU 并行处理
- **MJPEG 流式输出**：低延迟 (<150ms) 视频流
- **环境自检**：自动检测 Python/CUDA/模型/依赖
- **国内镜像加速**：pip 包下载速度提升 10 倍

## 技术栈

- PyTorch 2.1.2 + CUDA 12.1
- FastAPI 0.104.1
- OpenCV 4.8.1
- Transformers 4.35.2
- Diffusers 0.24.0

## API 使用

```bash
# 健康检查
curl http://localhost:8080/health

# 实时推理
curl -X POST http://localhost:8080/stream \
  -F "audio=@test.wav" \
  -F "avatar_id=default"
```

## 文档

- [快速入门](MuseTalkEngine/QUICKSTART.md)
- [API 文档](MuseTalkEngine/README_REALTIME.md)
- [部署指南](服务器部署说明.md)

## License

Apache 2.0
