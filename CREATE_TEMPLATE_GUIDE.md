# 📸 MuseTalk 模板创建指南

## 🎯 模板类型选择

MuseTalk 支持两种模板类型，根据您的需求选择：

| 类型 | 优点 | 缺点 | 适用场景 |
|-----|------|------|---------|
| **图片模板** | 简单快速、占用空间小 | 只能生成说话动作 | 客服、播报、对话 |
| **视频模板** | 可包含表情动作、更自然 | 需要预处理、占用空间大 | 虚拟主播、演示 |

### 推荐：图片模板（90% 场景够用）

---

## 方案一：使用图片模板（推荐）

### 📷 图片要求

#### 必须满足
- ✅ 格式：JPG、PNG
- ✅ 分辨率：至少 512x512 像素
- ✅ 人脸：正面、清晰可见
- ✅ 光线：均匀充足
- ✅ 数量：一人

#### 建议优化
- 🎯 表情：微笑或中性表情
- 🎯 背景：纯色或简洁背景
- 🎯 质量：高清照片
- 🎯 角度：平视镜头
- 🎯 着装：正式或休闲皆可

#### ❌ 避免
- ❌ 侧脸、仰头、低头
- ❌ 戴墨镜、口罩等遮挡物
- ❌ 光线太暗或过曝
- ❌ 多人合照
- ❌ 模糊或低分辨率

---

### 🚀 创建图片模板（三种方法）

#### 方法 1: 一键脚本（最简单）

创建脚本 `create_template.sh`：
```bash
#!/bin/bash

# 使用说明
if [ "$#" -lt 2 ]; then
    echo "用法: ./create_template.sh <模板ID> <图片路径>"
    echo "示例: ./create_template.sh john ./photos/john.jpg"
    exit 1
fi

TEMPLATE_ID=$1
IMAGE_PATH=$2

echo "🚀 开始创建模板: $TEMPLATE_ID"

# 1. 复制图片到共享目录
echo "📦 复制图片到容器..."
docker cp "$IMAGE_PATH" lmy-digitalhuman:/app/wwwroot/templates/${TEMPLATE_ID}.jpg

# 2. 调用预处理 API
echo "⚙️ 开始预处理..."
curl -X POST "http://192.168.20.250:28888/api/preprocess_template" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_id\": \"$TEMPLATE_ID\",
    \"image_path\": \"/app/wwwroot/templates/${TEMPLATE_ID}.jpg\",
    \"force\": false
  }"

# 3. 验证结果
echo ""
echo "✅ 预处理完成，验证结果..."
docker exec musetalk-python ls -la /opt/musetalk/template_cache/${TEMPLATE_ID}/

echo ""
echo "🎉 模板创建完成！"
echo "📋 模板ID: $TEMPLATE_ID"
echo "🌐 现在可以在 http://192.168.20.250:5000 使用该模板"
```

使用方法：
```bash
chmod +x create_template.sh
./create_template.sh default my_photo.jpg
```

---

#### 方法 2: 手动执行步骤

```bash
# 1. 复制图片到容器
docker cp your_photo.jpg lmy-digitalhuman:/app/wwwroot/templates/default.jpg

# 2. 调用预处理 API
curl -X POST "http://192.168.20.250:28888/api/preprocess_template" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "default",
    "image_path": "/app/wwwroot/templates/default.jpg"
  }'

# 3. 验证预处理结果（可选）
docker exec musetalk-python ls -la /opt/musetalk/template_cache/default/

# 应该看到以下文件：
# default_preprocessed.pkl
# default_metadata.json  
# model_state.pkl
```

---

#### 方法 3: 通过 Web 界面上传

```bash
# 1. 访问 Web 界面
http://192.168.20.250:5000

# 2. 找到"上传模板"或"管理模板"功能

# 3. 上传图片，系统会自动预处理

# 注意：具体界面取决于 C# 前端实现
```

---

## 方案二：使用视频模板（高级）

### 📹 视频要求

#### 必须满足
- ✅ 格式：MP4
- ✅ 编码：H.264
- ✅ 分辨率：至少 512x512
- ✅ 帧率：25fps（推荐）
- ✅ 时长：3-10 秒
- ✅ 内容：一个人的正面视频

#### 建议优化
- 🎯 动作：自然的待机动作（微笑、点头等）
- 🎯 表情：友好、专业
- 🎯 背景：纯色或绿幕
- 🎯 光线：均匀稳定

---

### 🎬 创建视频模板

#### 步骤 1: 准备视频
```bash
# 如果需要转换格式或调整参数
ffmpeg -i input.mov -c:v libx264 -preset medium -crf 23 \
  -s 512x512 -r 25 -t 5 output.mp4
```

#### 步骤 2: 复制到容器
```bash
docker cp output.mp4 musetalk-python:/videos/idle.mp4
```

#### 步骤 3: 预处理视频（提取人脸坐标）
```bash
# 进入 Python 容器
docker exec -it musetalk-python bash

# 运行预处理脚本
cd /opt/musetalk/repo/MuseTalkEngine
python3 preprocess_assets.py \
  --video /videos/idle.mp4 \
  --output /temp/preprocessed

# 查看生成的文件
ls -la /temp/preprocessed/

# 应该看到：
# idle_bbox.pkl   - 人脸坐标数据（二进制）
# idle_bbox.json  - 人脸坐标数据（JSON格式，可查看）

# 退出容器
exit
```

#### 步骤 4: 移动预处理结果
```bash
# 将生成的 pkl 文件移到正确位置
docker exec musetalk-python mkdir -p /opt/musetalk/preprocessed
docker exec musetalk-python cp /temp/preprocessed/idle_bbox.pkl /opt/musetalk/preprocessed/
```

