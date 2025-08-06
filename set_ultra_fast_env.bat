@echo off
echo 🚀 设置Ultra Fast环境变量...
set MUSETALK_ULTRA_FAST_MODE=1
set MUSETALK_BATCH_SIZE=16
set MUSETALK_ENABLE_MONITORING=1
set MUSETALK_GPU_OPTIMIZATION=1
set CUDA_VISIBLE_DEVICES=0,1,2,3
echo ✅ 环境变量设置完成
echo 🎯 Ultra Fast模式已激活
