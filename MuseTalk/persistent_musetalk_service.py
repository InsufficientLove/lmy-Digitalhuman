#!/usr/bin/env python3
"""
Persistent MuseTalk Service
持久化MuseTalk服务

维持一个长期运行的Python进程，通过命名管道或TCP进行通信
避免每次推理都启动新的Python进程，实现真正的极速推理

作者: Claude Sonnet
版本: 1.0
用途: C# 服务进程持久化通信
"""

import os
import sys
import json
import time
import socket
import traceback
import threading
import argparse
from pathlib import Path
from queue import Queue, Empty
import signal

# 设置工作目录到项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入增强系统
try:
    from enhanced_musetalk_preprocessing import EnhancedMuseTalkPreprocessor
    from ultra_fast_realtime_inference import UltraFastRealtimeInference
    from enhanced_musetalk_inference_v4 import EnhancedMuseTalkInferenceV4
    print("✅ 增强MuseTalk系统导入成功")
except ImportError as e:
    print(f"❌ 增强系统导入失败: {e}")
    sys.exit(1)


class PersistentMuseTalkService:
    """
    持久化MuseTalk服务
    
    特点：
    - 长期运行的Python进程
    - TCP Socket通信接口
    - 预加载模型，零启动延迟
    - 队列处理多并发请求
    - 智能内存管理
    """
    
    def __init__(self, 
                 host="127.0.0.1", 
                 port=58080,
                 cache_dir="./model_states",
                 device="cuda:0",
                 max_workers=4):
        """
        初始化持久化服务
        
        Args:
            host: 监听主机
            port: 监听端口  
            cache_dir: 缓存目录
            device: 计算设备
            max_workers: 最大工作线程数
        """
        self.host = host
        self.port = port
        self.cache_dir = Path(cache_dir)
        self.device = device
        self.max_workers = max_workers
        
        # 服务状态
        self.is_running = False
        self.server_socket = None
        self.client_threads = []
        self.request_queue = Queue()
        
        # 增强推理系统（预加载）
        self.inference_system = None
        self.model_loaded = False
        
        print(f"🚀 初始化持久化MuseTalk服务")
        print(f"📡 监听地址: {host}:{port}")
        print(f"📱 计算设备: {device}")
        print(f"💾 缓存目录: {cache_dir}")
        print(f"👥 最大工作线程: {max_workers}")
    
    def load_models(self):
        """预加载模型到内存"""
        try:
            print(f"🔄 开始预加载MuseTalk模型...")
            start_time = time.time()
            
            # 初始化增强推理系统
            self.inference_system = EnhancedMuseTalkInferenceV4(
                device=self.device,
                cache_dir=str(self.cache_dir),
                fp16=True
            )
            
            self.model_loaded = True
            load_time = time.time() - start_time
            print(f"✅ 模型预加载完成，耗时: {load_time:.2f}秒")
            
        except Exception as e:
            print(f"❌ 模型预加载失败: {e}")
            traceback.print_exc()
            raise
    
    def start_server(self):
        """启动服务器"""
        try:
            # 预加载模型
            if not self.model_loaded:
                self.load_models()
            
            # 创建服务器Socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            print(f"🌟 持久化MuseTalk服务启动成功!")
            print(f"📡 监听地址: {self.host}:{self.port}")
            print(f"⏰ 启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 主服务循环
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"🔗 新客户端连接: {client_address}")
                    
                    # 创建客户端处理线程
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    self.client_threads.append(client_thread)
                    
                except Exception as e:
                    if self.is_running:
                        print(f"❌ 接受客户端连接失败: {e}")
        
        except KeyboardInterrupt:
            print(f"\n🛑 收到中断信号，正在关闭服务...")
            self.stop_server()
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            traceback.print_exc()
    
    def handle_client(self, client_socket, client_address):
        """处理客户端请求"""
        try:
            while self.is_running:
                # 接收请求数据
                data = client_socket.recv(8192)
                if not data:
                    break
                
                try:
                    # 解析JSON请求
                    request_str = data.decode('utf-8')
                    request_data = json.loads(request_str)
                    
                    print(f"📥 收到请求: {request_data.get('command', 'unknown')}")
                    
                    # 处理请求
                    response = self.process_request(request_data)
                    
                    # 发送响应
                    response_str = json.dumps(response, ensure_ascii=False)
                    client_socket.send(response_str.encode('utf-8'))
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        "success": False,
                        "error": f"JSON解析错误: {e}",
                        "error_type": "json_decode_error"
                    }
                    response_str = json.dumps(error_response, ensure_ascii=False)
                    client_socket.send(response_str.encode('utf-8'))
                
                except Exception as e:
                    print(f"❌ 处理客户端请求失败: {e}")
                    traceback.print_exc()
                    error_response = {
                        "success": False,
                        "error": str(e),
                        "error_type": "request_processing_error"
                    }
                    response_str = json.dumps(error_response, ensure_ascii=False)
                    client_socket.send(response_str.encode('utf-8'))
        
        except Exception as e:
            print(f"❌ 客户端处理异常: {client_address}, 错误: {e}")
        
        finally:
            try:
                client_socket.close()
                print(f"🔌 客户端连接关闭: {client_address}")
            except:
                pass
    
    def process_request(self, request_data):
        """处理具体请求"""
        try:
            command = request_data.get("command")
            
            if command == "ping":
                return self.handle_ping()
            
            elif command == "inference":
                return self.handle_inference(request_data)
            
            elif command == "preprocess":
                return self.handle_preprocess(request_data)
            
            elif command == "check_cache":
                return self.handle_check_cache(request_data)
            
            elif command == "status":
                return self.handle_status()
            
            elif command == "shutdown":
                return self.handle_shutdown()
            
            else:
                return {
                    "success": False,
                    "error": f"未知命令: {command}",
                    "error_type": "unknown_command"
                }
        
        except Exception as e:
            print(f"❌ 请求处理异常: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "error_type": "processing_exception"
            }
    
    def handle_ping(self):
        """处理ping请求"""
        return {
            "success": True,
            "message": "pong",
            "timestamp": time.time(),
            "model_loaded": self.model_loaded
        }
    
    def handle_inference(self, request_data):
        """处理推理请求"""
        try:
            if not self.model_loaded:
                return {
                    "success": False,
                    "error": "模型未加载",
                    "error_type": "model_not_loaded"
                }
            
            # 提取参数
            template_id = request_data.get("template_id")
            audio_path = request_data.get("audio_path")
            output_path = request_data.get("output_path")
            template_dir = request_data.get("template_dir", "./wwwroot/templates")
            fps = request_data.get("fps", 25)
            bbox_shift = request_data.get("bbox_shift", 0)
            parsing_mode = request_data.get("parsing_mode", "jaw")
            
            if not all([template_id, audio_path, output_path]):
                return {
                    "success": False,
                    "error": "缺少必要参数: template_id, audio_path, output_path",
                    "error_type": "missing_parameters"
                }
            
            print(f"⚡ 开始推理: {template_id}")
            start_time = time.time()
            
            # 执行推理
            result_path = self.inference_system.generate_video(
                template_id=template_id,
                audio_path=audio_path,
                output_path=output_path,
                template_dir=template_dir,
                fps=fps,
                bbox_shift=bbox_shift,
                parsing_mode=parsing_mode
            )
            
            inference_time = time.time() - start_time
            print(f"✅ 推理完成: {template_id}, 耗时: {inference_time:.2f}秒")
            
            return {
                "success": True,
                "result_path": result_path,
                "inference_time": inference_time,
                "template_id": template_id
            }
        
        except Exception as e:
            print(f"❌ 推理失败: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "error_type": "inference_error"
            }
    
    def handle_preprocess(self, request_data):
        """处理预处理请求"""
        try:
            if not self.model_loaded:
                return {
                    "success": False,
                    "error": "模型未加载",
                    "error_type": "model_not_loaded"
                }
            
            template_id = request_data.get("template_id")
            template_image_path = request_data.get("template_image_path")
            bbox_shift = request_data.get("bbox_shift", 0)
            parsing_mode = request_data.get("parsing_mode", "jaw")
            
            if not template_id:
                return {
                    "success": False,
                    "error": "缺少template_id参数",
                    "error_type": "missing_parameters"
                }
            
            print(f"🎯 开始预处理: {template_id}")
            start_time = time.time()
            
            # 执行预处理
            success = self.inference_system.ensure_template_preprocessed(
                template_id=template_id,
                template_image_path=template_image_path,
                bbox_shift=bbox_shift,
                parsing_mode=parsing_mode
            )
            
            process_time = time.time() - start_time
            print(f"✅ 预处理完成: {template_id}, 耗时: {process_time:.2f}秒")
            
            return {
                "success": success,
                "process_time": process_time,
                "template_id": template_id
            }
        
        except Exception as e:
            print(f"❌ 预处理失败: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "error_type": "preprocess_error"
            }
    
    def handle_check_cache(self, request_data):
        """检查缓存状态"""
        try:
            template_id = request_data.get("template_id")
            if not template_id:
                return {
                    "success": False,
                    "error": "缺少template_id参数",
                    "error_type": "missing_parameters"
                }
            
            cache_path = self.cache_dir / f"{template_id}_preprocessed.pkl"
            metadata_path = self.cache_dir / f"{template_id}_metadata.json"
            
            cache_exists = cache_path.exists() and metadata_path.exists()
            
            return {
                "success": True,
                "template_id": template_id,
                "cache_exists": cache_exists,
                "cache_path": str(cache_path) if cache_exists else None,
                "metadata_path": str(metadata_path) if cache_exists else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "check_cache_error"
            }
    
    def handle_status(self):
        """获取服务状态"""
        return {
            "success": True,
            "status": "running",
            "model_loaded": self.model_loaded,
            "device": self.device,
            "cache_dir": str(self.cache_dir),
            "active_threads": len(self.client_threads),
            "uptime": time.time(),
            "version": "1.0"
        }
    
    def handle_shutdown(self):
        """处理关闭请求"""
        print(f"🛑 收到关闭请求")
        threading.Thread(target=self.stop_server, daemon=True).start()
        return {
            "success": True,
            "message": "服务正在关闭..."
        }
    
    def stop_server(self):
        """停止服务器"""
        self.is_running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print(f"🔌 持久化MuseTalk服务已关闭")


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description="Persistent MuseTalk Service")
    
    parser.add_argument("--host", default="127.0.0.1", help="监听主机")
    parser.add_argument("--port", type=int, default=58080, help="监听端口")
    parser.add_argument("--cache_dir", default="./model_states", help="缓存目录")
    parser.add_argument("--device", default="cuda:0", help="计算设备")
    parser.add_argument("--max_workers", type=int, default=4, help="最大工作线程数")
    
    args = parser.parse_args()
    
    # 创建并启动服务
    service = PersistentMuseTalkService(
        host=args.host,
        port=args.port,
        cache_dir=args.cache_dir,
        device=args.device,
        max_workers=args.max_workers
    )
    
    # 注册信号处理
    def signal_handler(sig, frame):
        print(f"\n🛑 收到信号 {sig}，正在关闭服务...")
        service.stop_server()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务
    service.start_server()


if __name__ == "__main__":
    main()