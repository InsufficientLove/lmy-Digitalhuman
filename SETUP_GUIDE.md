# 🔧 MuseTalk Docker 部署 - 问题解决指南

## 问题 1: 127.0.0.1:5000 访问被拒绝

### 原因分析
容器配置了 `ASPNETCORE_URLS=http://0.0.0.0:5000`，这意味着服务监听在所有网络接口上，但某些系统的本地回环地址（127.0.0.1）可能无法正确访问容器内的服务。

### ✅ 解决方案（三选一）

#### 方案 1: 使用内网 IP 访问（推荐）
```bash
# 您已经发现可以用内网IP访问
http://192.168.20.250:5000
```

#### 方案 2: 修改 docker-compose.yml 绑定到主机网络
```yaml
# 在 lmy-digitalhuman 服务中添加
lmy-digitalhuman:
  # ... 其他配置 ...
  network_mode: "host"  # 使用主机网络模式
  environment:
    - ASPNETCORE_URLS=http://0.0.0.0:5000
```

重启服务：
```bash
docker-compose down
docker-compose up -d
```

#### 方案 3: 配置端口转发（不推荐，因为已经可以访问）
保持现状，统一使用内网 IP `192.168.20.250:5000` 访问。

---

## 问题 2: 需要初始化视频文件

### 系统要求说明

MuseTalk 系统需要一个**数字人模板**才能工作。模板有两种类型：

1. **图片模板**（推荐）- 单张人脸照片，系统会自动预处理
2. **视频模板**（可选）- 预录制的视频，需要预处理人脸坐标

### 🎯 推荐方案：使用图片模板（最简单）

#### 准备图片
准备一张清晰的人脸正面照（要求）：
- 格式：JPG、PNG
- 分辨率：512x512 或更高
- 要求：人脸清晰、正脸、光线充足
- 建议：背景简洁、无遮挡

#### 上传并预处理图片

##### 方法 1: 通过 Web 界面上传（最简单）
```bash
# 访问 C# Web 界面
http://192.168.20.250:5000

# 在界面上传图片，系统会自动调用 Python API 进行预处理
```

##### 方法 2: 通过 API 上传
```bash
# 1. 将图片复制到容器的共享目录
docker cp your_photo.jpg lmy-digitalhuman:/app/wwwroot/templates/default.jpg

# 2. 调用预处理 API
curl -X POST "http://192.168.20.250:28888/api/preprocess_template" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "default",
    "image_path": "/app/wwwroot/templates/default.jpg",
    "force": false
  }'

# 预期返回：
{
  "success": true,
  "template_id": "default",
  "cache_path": "/opt/musetalk/template_cache/default",
  "message": "预处理成功"
}
```

##### 方法 3: 直接在宿主机操作
```bash
# 1. 将图片复制到宿主机的共享目录
cp your_photo.jpg /opt/musetalk/templates/default.jpg

# 2. 进入 Python 容器手动预处理
docker exec -it musetalk-python bash

# 3. 在容器内运行预处理
cd /opt/musetalk/repo/MuseTalkEngine
python3 -c "
from core.template_manager import preprocess_template
success = preprocess_template(
    template_id='default',
    image_path='/opt/musetalk/templates/default.jpg'
)
print('✅ 预处理成功' if success else '❌ 预处理失败')
"

# 4. 退出容器
exit
```

---

### 🎬 高级方案：使用视频模板

如果您想使用视频（比如预录制的待机动作），需要额外的预处理步骤。

#### 视频要求
- 格式：MP4
- 分辨率：512x512 或以上
- 帧率：25fps（推荐）
- 时长：任意（建议 3-10 秒）
- 内容：一个人的正面视频，人脸清晰可见

#### 创建视频模板的步骤

##### 步骤 1: 准备视频文件
```bash
# 将视频复制到宿主机
cp your_video.mp4 /opt/musetalk/videos/idle.mp4
```

##### 步骤 2: 预处理视频（提取人脸坐标）
```bash
# 进入 Python 容器
docker exec -it musetalk-python bash

# 在容器内执行预处理
cd /opt/musetalk/repo/MuseTalkEngine

python3 preprocess_assets.py \
  --video /videos/idle.mp4 \
  --output /temp/preprocessed

# 这会生成：
# /temp/preprocessed/idle_bbox.pkl    # 人脸坐标数据
# /temp/preprocessed/idle_bbox.json   # 人脸坐标（JSON格式）
```

##### 步骤 3: 将预处理结果复制到正确位置
```bash
# 在容器内
mkdir -p /opt/musetalk/preprocessed
cp /temp/preprocessed/idle_bbox.pkl /opt/musetalk/preprocessed/

# 退出容器
exit
```