#### 步骤 5: 加载视频资产
```bash
curl -X POST "http://192.168.20.250:28888/load_asset" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "idle",
    "video_path": "/videos/idle.mp4",
    "bbox_path": "/opt/musetalk/preprocessed/idle_bbox.pkl"
  }'
```

---

## 🔄 一键视频模板创建脚本

创建 `create_video_template.sh`：
```bash
#!/bin/bash

if [ "$#" -lt 2 ]; then
    echo "用法: ./create_video_template.sh <模板ID> <视频路径>"
    echo "示例: ./create_video_template.sh idle ./videos/idle.mp4"
    exit 1
fi

TEMPLATE_ID=$1
VIDEO_PATH=$2

echo "🚀 开始创建视频模板: $TEMPLATE_ID"

# 1. 复制视频到容器
echo "📦 复制视频到容器..."
docker cp "$VIDEO_PATH" musetalk-python:/videos/${TEMPLATE_ID}.mp4

# 2. 预处理视频
echo "⚙️ 预处理视频（提取人脸坐标）..."
docker exec musetalk-python bash -c "
cd /opt/musetalk/repo/MuseTalkEngine && \
python3 preprocess_assets.py \
  --video /videos/${TEMPLATE_ID}.mp4 \
  --output /temp/preprocessed
"

# 3. 移动预处理结果
echo "📋 整理预处理结果..."
docker exec musetalk-python mkdir -p /opt/musetalk/preprocessed
docker exec musetalk-python cp /temp/preprocessed/${TEMPLATE_ID}_bbox.pkl /opt/musetalk/preprocessed/

# 4. 加载资产
echo "🔄 加载视频资产..."
curl -X POST "http://192.168.20.250:28888/load_asset" \
  -H "Content-Type: application/json" \
  -d "{
    \"asset_id\": \"$TEMPLATE_ID\",
    \"video_path\": \"/videos/${TEMPLATE_ID}.mp4\",
    \"bbox_path\": \"/opt/musetalk/preprocessed/${TEMPLATE_ID}_bbox.pkl\"
  }"

echo ""
echo "🎉 视频模板创建完成！"
echo "📋 模板ID: $TEMPLATE_ID"
```

使用方法：
```bash
chmod +x create_video_template.sh
./create_video_template.sh idle my_video.mp4
```

---

## 📋 模板管理

### 列出所有模板
```bash
# 列出图片模板
docker exec musetalk-python ls -la /opt/musetalk/template_cache/

# 列出视频资产
curl http://192.168.20.250:28888/assets
```

### 删除模板
```bash
# 删除图片模板
docker exec musetalk-python rm -rf /opt/musetalk/template_cache/template_name/

# 删除视频
docker exec musetalk-python rm /videos/template_name.mp4
docker exec musetalk-python rm /opt/musetalk/preprocessed/template_name_bbox.pkl
```

### 重新预处理（强制覆盖）
```bash
curl -X POST "http://192.168.20.250:28888/api/preprocess_template" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "default",
    "image_path": "/app/wwwroot/templates/default.jpg",
    "force": true
  }'
```

---

## 🧪 测试模板

### 快速测试图片模板
```bash
# 1. 创建会话
curl -X POST "http://192.168.20.250:28888/api/start_session" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test001",
    "template_id": "default"
  }'

# 2. 处理测试音频
# 先准备一个测试音频文件 test.wav

curl -X POST "http://192.168.20.250:28888/api/process_segment" \
  -F "session_id=test001" \
  -F "segment_index=0" \
  -F "audio=@test.wav"

# 3. 结束会话
curl -X POST "http://192.168.20.250:28888/api/end_session" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test001"}'
```

---

## 🎨 高级技巧

### 批量创建多个模板
```bash
#!/bin/bash
# batch_create_templates.sh

PHOTOS_DIR="./employee_photos"

for photo in $PHOTOS_DIR/*.jpg; do
    filename=$(basename "$photo" .jpg)
    echo "创建模板: $filename"
    ./create_template.sh "$filename" "$photo"
    sleep 2
done

echo "✅ 批量创建完成！"
```

### 自动化视频转换
```bash
# convert_and_create.sh
INPUT=$1
TEMPLATE_ID=$2

# 转换视频为标准格式
ffmpeg -i "$INPUT" \
  -c:v libx264 \
  -preset medium \
  -crf 23 \
  -s 512x512 \
  -r 25 \
  -t 5 \
  "/tmp/${TEMPLATE_ID}.mp4"

# 创建模板
./create_video_template.sh "$TEMPLATE_ID" "/tmp/${TEMPLATE_ID}.mp4"

# 清理临时文件
rm "/tmp/${TEMPLATE_ID}.mp4"
```

---

## 🔍 故障排查

### 问题：预处理失败
```bash
# 查看详细日志
docker logs musetalk-python --tail 100

# 常见原因：
# 1. 图片中没有检测到人脸
# 2. 图片格式不支持
# 3. GPU 内存不足
# 4. 文件路径不正确
```

### 问题：找不到模板文件
```bash
# 检查文件是否存在
docker exec musetalk-python ls -la /app/wwwroot/templates/
docker exec lmy-digitalhuman ls -la /app/wwwroot/templates/

# 检查目录挂载
docker inspect musetalk-python | grep Mounts -A 20
```

### 问题：视频预处理太慢
```bash
# 使用较短的视频（3-5秒）
# 降低分辨率到 512x512
# 确保 GPU 可用

docker exec musetalk-python nvidia-smi
```

---

## 📚 参考资料

- 图片要求示例：见本文档"图片要求"部分
- 视频要求示例：见本文档"视频要求"部分
- API 文档：查看 `DOCKER_USAGE.md`
- 完整部署指南：查看 `SETUP_GUIDE.md`

---

**祝您创建出完美的数字人模板！🎭**
