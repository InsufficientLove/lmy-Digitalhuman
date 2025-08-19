# Ollama 模型管理指南

## 1. 查看已安装的模型列表

```bash
# 查看所有已下载的模型
docker exec -it ollama ollama list

# 或者在宿主机上（如果直接安装了ollama）
ollama list
```

## 2. 下载新模型

```bash
# 下载常用的中文模型
docker exec -it ollama ollama pull qwen2.5:7b        # 通义千问2.5 7B
docker exec -it ollama ollama pull qwen2:7b          # 通义千问2 7B  
docker exec -it ollama ollama pull llama3.2:3b       # Llama 3.2 3B (较小)
docker exec -it ollama ollama pull deepseek-coder:6.7b # DeepSeek编程模型

# 下载其他模型
docker exec -it ollama ollama pull mistral:7b        # Mistral 7B
docker exec -it ollama ollama pull gemma2:9b         # Google Gemma2 9B
```

## 3. 在配置文件中指定模型

编辑 `/workspace/LmyDigitalHuman/appsettings.json` 或 `appsettings.Docker.json`:

```json
{
  "Ollama": {
    "BaseUrl": "http://host.docker.internal:11434",
    "Model": "qwen2.5:7b",  // 在这里指定模型名称
    "Temperature": 0.7,
    "MaxTokens": 2048,
    "SystemPrompt": "你是一个专业的AI助手，请用中文回答问题。"
  }
}
```

## 4. 支持的模型列表

### 中文优化模型（推荐）
- `qwen2.5:7b` - 通义千问2.5，中文效果最好
- `qwen2:7b` - 通义千问2
- `yi:6b` - 零一万物Yi模型

### 多语言模型
- `llama3.2:3b` - 最新的Llama，较小但效果好
- `mistral:7b` - Mistral 7B
- `gemma2:9b` - Google的Gemma2

### 编程专用
- `deepseek-coder:6.7b` - 编程能力强
- `codellama:7b` - Meta的编程模型

## 5. 模型选择建议

- **中文对话**: 使用 `qwen2.5:7b` 或 `qwen2:7b`
- **快速响应**: 使用 `llama3.2:3b` 或 `qwen2.5:3b`
- **编程相关**: 使用 `deepseek-coder:6.7b`
- **平衡性能**: 使用 `mistral:7b`

## 6. 测试模型

```bash
# 测试模型是否工作
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "prompt": "你好，请介绍一下你自己",
    "stream": false
  }'
```

## 7. 删除不需要的模型

```bash
# 删除模型以节省空间
docker exec -it ollama ollama rm model_name
```

## 8. 查看模型信息

```bash
# 查看模型详细信息
docker exec -it ollama ollama show qwen2.5:7b
```

## 注意事项

1. 首次下载模型可能需要较长时间（几GB大小）
2. 确保有足够的磁盘空间
3. 模型会保存在Docker卷中：`ollama:/root/.ollama`
4. 可以同时安装多个模型，在配置中切换使用