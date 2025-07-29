# 🔧 新版Chrome访问解决方案

## 🎯 问题
新版Chrome对localhost HTTPS访问更加严格，不显示传统的证书警告页面。

## ✅ 最简单的解决方案

### 方法1：命令行启动Chrome（推荐）

1. **关闭所有Chrome窗口**
2. **按Win+R，输入cmd，回车**
3. **复制粘贴以下命令**：

```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="%TEMP%\chrome_dev" --ignore-certificate-errors --ignore-ssl-errors --allow-running-insecure-content --disable-web-security --allow-insecure-localhost https://localhost:7001/digital-human-test.html
```

如果Chrome安装在其他位置，尝试：
```cmd
"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --user-data-dir="%TEMP%\chrome_dev" --ignore-certificate-errors --ignore-ssl-errors --allow-running-insecure-content --disable-web-security --allow-insecure-localhost https://localhost:7001/digital-human-test.html
```

### 方法2：使用HTTP访问

直接访问：http://localhost:5001/digital-human-test.html

然后在Chrome设置中允许麦克风权限：
1. 点击地址栏左侧的🔒图标
2. 选择"麦克风" → "允许"

### 方法3：使用Firefox浏览器

Firefox对localhost证书更宽松，直接访问：
https://localhost:7001/digital-human-test.html

遇到警告时点击"高级" → "继续访问"

## 💡 说明

- 方法1使用临时Chrome配置，不会影响您的正常浏览
- 方法2简单但麦克风权限需要手动设置
- 方法3是最可靠的备选方案

## 🚀 推荐流程

1. 先尝试方法1（命令行Chrome）
2. 如果不行，使用方法3（Firefox）
3. 最后考虑方法2（HTTP + 权限设置）