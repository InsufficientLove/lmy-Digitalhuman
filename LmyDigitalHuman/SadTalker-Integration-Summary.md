# SadTalker 集成总结

## 环境配置

### 1. 统一的依赖环境
- **Python 版本**: 3.8（与 SadTalker 官方一致）
- **PyTorch 版本**: 1.12.1+cu113（官方推荐）
- **CUDA 版本**: 11.3（最佳兼容性）

### 2. 核心依赖版本（根据您提供的 requirements）
```
numpy==1.23.4
face_alignment==1.3.5
imageio==2.19.3
imageio-ffmpeg==0.4.7
librosa==0.9.2
numba
resampy==0.3.1
pydub==0.25.1
scipy==1.10.1
kornia==0.6.8
tqdm
yacs==0.1.8
pyyaml
joblib==1.1.0
scikit-image==0.19.3
basicsr==1.4.2
facexlib==0.3.0
gradio
gfpgan
av
safetensors
```

### 3. 集成方案
- 所有组件（SadTalker、Edge-TTS、Whisper）都在**同一个虚拟环境**中
- 避免了版本冲突和环境切换问题
- Docker 镜像包含完整环境，开箱即用

## 安装步骤

### 本地安装
1. 安装 CUDA 11.3
2. 运行 `setup-python-env.bat`
3. 下载 SadTalker 模型（运行 `download-sadtalker-models.sh` 或手动下载）

### Docker 部署
```bash
# 开发环境
docker-compose up lmy-digital-human-dev

# 生产环境
docker-compose up -d lmy-digital-human
```

## 配置说明

### appsettings.json 中的 SadTalker 配置
```json
{
  "SadTalker": {
    "Path": "F:/AI/SadTalker",                    // SadTalker 根目录
    "PythonPath": "F:/AI/SadTalker/venv/Scripts/python.exe",  // Python 解释器路径
    "EnableGPU": true,                             // 启用 GPU 加速
    "CheckpointsPath": "checkpoints",              // 模型文件路径
    "GfpganPath": "gfpgan",                        // GFPGAN 模型路径
    "Enhancer": "gfpgan",                          // 增强器类型
    "PreProcess": "crop",                          // 预处理方式
    "FaceModel": "256"                             // 人脸模型分辨率
  }
}
```

## 模型文件

### 必需的模型文件
1. **SadTalker 核心模型**
   - `checkpoints/SadTalker_V0.0.2_256.safetensors`
   - `checkpoints/SadTalker_V0.0.2_512.safetensors`
   - `checkpoints/mapping_00229-model.pth.tar`
   - `checkpoints/mapping_00109-model.pth.tar`

2. **GFPGAN 增强模型**
   - `gfpgan/weights/GFPGANv1.4.pth`
   - `gfpgan/weights/detection_Resnet50_Final.pth`
   - `gfpgan/weights/parsing_parsenet.pth`

### 下载地址
- 百度网盘：https://pan.baidu.com/s/1tb0pBh2vZO5YD5vRNe_ZXg （提取码：sadt）
- Google Drive：https://drive.google.com/drive/folders/1Wd88VDoLhVzYsQ30_qDVluQHjqQHrmYKr

## 注意事项

1. **CUDA 版本兼容性**
   - 必须使用 CUDA 11.3，其他版本可能导致依赖冲突
   - 如果本地已有其他 CUDA 版本，建议使用 Docker

2. **Python 环境**
   - 强烈建议使用虚拟环境
   - 不要混用不同 Python 版本

3. **内存和显存要求**
   - 建议至少 8GB 显存
   - 系统内存至少 16GB

4. **性能优化**
   - 启用 GPU 加速（UseGPU: true）
   - 适当调整批处理大小（BatchSize）
   - 使用合适的人脸模型分辨率（256 或 512）

## 故障排除

1. **CUDA 相关错误**
   - 确认 CUDA 11.3 正确安装
   - 检查环境变量设置
   - 使用 `nvidia-smi` 验证 GPU 可用

2. **依赖版本冲突**
   - 严格按照提供的版本安装
   - 使用虚拟环境隔离
   - 考虑使用 Docker

3. **模型加载失败**
   - 确认模型文件完整下载
   - 检查文件路径配置
   - 验证文件权限

## 未来优化建议

1. 考虑将模型文件打包到 Docker 镜像中
2. 实现模型文件的自动下载和验证
3. 添加更多的错误处理和日志记录
4. 支持多 GPU 并行处理