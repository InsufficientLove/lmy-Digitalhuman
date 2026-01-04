#!/bin/bash
# MuseTalk Bug 修复验证脚本

echo "================================"
echo "MuseTalk Bug 修复验证"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查文件是否存在
echo "📁 检查修复的文件..."
files=(
    "MuseTalkEngine/offline/batch_inference.py"
    "MuseTalkEngine/offline/global_musetalk_service.py"
    "MuseTalkEngine/main_realtime.py"
    "MuseTalkEngine/core/gpu_inference_pool.py"
    "MuseTalkEngine/core/preprocessing.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (文件不存在)"
    fi
done
echo ""

# 检查 VAE Float32 修复
echo "🔍 验证 VAE Float32 修复..."
vae_float32_count=$(grep -r "torch.float32.*VAE\|VAE.*torch.float32" MuseTalkEngine/ --include="*.py" | grep -v ".pyc" | wc -l)
if [ "$vae_float32_count" -ge 5 ]; then
    echo -e "${GREEN}✓${NC} VAE Float32 修复已应用 ($vae_float32_count 处)"
else
    echo -e "${YELLOW}⚠${NC} VAE Float32 修复可能不完整 ($vae_float32_count 处，期望 ≥5)"
fi

# 检查颜色转换修复
echo "🔍 验证颜色转换修复..."
color_fix_count=$(grep -r "COLOR_RGB2BGR" MuseTalkEngine/ --include="*.py" | grep -v ".pyc" | wc -l)
if [ "$color_fix_count" -ge 3 ]; then
    echo -e "${GREEN}✓${NC} 颜色转换修复已应用 ($color_fix_count 处)"
else
    echo -e "${YELLOW}⚠${NC} 颜色转换修复可能不完整 ($color_fix_count 处，期望 ≥3)"
fi

# 检查 decode_latents Float32 转换
echo "🔍 验证 decode_latents Float32 转换..."
decode_fp32_count=$(grep -r "pred_latents.*\.to.*float32\|pred_latents_fp32" MuseTalkEngine/ --include="*.py" | grep -v ".pyc" | wc -l)
if [ "$decode_fp32_count" -ge 4 ]; then
    echo -e "${GREEN}✓${NC} decode_latents Float32 转换已应用 ($decode_fp32_count 处)"
else
    echo -e "${YELLOW}⚠${NC} decode_latents Float32 转换可能不完整 ($decode_fp32_count 处，期望 ≥4)"
fi

# 检查尺寸匹配修复
echo "🔍 验证尺寸匹配修复..."
resize_fix_count=$(grep -r "target_w, target_h = x2 - x1, y2 - y1" MuseTalkEngine/ --include="*.py" | grep -v ".pyc" | wc -l)
if [ "$resize_fix_count" -ge 3 ]; then
    echo -e "${GREEN}✓${NC} 尺寸匹配修复已应用 ($resize_fix_count 处)"
else
    echo -e "${YELLOW}⚠${NC} 尺寸匹配修复可能不完整 ($resize_fix_count 处，期望 ≥3)"
fi

echo ""
echo "================================"
echo "📊 修复统计"
echo "================================"
git diff --stat 2>/dev/null || echo "未检测到 git 仓库"
echo ""

echo "================================"
echo "✅ 验证完成"
echo "================================"
echo ""
echo "💡 提示："
echo "1. 如果所有检查都通过，说明修复已正确应用"
echo "2. 运行推理测试以验证实际效果"
echo "3. 观察日志中是否出现："
echo "   ✓ 'GPU0 VAE 保持 Float32（避免cuDNN错误）'"
echo "   ✓ '并行合成完成: N 帧'"
echo "   ✗ 不应再出现 'cuDNN error' 或 'blending失败'"
echo ""
echo "📚 详细文档："
echo "   - 中文说明: 修复说明.md"
echo "   - 英文说明: BUG_FIXES_SUMMARY.md"
echo ""
