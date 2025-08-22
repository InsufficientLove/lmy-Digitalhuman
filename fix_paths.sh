#!/bin/bash
echo "🔧 修复MuseTalk路径和导入问题..."

# 1. 修复mmpose导入
echo "修复mmpose API导入..."
sed -i 's/from mmpose.apis import inference_topdown, init_model/from mmpose.apis import inference_top_down_pose_model as inference_topdown, init_pose_model as init_model/' /opt/musetalk/repo/MuseTalk/musetalk/utils/preprocessing.py

# 2. 添加merge_data_samples兼容函数
echo "添加兼容函数..."
python3 -c "
file_path = '/opt/musetalk/repo/MuseTalk/musetalk/utils/preprocessing.py'
with open(file_path, 'r') as f:
    content = f.read()

if 'def merge_data_samples' not in content:
    content = content.replace(
        'from mmpose.apis import inference_top_down_pose_model as inference_topdown, init_pose_model as init_model',
        '''from mmpose.apis import inference_top_down_pose_model as inference_topdown, init_pose_model as init_model

# Compatibility function for mmpose 0.25.1
def merge_data_samples(results):
    \"\"\"Compatibility wrapper for mmpose 0.25.1\"\"\"
    if isinstance(results, list) and len(results) > 0:
        return results[0]
    return results'''
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    print('✅ Added compatibility function')
"

# 3. 修复文件路径为绝对路径
echo "修复文件路径..."
sed -i "s|config_file = './musetalk/utils/dwpose/rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py'|config_file = '/opt/musetalk/repo/MuseTalk/musetalk/utils/dwpose/rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py'|" /opt/musetalk/repo/MuseTalk/musetalk/utils/preprocessing.py

sed -i "s|checkpoint_file = './models/dwpose/dw-ll_ucoco_384.pth'|checkpoint_file = '/opt/musetalk/repo/MuseTalk/models/dwpose/dw-ll_ucoco_384.pth'|" /opt/musetalk/repo/MuseTalk/musetalk/utils/preprocessing.py

echo "✅ 路径修复完成！"