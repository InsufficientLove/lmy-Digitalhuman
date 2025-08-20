#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块 - 控制日志级别和输出
"""

import os
import logging

# 从环境变量获取日志级别
LOG_LEVEL = os.environ.get('MUSE_LOG_LEVEL', 'INFO').upper()
SHOW_PING_LOGS = os.environ.get('MUSE_SHOW_PING_LOGS', 'false').lower() == 'true'

# 配置日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logging():
    """设置全局日志配置"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT
    )
    
    # 设置特定模块的日志级别
    if not SHOW_PING_LOGS:
        # 降低心跳检测相关的日志级别
        logging.getLogger('heartbeat').setLevel(logging.WARNING)
        logging.getLogger('ping').setLevel(logging.WARNING)

def should_log_ping():
    """判断是否应该记录ping日志"""
    return SHOW_PING_LOGS

def log_if_not_ping(message, data=None):
    """只在非ping命令时记录日志"""
    if data:
        try:
            import json
            request = json.loads(data) if isinstance(data, str) else data
            if request.get('command') == 'ping' and not SHOW_PING_LOGS:
                return False
        except:
            pass
    print(message)
    return True

# 初始化日志配置
setup_logging()