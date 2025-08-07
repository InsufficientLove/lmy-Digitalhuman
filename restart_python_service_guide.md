# Python服务重启指南

## 为什么需要重启？

您看到的错误表明Python服务仍在使用旧代码（batch_size=16），需要重启才能加载新的配置。

## 重启步骤

### 1. 停止当前服务
在Windows任务管理器中：
1. 查找所有Python进程
2. 结束相关进程

或使用命令行：
```cmd
taskkill /F /IM python.exe
```

### 2. 重启.NET应用
重启您的ASP.NET Core应用，它会自动启动新的Python服务。

### 3. 验证新配置
重启后，日志应该显示：
- `Latent batch shape: torch.Size([6, 8, 247, 164])` （不是16）
- `Estimated memory: ~18GB` （不是48.90GB）

## 批次大小计算

基于您的4×24GB显卡配置：
- 原始需求：48.90GB ÷ 16 = 3.06GB per frame
- 可用内存：24GB × 0.8 = 19.2GB（留20%余量）
- 最大批次：19.2GB ÷ 3.06GB = 6.27
- 推荐设置：batch_size = 6

## 性能预期

- batch_size=16：需要48.90GB（超出单GPU内存）
- batch_size=6：需要约18.4GB（适合24GB显卡）
- batch_size=4：需要约12.2GB（更保守）
- batch_size=1：需要约3.1GB（最保守）

## 故障排除

如果重启后仍有问题：
1. 检查Python进程是否完全关闭
2. 确认拉取了最新代码
3. 查看启动日志中的batch_size配置
4. 使用nvidia-smi监控实际内存使用