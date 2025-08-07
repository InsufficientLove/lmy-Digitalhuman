# 修复Batch Size问题完整指南

## 问题诊断

您的日志显示batch_size仍然是16，而不是配置的6。这说明Python服务使用了缓存的旧代码。

## 解决步骤

### 1. 完全停止服务

```cmd
# Windows命令行
taskkill /F /IM python.exe
```

### 2. 清理Python缓存

在MuseTalkEngine目录运行：
```cmd
python clean_python_cache.py
```

或手动删除：
- 所有 `__pycache__` 目录
- 所有 `.pyc` 文件

### 3. 验证代码更改

确认以下文件的batch_size都是6：
- `ultra_fast_realtime_inference_v2.py` 第369行
- `global_musetalk_service.py` 第249行
- `gpu_config.py` 中的default值

### 4. 重启服务

重启您的.NET应用，它会启动新的Python服务。

### 5. 验证新配置

重启后应该看到：
- `GPU内存配置完成: 批次大小: 6`
- `⚙️ 执行4GPU并行推理，batch_size=6`
- `Latent batch shape: torch.Size([6, 8, 247, 164])`

## 内存计算验证

正确的内存需求应该是：
- batch_size=16: 48.90GB（超出单GPU）
- batch_size=6: 约18.3GB（适合24GB GPU）
- batch_size=4: 约12.2GB（更保守）

## 如果仍有问题

1. **检查是否有多个Python环境**
   ```cmd
   where python
   ```

2. **强制使用Python -B参数**（不生成.pyc文件）
   修改启动命令添加 `-B` 参数

3. **检查是否有其他服务占用端口**
   ```cmd
   netstat -an | findstr 28888
   ```

4. **使用环境变量禁用Python缓存**
   ```cmd
   set PYTHONDONTWRITEBYTECODE=1
   ```

## 预期效果

修复后您应该看到：
- 每个批次使用约18GB内存（而不是49GB）
- 4个GPU都能正常工作
- 推理成功完成