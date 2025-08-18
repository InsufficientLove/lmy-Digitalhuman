# Whisper 模型设置指南

## 模型下载

LmyDigitalHuman 使用 Whisper 模型进行语音识别。您需要手动下载模型文件并放置到正确的位置。

### 1. 创建模型目录

在宿主机上创建 whisper 模型目录：

```bash
sudo mkdir -p /opt/musetalk/models/whisper
```

### 2. 下载模型文件

根据您在 `appsettings.json` 中配置的 `ModelSize`，下载对应的模型文件：

| 模型大小 | 文件名 | 下载地址 | 文件大小 |
|---------|--------|----------|----------|
| Tiny | ggml-tiny.bin | https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin | ~39 MB |
| Base | ggml-base.bin | https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin | ~142 MB |
| Small | ggml-small.bin | https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin | ~466 MB |
| Medium | ggml-medium.bin | https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin | ~1.5 GB |
| Large | ggml-large-v3.bin | https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin | ~3.1 GB |

### 3. 下载命令示例

使用 wget 下载 Large 模型（默认配置）：

```bash
cd /opt/musetalk/models/whisper
sudo wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
```

或使用 curl：

```bash
cd /opt/musetalk/models/whisper
sudo curl -L -o ggml-large-v3.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
```

### 4. 设置权限

确保文件有正确的权限：

```bash
sudo chmod 644 /opt/musetalk/models/whisper/*.bin
```

### 5. 验证文件

确认文件已正确放置：

```bash
ls -lh /opt/musetalk/models/whisper/
```

## 配置说明

在 `appsettings.json` 中，您可以修改使用的模型大小：

```json
"RealtimeDigitalHuman": {
  "WhisperNet": {
    "ModelSize": "Large"  // 可选: Tiny, Base, Small, Medium, Large
  }
}
```

### 模型选择建议

- **Tiny**: 最快，准确度最低，适合测试
- **Base**: 快速，准确度一般，适合实时应用
- **Small**: 平衡速度和准确度
- **Medium**: 较好的准确度，速度适中
- **Large**: 最高准确度，速度较慢，推荐用于生产环境

## Docker 挂载

模型目录已在 `docker-compose.yml` 中配置挂载：

```yaml
volumes:
  - /opt/musetalk/models:/models
```

容器内的路径为 `/models/whisper/`，程序会自动从这个位置加载模型。

## 故障排除

如果程序启动时报错找不到模型文件：

1. 检查文件是否存在：`ls /opt/musetalk/models/whisper/`
2. 检查文件名是否正确（必须与上表中的文件名完全一致）
3. 检查 Docker 容器是否正确挂载了目录：
   ```bash
   docker exec lmy-digitalhuman ls -la /models/whisper/
   ```
4. 查看容器日志获取详细错误信息：
   ```bash
   docker logs lmy-digitalhuman
   ```

## 注意事项

- 模型文件较大，下载可能需要一些时间
- 确保有足够的磁盘空间
- Large 模型提供最好的识别效果，但需要更多内存和计算资源
- 首次加载模型可能需要几秒钟时间