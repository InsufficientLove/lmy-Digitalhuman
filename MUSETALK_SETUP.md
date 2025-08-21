# MuseTalk 依赖配置说明

## 问题描述
项目依赖MuseTalk的核心代码，但该代码不在当前仓库中。需要单独获取并正确配置。

## 解决方案

### 方案1：克隆MuseTalk仓库（推荐）
```bash
# 在项目根目录执行
git clone https://github.com/TMElyraedge/MuseTalk.git

# 或者如果有私有仓库
git clone [你的MuseTalk仓库地址] MuseTalk
```

### 方案2：使用子模块
```bash
# 添加为git子模块
git submodule add https://github.com/TMElyraedge/MuseTalk.git MuseTalk
git submodule update --init --recursive
```

### 方案3：创建最小化的MuseTalk结构
如果只需要部分功能，可以创建最小化的目录结构：

```
MuseTalk/
├── musetalk/
│   ├── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── face_parsing.py
│       ├── utils.py
│       ├── preprocessing.py
│       ├── blending.py
│       └── audio_processor.py
└── models/  # 模型文件目录
```

## Docker挂载配置
docker-compose.yml已正确配置了挂载：
```yaml
volumes:
  - ./MuseTalk:/opt/musetalk/repo/MuseTalk
```

## 模型文件
确保在宿主机的 `/opt/musetalk/models` 目录下有必要的模型文件：
- VAE模型
- UNet模型
- 音频处理模型
- 其他预训练模型

## 验证
容器启动后，可以通过以下命令验证：
```bash
docker exec -it musetalk-python python3 -c "from musetalk.utils.utils import datagen; print('MuseTalk导入成功')"
```