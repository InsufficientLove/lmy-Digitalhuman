@echo off
chcp 65001 > nul
color 0C
title 数字人系统 - HTTPS证书强力修复工具

echo ================================================================================
echo                        数字人系统 - HTTPS证书强力修复工具
echo ================================================================================
echo.
echo ⚠️  此工具将彻底解决 HTTPS 开发证书问题
echo.
echo 🔧 修复步骤：
echo   1. 完全清理所有开发证书
echo   2. 重新生成并强制信任证书
echo   3. 清理浏览器SSL缓存
echo   4. 添加Chrome安全例外
echo.
echo ⚠️  请确保以管理员身份运行此脚本！
echo.
pause

echo ================================================================================
echo [步骤 1/5] 停止相关进程
echo ================================================================================

echo [信息] 正在停止可能占用证书的进程...
taskkill /f /im "dotnet.exe" >nul 2>&1
taskkill /f /im "LmyDigitalHuman.exe" >nul 2>&1
echo [✓] 进程清理完成

echo ================================================================================
echo [步骤 2/5] 完全清理现有证书
echo ================================================================================

echo [信息] 清理所有HTTPS开发证书...
dotnet dev-certs https --clean --verbose
if %errorlevel% neq 0 (
    echo [警告] 清理过程中遇到问题，继续执行...
)

echo [信息] 清理IIS Express证书...
netsh http delete sslcert ipport=0.0.0.0:44300 >nul 2>&1
netsh http delete sslcert ipport=0.0.0.0:7001 >nul 2>&1

echo ================================================================================
echo [步骤 3/5] 生成新的受信任证书
echo ================================================================================

echo [信息] 生成新的开发证书...
dotnet dev-certs https --verbose
if %errorlevel% neq 0 (
    echo [错误] 证书生成失败
    pause
    goto end
)

echo [信息] 强制信任证书...
dotnet dev-certs https --trust --verbose
if %errorlevel% neq 0 (
    echo [错误] 证书信任失败
    echo.
    echo 请确保：
    echo 1. 以管理员身份运行此脚本
    echo 2. 在弹出的对话框中点击"是"
    pause
    goto end
)

echo ================================================================================
echo [步骤 4/5] 验证证书状态
echo ================================================================================

echo [信息] 检查证书状态...
dotnet dev-certs https --check --verbose
if %errorlevel% neq 0 (
    echo [警告] 证书验证失败，但继续执行...
) else (
    echo [✓] 证书验证成功
)

echo ================================================================================
echo [步骤 5/5] 清理浏览器缓存指导
echo ================================================================================

echo [信息] 请手动执行以下浏览器清理步骤：
echo.
echo 🌐 Chrome浏览器：
echo   1. 按 Ctrl+Shift+Delete 打开清理对话框
echo   2. 选择"高级"选项卡
echo   3. 时间范围选择"所有时间"
echo   4. 勾选"Cookie及其他网站数据"和"缓存的图片和文件"
echo   5. 点击"清除数据"
echo.
echo 🔒 Chrome SSL状态重置：
echo   1. 在地址栏输入: chrome://settings/security
echo   2. 点击"管理证书"
echo   3. 在"受信任的根证书颁发机构"中找到"localhost"证书
echo   4. 确保证书存在且有效
echo.
echo 💡 或者尝试在Chrome中访问 chrome://flags/#allow-insecure-localhost
echo    启用"Allow invalid certificates for resources loaded from localhost"
echo.

echo ================================================================================
echo                                修复完成
echo ================================================================================
echo.
echo [✓] 证书修复完成！
echo.
echo 🚀 接下来请：
echo.
echo   1. 关闭所有浏览器窗口
echo   2. 重启 Visual Studio 2022
echo   3. 重新运行项目
echo   4. 访问: https://localhost:7001/digital-human-test.html
echo.
echo 💡 如果仍有问题，请尝试：
echo   - 使用无痕模式访问
echo   - 在Chrome地址栏中输入 thisisunsafe（当看到证书警告时）
echo   - 点击"高级" → "继续前往 localhost（不安全）"
echo.

:end
echo 按任意键退出...
pause >nul