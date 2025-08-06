# 服务器启动指南

## 🎯 单独启动C#数字人服务

### 方法1: 直接启动 (推荐)

```cmd
cd C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\LmyDigitalHuman
dotnet run
```

### 方法2: 发布模式启动

```cmd
cd C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\LmyDigitalHuman
dotnet run --configuration Release
```

## 🔧 启动说明

1. **自动启动**: C#服务启动时会自动启动Python推理服务
2. **端口配置**: 
   - C# API服务: http://localhost:5001
   - Python推理服务: 端口28888 (自动启动)
3. **日志监控**: 所有日志会在控制台显示

## 📊 验证服务状态

### 检查API服务
```
浏览器访问: http://localhost:5001/swagger
```

### 检查Python服务
```
日志中查看: "🌐 Ultra Fast Service 就绪 - 监听端口: 28888"
```

## 🛠️ 故障排除

### 如果Python服务启动失败:

1. **检查虚拟环境**:
   ```cmd
   C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\venv_musetalk\Scripts\activate
   ```

2. **检查模型文件**:
   ```
   确认存在: C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\MuseTalk\models\
   ```

3. **手动启动Python服务** (调试用):
   ```cmd
   cd C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\MuseTalkEngine
   C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\venv_musetalk\Scripts\python.exe start_ultra_fast_service.py --port 28888
   ```

## 📈 性能测试

服务启动后，可以运行性能测试:
```cmd
cd C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman
C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\venv_musetalk\Scripts\python.exe test_ultra_fast_performance.py
```

## 🎯 预期启动日志

成功启动时应该看到:
```
🌍 当前运行环境: Development
🚀 正在启动4GPU共享全局MuseTalk服务...
🔧 工作目录设置为: C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\MuseTalk
🚀 启动Ultra Fast MuseTalk服务...
🚀 Ultra Fast Service 初始化完成 - 4GPU并行架构
🌐 Ultra Fast Service 就绪 - 监听端口: 28888
✅ 4GPU共享全局MuseTalk服务启动成功
🚀 数字人API服务启动成功
Now listening on: http://localhost:5001
```