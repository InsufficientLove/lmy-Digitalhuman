#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo -e "    数字人系统启动脚本"
echo -e "========================================${NC}"
echo

# 检查.NET SDK是否安装
if ! command -v dotnet &> /dev/null; then
    echo -e "${RED}[错误] 未找到.NET SDK，请先安装.NET 8.0 SDK${NC}"
    echo -e "${YELLOW}安装命令:${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install -y dotnet-sdk-8.0"
    echo "  CentOS/RHEL: sudo dnf install dotnet-sdk-8.0"
    echo "  macOS: brew install dotnet"
    echo -e "${YELLOW}或访问: https://dotnet.microsoft.com/download/dotnet/8.0${NC}"
    exit 1
fi

echo -e "${GREEN}[信息] 检测到.NET SDK版本:${NC}"
dotnet --version

echo
echo -e "${GREEN}[信息] 正在还原NuGet包...${NC}"
dotnet restore LmyDigitalHuman/LmyDigitalHuman.csproj
if [ $? -ne 0 ]; then
    echo -e "${RED}[错误] NuGet包还原失败${NC}"
    exit 1
fi

echo
echo -e "${GREEN}[信息] 正在编译项目...${NC}"
dotnet build LmyDigitalHuman/LmyDigitalHuman.csproj --configuration Release
if [ $? -ne 0 ]; then
    echo -e "${RED}[错误] 项目编译失败，请检查代码错误${NC}"
    exit 1
fi

echo
echo -e "${GREEN}[信息] 正在启动数字人系统...${NC}"
echo -e "${YELLOW}[提示] 系统启动后请访问: https://localhost:7001 或 http://localhost:5001${NC}"
echo -e "${YELLOW}[提示] 按 Ctrl+C 可停止服务${NC}"
echo

cd LmyDigitalHuman
dotnet run --configuration Release --urls "https://localhost:7001;http://localhost:5001"