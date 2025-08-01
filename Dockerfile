# 数字人系统 Docker 部署文件
# 支持.NET 8.0 和 Python 虚拟环境

# ===== 阶段1: .NET 构建阶段 =====
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# 复制项目文件并还原依赖
COPY ["LmyDigitalHuman/LmyDigitalHuman.csproj", "LmyDigitalHuman/"]
RUN dotnet restore "LmyDigitalHuman/LmyDigitalHuman.csproj"

# 复制所有源代码并构建
COPY . .
WORKDIR "/src/LmyDigitalHuman"
RUN dotnet build "LmyDigitalHuman.csproj" -c Release -o /app/build

# 发布应用
RUN dotnet publish "LmyDigitalHuman.csproj" -c Release -o /app/publish /p:UseAppHost=false

# ===== 阶段2: Python 环境准备阶段 =====
FROM python:3.11-slim AS python-env
WORKDIR /python-setup

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv_musetalk
ENV PATH="/opt/venv_musetalk/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ===== 阶段3: 运行时阶段 =====
FROM mcr.microsoft.com/dotnet/aspnet:8.0

# 安装Python运行时
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 创建应用目录
WORKDIR /app

# 复制.NET应用
COPY --from=build /app/publish .

# 复制Python虚拟环境
COPY --from=python-env /opt/venv_musetalk ./venv_musetalk

# 复制Python脚本和配置
COPY LmyDigitalHuman/musetalk_service_complete.py ./
COPY LmyDigitalHuman/appsettings.json ./
COPY LmyDigitalHuman/appsettings.Production.json ./

# 创建必要的目录
RUN mkdir -p /app/temp /app/logs /app/wwwroot/videos /app/wwwroot/templates /app/models

# 设置权限
RUN chmod +x /app/venv_musetalk/bin/python && \
    chmod -R 755 /app/venv_musetalk

# 设置环境变量
ENV ASPNETCORE_ENVIRONMENT=Docker
ENV ASPNETCORE_URLS=http://+:5000
ENV PYTHONPATH=/app/venv_musetalk/bin
ENV PATH="/app/venv_musetalk/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# 创建非root用户
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/diagnostics/system-info || exit 1

# 暴露端口
EXPOSE 5000

# 启动应用
ENTRYPOINT ["dotnet", "LmyDigitalHuman.dll"]