FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet restore ./LmyDigitalHuman/LmyDigitalHuman.csproj
RUN dotnet publish ./LmyDigitalHuman/LmyDigitalHuman.csproj -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
# 安装 Python 运行环境，供模板预处理等本地调用使用
RUN apt-get update && apt-get install -y python3 python3-venv python3-pip \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /app/publish .
ENV ASPNETCORE_URLS=http://0.0.0.0:5000
EXPOSE 5000
ENTRYPOINT ["dotnet", "LmyDigitalHuman.dll"]