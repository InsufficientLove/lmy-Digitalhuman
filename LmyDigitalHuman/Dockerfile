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

# 安装Python和edge-tts
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir edge-tts

COPY --from=build /app/publish .
ENV ASPNETCORE_URLS=http://0.0.0.0:5000
ENV ASPNETCORE_ENVIRONMENT=Docker
EXPOSE 5000
ENTRYPOINT ["dotnet", "LmyDigitalHuman.dll"]