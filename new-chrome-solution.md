# 新版Chrome HTTPS解决方案

## 🔍 问题分析
新版Chrome对localhost的HTTPS要求更加严格，不再显示传统的证书警告页面。

## 🚀 解决方案

### 方案1：Chrome启动参数（推荐）
在命令行中使用以下参数启动Chrome：

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="C:\temp\chrome_dev" --ignore-certificate-errors --ignore-ssl-errors --allow-running-insecure-content --disable-web-security --allow-insecure-localhost --unsafely-treat-insecure-origin-as-secure=https://localhost:7001
```

### 方案2：使用HTTP访问（临时方案）
直接使用HTTP访问，但需要解决麦克风权限问题：
- 访问：http://localhost:5001/digital-human-test.html
- 在Chrome设置中允许HTTP站点访问麦克风

### 方案3：Chrome设置修改
1. 打开Chrome设置：chrome://settings/content/microphone
2. 添加允许站点：http://localhost:5001
3. 添加允许站点：https://localhost:7001

### 方案4：使用其他浏览器
- Firefox对localhost证书更宽松
- Edge浏览器也是不错的选择

## 🔧 技术说明
新版Chrome的安全策略变更：
- 不再显示"继续访问"选项
- 对HTTP/2 over TLS要求更严格
- localhost证书验证更严格

## 💡 建议
推荐使用方案1的Chrome启动参数，这是最可靠的开发环境解决方案。