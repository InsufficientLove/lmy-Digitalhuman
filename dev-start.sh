#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo -e "    数字人系统 - 开发模式启动"
echo -e "========================================${NC}"
echo

echo -e "${GREEN}[信息] 开发模式启动中...${NC}"
echo -e "${YELLOW}[提示] 开发模式支持热重载，代码修改后自动重启${NC}"
echo -e "${YELLOW}[提示] 系统启动后请访问: https://localhost:7001 或 http://localhost:5001${NC}"
echo -e "${YELLOW}[提示] 按 Ctrl+C 可停止服务${NC}"
echo

cd LmyDigitalHuman
dotnet watch run --urls "https://localhost:7001;http://localhost:5001"