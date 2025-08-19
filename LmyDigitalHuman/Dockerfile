FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
# 先仅复制项目文件以最大化利用缓存
COPY LmyDigitalHuman/LmyDigitalHuman.csproj LmyDigitalHuman/
RUN dotnet restore ./LmyDigitalHuman/LmyDigitalHuman.csproj
# 再复制其余代码并发布
COPY LmyDigitalHuman ./LmyDigitalHuman
RUN dotnet publish ./LmyDigitalHuman/LmyDigitalHuman.csproj -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app

# 配置国内镜像源并安装Python和edge-tts
# 使用阿里云镜像源加速apt-get
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-setuptools \
    && rm -rf /var/lib/apt/lists/* && \
    # 使用清华大学镜像源加速pip
    pip3 install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple edge-tts

COPY --from=build /app/publish .
ENV ASPNETCORE_URLS=http://0.0.0.0:5000
ENV ASPNETCORE_ENVIRONMENT=Docker
EXPOSE 5000
ENTRYPOINT ["dotnet", "LmyDigitalHuman.dll"]