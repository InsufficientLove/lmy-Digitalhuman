#!/bin/bash

echo "=== 验证 GPUResourceManager 方法签名 ==="
echo ""
echo "接口定义 (IGPUResourceManager.cs):"
grep -n "AllocateGPUAsync\|ReleaseGPUAsync" LmyDigitalHuman/Services/IGPUResourceManager.cs
echo ""
echo "实现类 (GPUResourceManager.cs):"
grep -n "public.*AllocateGPUAsync\|public.*ReleaseGPUAsync" LmyDigitalHuman/Services/Core/GPUResourceManager.cs
echo ""
echo "=== Git 信息 ==="
echo "当前提交: $(git rev-parse HEAD)"
echo "最新提交信息:"
git log -1 --oneline