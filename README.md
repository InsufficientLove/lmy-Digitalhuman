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

## 核心文件

```
├── install_dependencies.sh          # 依赖安装
├── quick_check.sh                   # 快速检查
└── MuseTalkEngine/
    ├── main_realtime.py             # 实时推理服务
    ├── config_paths.py              # 路径配置
    ├── check_env.py                 # 环境验证
    ├── auto_detect_models.py        # 模型检测
    └── start_realtime_service.sh    # 服务启动
```

## 技术栈

- PyTorch 2.1.2 + CUDA 12.1
- FastAPI 0.104.1
- OpenCV 4.8.1
- Transformers 4.35.2

## API

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
