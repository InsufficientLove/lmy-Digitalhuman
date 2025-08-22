#!/bin/bash
echo "🔧 修复MMCV版本冲突..."

# 1. 检查当前安装的版本
echo "当前安装的包："
pip3 list | grep -E "mmcv|mmpose|mmdet|mmengine"

# 2. 卸载所有MM系列包
echo "卸载旧版本..."
pip3 uninstall -y mmcv mmcv-full mmpose mmdet mmengine 2>/dev/null

# 3. 清理pip缓存
pip3 cache purge

# 4. 重新安装正确版本的mmcv-full（而不是mmcv）
echo "安装mmcv-full 1.7.0（兼容mmpose 0.29.0）..."
pip3 install --no-cache-dir mmcv-full==1.7.0 -f https://download.openmmlab.com/mmcv/dist/cu121/torch2.1/index.html

# 5. 安装其他MM包
echo "安装mmpose和mmdet..."
pip3 install --no-cache-dir mmpose==0.29.0 mmdet==2.28.2

# 6. 验证安装
echo "验证安装..."
python3 -c "
import mmcv
import mmpose
import mmdet
print(f'✅ MMCV: {mmcv.__version__}')
print(f'✅ MMPose: {mmpose.__version__}')
print(f'✅ MMDet: {mmdet.__version__}')
print('✅ 所有MM包安装成功！')
"

echo "修复完成！"