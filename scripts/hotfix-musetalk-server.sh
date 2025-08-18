#!/bin/bash
# 临时修复脚本 - 直接在musetalk-python容器内修改服务端代码
# 无需重建镜像

echo "🔧 应用MuseTalk服务端热修复..."

# 创建修复补丁
cat > /tmp/fix_protocol.patch << 'EOF'
--- a/ultra_fast_realtime_inference_v2.py
+++ b/ultra_fast_realtime_inference_v2.py
@@ -820,7 +820,15 @@ def handle_client_ultra_fast(client_socket, client_address):
         while True:
             data = client_socket.recv(4096).decode('utf-8')
             if not data:
                 break
-            request = json.loads(data)
+            
+            # 修复：处理可能没有换行符的消息
+            data = data.strip()
+            if not data:
+                continue
+                
+            # 尝试解析JSON
+            request = json.loads(data)
+            
             command = request.get('command')
             
             if command == 'preprocess':
EOF

# 应用补丁到容器内的文件
docker exec musetalk-python bash -c "
cd /opt/musetalk/repo/MuseTalkEngine
# 备份原文件
cp ultra_fast_realtime_inference_v2.py ultra_fast_realtime_inference_v2.py.bak

# 直接修改handle_client_ultra_fast函数
python3 << 'PYTHON_FIX'
import re

# 读取文件
with open('ultra_fast_realtime_inference_v2.py', 'r') as f:
    content = f.read()

# 查找并替换问题代码
old_pattern = r'data = client_socket\.recv\(4096\)\.decode\(\'utf-8\'\)\s+if not data:\s+break\s+request = json\.loads\(data\)'
new_code = '''data = client_socket.recv(4096).decode('utf-8')
            if not data:
                break
            
            # 修复：处理可能没有换行符的消息
            data = data.strip()
            if not data:
                continue
                
            try:
                # 尝试解析JSON
                request = json.loads(data)
            except json.JSONDecodeError as e:
                print(f'JSON解析错误: {e}, 原始数据: {data[:100]}')
                continue'''

# 使用更简单的替换方式
if 'request = json.loads(data)' in content:
    content = content.replace(
        'request = json.loads(data)',
        '''# 修复：安全解析JSON
            data = data.strip()
            if not data:
                continue
            try:
                request = json.loads(data)
            except json.JSONDecodeError as e:
                print(f'JSON解析错误: {e}')
                continue'''
    )
    
    # 写回文件
    with open('ultra_fast_realtime_inference_v2.py', 'w') as f:
        f.write(content)
    
    print('✅ 热修复应用成功')
else:
    print('⚠️ 未找到需要修复的代码，可能已经修复过了')
PYTHON_FIX
"

echo "✅ 热修复完成"
echo ""
echo "📝 注意事项："
echo "1. 此修复是临时的，容器重启后会失效"
echo "2. 建议测试完成后重建镜像以永久修复"
echo "3. 如果修复后仍有问题，可以重启musetalk-python服务"
echo ""
echo "🔄 如需重启服务（会中断几秒）："
echo "docker exec musetalk-python pkill -f 'ultra_fast_realtime_inference_v2.py'"
echo "等待几秒后服务会自动重启"