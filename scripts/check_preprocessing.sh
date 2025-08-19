#!/bin/bash

# 检查预处理结果的脚本

TEMPLATE_ID=${1:-xiaoha}
MODELS_DIR="/opt/musetalk/models/templates"

echo "🔍 检查模板预处理结果: $TEMPLATE_ID"
echo "================================"

# 检查目录是否存在
TEMPLATE_DIR="$MODELS_DIR/$TEMPLATE_ID"
if [ -d "$TEMPLATE_DIR" ]; then
    echo "✅ 预处理目录存在: $TEMPLATE_DIR"
    
    # 列出目录内容
    echo ""
    echo "📁 目录内容:"
    ls -la "$TEMPLATE_DIR"
    
    # 检查关键文件
    echo ""
    echo "🔍 检查关键文件:"
    
    if [ -f "$TEMPLATE_DIR/preprocessed.flag" ]; then
        echo "  ✅ preprocessed.flag - 预处理标记文件"
    else
        echo "  ❌ preprocessed.flag - 缺失"
    fi
    
    if [ -f "$TEMPLATE_DIR/preprocessing_info.json" ]; then
        echo "  ✅ preprocessing_info.json - 预处理信息"
        echo ""
        echo "📄 预处理信息内容:"
        cat "$TEMPLATE_DIR/preprocessing_info.json" 2>/dev/null | python3 -m json.tool
    else
        echo "  ❌ preprocessing_info.json - 缺失"
    fi
    
    # 检查是否有latents文件（真正的预处理会生成）
    if ls "$TEMPLATE_DIR"/*.pt 2>/dev/null | grep -q .; then
        echo "  ✅ 找到 .pt 文件（潜在特征）"
        ls -lh "$TEMPLATE_DIR"/*.pt
    else
        echo "  ⚠️ 没有找到 .pt 文件（可能是模拟预处理）"
    fi
    
    # 检查是否有人脸检测结果
    if [ -f "$TEMPLATE_DIR/face_landmarks.json" ]; then
        echo "  ✅ face_landmarks.json - 人脸关键点"
    fi
    
    if [ -f "$TEMPLATE_DIR/face_bbox.json" ]; then
        echo "  ✅ face_bbox.json - 人脸边界框"
    fi
    
else
    echo "❌ 预处理目录不存在: $TEMPLATE_DIR"
    echo ""
    echo "可用的模板目录:"
    ls -d "$MODELS_DIR"/*/ 2>/dev/null || echo "没有找到任何模板目录"
fi

echo ""
echo "================================"
echo "💡 提示："
echo "  - 如果是模拟预处理，只会有 flag 和 info 文件"
echo "  - 真正的预处理会生成 .pt 文件和人脸检测结果"
echo "  - 可以通过 info 文件中的 'mode' 字段判断是否为模拟"