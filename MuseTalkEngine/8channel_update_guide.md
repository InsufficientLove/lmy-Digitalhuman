# 8通道预处理更新指南

## 更新内容

我们已经更新了预处理方式，现在生成的是8通道的latent（4通道masked + 4通道reference），以匹配UNet模型的期望输入。

### 主要改动

1. **预处理阶段（optimized_preprocessing_v2.py）**
   - 现在使用面部解析（Face Parsing）生成面部mask
   - VAE编码时生成两个latent：
     - masked_latent: 应用了面部mask的图像latent（4通道）
     - reference_latent: 原始图像的latent（4通道）
   - 将两个latent拼接成8通道输出

2. **推理阶段（ultra_fast_realtime_inference_v2.py）**
   - 移除了临时的4通道到8通道转换代码
   - 直接使用预处理生成的8通道latent

## 使用方法

### 1. 重新预处理模板

由于预处理格式已更改，需要重新预处理现有模板：

```bash
cd /workspace/MuseTalkEngine
python optimized_preprocessing_v2.py --template_path <模板图片路径> --output_dir ./model_state --template_id <模板ID>
```

### 2. 测试预处理结果

使用测试脚本验证预处理是否正确生成8通道：

```bash
# 测试特定模板
python test_8channel_preprocessing.py --template_id <模板ID>

# 测试所有缓存文件
python test_8channel_preprocessing.py
```

### 3. 运行推理

预处理完成后，可以正常运行推理：

```bash
python ultra_fast_realtime_inference_v2.py
```

## 技术细节

### Masked Latent vs Reference Latent

- **Masked Latent**: 只包含面部区域的latent，背景被mask掉（设为0）
- **Reference Latent**: 完整图像的latent，包含所有信息

UNet模型使用这两个latent的组合来生成更准确的输出，其中：
- Masked latent提供面部区域的精确信息
- Reference latent提供完整的上下文信息

### 面部解析Mask处理

1. 使用FaceParsing模型生成语义分割mask（0=背景，1-19=不同面部部位）
2. 将mask转换为二值mask（面部区域=1，背景=0）
3. 应用高斯滤波平滑mask边缘
4. 根据需要调整mask大小以匹配图像尺寸

## 注意事项

1. 旧的4通道预处理缓存文件不兼容，需要重新生成
2. 如果面部解析失败，系统会使用复制的reference latent作为fallback
3. 预处理时会输出latent形状信息，应该显示为8通道

## 性能影响

- 预处理时间略有增加（需要额外的面部解析和双重VAE编码）
- 推理性能保持不变（移除了运行时的通道转换）
- 整体质量提升（更准确的面部区域处理）