##### 步骤 4: 通过 API 加载视频资产
```bash
curl -X POST "http://192.168.20.250:28888/load_asset" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "idle",
    "video_path": "/videos/idle.mp4",
    "bbox_path": "/opt/musetalk/preprocessed/idle_bbox.pkl"
  }'

# 预期返回：
{
  "success": true,
  "asset_id": "idle",
  "message": "资产加载成功"
}
```

---

## 🎯 快速验证步骤

### 1. 验证容器运行状态
```bash
docker-compose ps

# 应该看到三个容器都在运行：
# traefik
# musetalk-python
# lmy-digitalhuman
```

### 2. 验证 Python 服务
```bash
curl http://192.168.20.250:28888/health

# 预期返回：
{"status": "healthy", "service": "MuseTalk API"}
```

### 3. 验证 C# Web 服务
```bash
curl http://192.168.20.250:5000/health

# 预期返回：
{"status": "healthy", "timestamp": "..."}
```

### 4. 检查模板缓存
```bash
# 查看已预处理的模板
docker exec musetalk-python ls -la /opt/musetalk/template_cache/

# 如果有模板，应该看到类似：
# default/
#   default_preprocessed.pkl
#   default_metadata.json
#   model_state.pkl
```

---

## 📋 完整初始化流程（推荐）

```bash
# 1. 确保服务运行
docker-compose ps

# 2. 准备一张人脸照片（最简单的方式）
# 照片命名为 default.jpg

# 3. 复制到共享目录
docker cp default.jpg lmy-digitalhuman:/app/wwwroot/templates/default.jpg

# 4. 调用预处理 API
curl -X POST "http://192.168.20.250:28888/api/preprocess_template" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "default",
    "image_path": "/app/wwwroot/templates/default.jpg"
  }'

# 5. 验证预处理结果
docker exec musetalk-python ls -la /opt/musetalk/template_cache/default/

# 6. 现在可以开始使用系统了！
# 访问: http://192.168.20.250:5000
```

---

## 🔍 故障排查

### 问题：预处理失败
```bash
# 查看 Python 容器日志
docker logs musetalk-python --tail 100

# 常见原因：
# 1. 图片格式不支持 - 确保是 JPG 或 PNG
# 2. 人脸检测失败 - 确保照片中有清晰的正面人脸
# 3. GPU 内存不足 - 检查 nvidia-smi
```

### 问题：找不到模板
```bash
# 检查模板目录
docker exec musetalk-python ls -la /opt/musetalk/template_cache/
docker exec lmy-digitalhuman ls -la /app/wwwroot/templates/

# 确保两个容器都挂载了相同的目录
```

### 问题：API 调用失败
```bash
# 检查 Python 服务是否响应
curl http://192.168.20.250:28888/api/status

# 查看服务状态
docker exec musetalk-python ps aux | grep python
```

---

## 📄 示例图片要求

### ✅ 好的示例
- 正面照
- 表情自然（微笑或中性）
- 光线均匀
- 背景简洁
- 没有遮挡（眼镜可以，但不要墨镜）
- 分辨率至少 512x512

### ❌ 不好的示例
- 侧脸或仰头/低头
- 光线太暗或过曝
- 人脸被遮挡
- 多人照片
- 模糊不清

---

## 🎉 完成后的使用方式

### Web 界面使用
```
1. 访问 http://192.168.20.250:5000
2. 选择模板（default）
3. 输入文字或上传音频
4. 点击生成，等待视频生成
5. 播放生成的数字人视频
```

### API 调用
```bash
# 创建会话
curl -X POST "http://192.168.20.250:28888/api/start_session" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test123",
    "template_id": "default"
  }'

# 处理音频段
curl -X POST "http://192.168.20.250:28888/api/process_segment" \
  -F "session_id=test123" \
  -F "segment_index=0" \
  -F "audio=@input.wav"

# 结束会话
curl -X POST "http://192.168.20.250:28888/api/end_session" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test123"}'
```

---

## 📞 需要帮助？

如果遇到问题，请提供以下信息：

```bash
# 1. 容器状态
docker-compose ps

# 2. Python 服务日志
docker logs musetalk-python --tail 50

# 3. C# 服务日志
docker logs lmy-digitalhuman --tail 50

# 4. GPU 状态
docker exec musetalk-python nvidia-smi

# 5. 模板目录内容
docker exec musetalk-python ls -la /opt/musetalk/template_cache/
```

---

**祝您使用愉快！🚀**
