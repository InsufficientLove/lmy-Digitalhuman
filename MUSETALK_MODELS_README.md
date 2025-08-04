# MuseTalk 模型文件下载指南

## 问题说明

当前错误显示缺少以下MuseTalk模型文件：
- `models/musetalk/musetalk.json` - UNet配置文件
- `models/musetalk/pytorch_model.bin` - MuseTalk主模型权重
- `models/sd-vae/diffusion_pytorch_model.safetensors` - SD-VAE模型权重
- `models/sd-vae/config.json` - SD-VAE配置文件

## 自动下载方法

运行提供的下载脚本：

```bash
# 在项目根目录下执行
python download_musetalk_models.py
```

这个脚本会：
1. 创建必要的目录结构
2. 生成配置文件 (`musetalk.json`, `config.json`)
3. 从HuggingFace下载模型权重文件

## 手动下载方法

如果自动下载失败，可以手动下载：

### 1. MuseTalk主模型
访问：https://huggingface.co/TMElyralab/MuseTalk
下载文件：
- `pytorch_model.bin` → 放置到 `models/musetalk/pytorch_model.bin`
- `musetalk.json` → 放置到 `models/musetalk/musetalk.json`

### 2. SD-VAE模型  
访问：https://huggingface.co/stabilityai/sd-vae-ft-mse
下载文件：
- `diffusion_pytorch_model.safetensors` → 放置到 `models/sd-vae/diffusion_pytorch_model.safetensors`
- `config.json` → 放置到 `models/sd-vae/config.json`

## 最终目录结构

下载完成后，目录结构应该如下：

```
models/
├── musetalk/
│   ├── musetalk.json          # UNet配置文件
│   └── pytorch_model.bin      # MuseTalk主模型权重
├── sd-vae/
│   ├── config.json           # SD-VAE配置文件
│   └── diffusion_pytorch_model.safetensors  # SD-VAE模型权重
├── dwpose/
│   └── dw-ll_ucoco_384.pth   # DWPose模型权重 (已存在)
└── whisper/
    └── ...                   # Whisper相关文件 (已存在)
```

## 注意事项

1. **文件大小**: 模型文件较大（几GB），请确保有足够的磁盘空间和网络带宽
2. **网络访问**: 需要能够访问HuggingFace，如有网络问题可使用镜像站点
3. **模型版本**: 确保下载的是兼容版本的模型文件

## 验证安装

下载完成后，可以通过以下方式验证：

```bash
# 检查文件是否存在
ls -la models/musetalk/
ls -la models/sd-vae/

# 检查文件大小 (应该不为0)
du -h models/musetalk/pytorch_model.bin
du -h models/sd-vae/diffusion_pytorch_model.safetensors
```

## 常见问题

**Q: 下载速度很慢怎么办？**
A: 可以使用HuggingFace镜像站点，或者使用支持断点续传的下载工具

**Q: 提示文件损坏？**
A: 重新下载对应的文件，确保下载完整

**Q: 仍然报找不到文件？**
A: 检查文件路径和权限，确保程序有读取权限

## 相关链接

- [MuseTalk官方仓库](https://github.com/TMElyralab/MuseTalk)
- [HuggingFace MuseTalk模型](https://huggingface.co/TMElyralab/MuseTalk)
- [HuggingFace SD-VAE模型](https://huggingface.co/stabilityai/sd-vae-ft-mse)