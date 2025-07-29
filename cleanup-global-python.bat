@echo off
chcp 65001 >nul
echo ================================================================================
echo                    清理全局 Python 环境中的项目依赖
echo ================================================================================
echo.
echo 此脚本将帮助您清理全局 Python 环境中可能存在的项目相关依赖包
echo 这些包可能是之前直接安装到全局环境中的，现在我们使用虚拟环境管理
echo.
echo ⚠️  注意：此操作将从全局 Python 环境中卸载以下类型的包：
echo   - PyTorch 相关包 (torch, torchvision, torchaudio)
echo   - Edge-TTS 语音合成包
echo   - 图像处理包 (opencv-python, pillow, scikit-image)
echo   - 科学计算包 (numpy, scipy)
echo   - 音频处理包 (librosa, pydub)
echo   - 其他工具包 (tqdm, requests)
echo.
choice /c YN /m "确定要继续清理全局 Python 环境吗"
if errorlevel 2 goto cancel

echo.
echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境
    echo 如果您的 Python 安装路径不在 PATH 中，请手动执行清理
    pause
    goto end
)

echo [✓] Python 环境正常
python --version

echo.
echo [2/3] 检查已安装的相关包...
echo [信息] 正在扫描全局环境中的相关包...

REM 创建临时文件存储要卸载的包
echo torch>temp_packages.txt
echo torchvision>>temp_packages.txt
echo torchaudio>>temp_packages.txt
echo edge-tts>>temp_packages.txt
echo opencv-python>>temp_packages.txt
echo pillow>>temp_packages.txt
echo scipy>>temp_packages.txt
echo scikit-image>>temp_packages.txt
echo librosa>>temp_packages.txt
echo tqdm>>temp_packages.txt
echo pydub>>temp_packages.txt
echo requests>>temp_packages.txt
echo numpy>>temp_packages.txt

set "FOUND_PACKAGES="
for /f %%i in (temp_packages.txt) do (
    python -c "import %%i" >nul 2>&1
    if not errorlevel 1 (
        echo [发现] %%i
        set "FOUND_PACKAGES=!FOUND_PACKAGES! %%i"
    )
)

del temp_packages.txt

if "%FOUND_PACKAGES%"=="" (
    echo [✓] 全局环境中未发现项目相关依赖包
    echo 您的全局 Python 环境很干净！
    goto success
)

echo.
echo [3/3] 卸载发现的包...
echo [信息] 将要卸载的包:%FOUND_PACKAGES%
echo.
choice /c YN /m "确认卸载这些包"
if errorlevel 2 goto cancel

echo [信息] 正在卸载包...

REM 卸载 PyTorch 相关（通常最大）
echo [信息] 卸载 PyTorch 相关包...
pip uninstall torch torchvision torchaudio -y >nul 2>&1

REM 卸载其他包
echo [信息] 卸载其他依赖包...
pip uninstall edge-tts opencv-python pillow scipy scikit-image librosa tqdm pydub -y >nul 2>&1

REM numpy 可能被其他包依赖，最后卸载
echo [信息] 尝试卸载 numpy（如果没有其他依赖）...
pip uninstall numpy -y >nul 2>&1

REM requests 是常用包，询问是否卸载
python -c "import requests" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo [询问] requests 是常用的HTTP库，其他项目可能也在使用
    choice /c YN /m "是否也要卸载 requests"
    if not errorlevel 2 (
        pip uninstall requests -y >nul 2>&1
        echo [✓] requests 已卸载
    )
)

echo.
echo [✓] 清理完成！

:success
echo.
echo ================================================================================
echo                              清理完成
echo ================================================================================
echo.
echo [✓] 全局 Python 环境清理完成
echo.
echo 💡 接下来建议：
echo   1. 运行 setup-environment.bat 重新创建虚拟环境
echo   2. 使用 verify-environment.bat 验证环境配置
echo   3. 今后所有 Python 依赖都将在虚拟环境中管理
echo.
echo 🐍 虚拟环境的优势：
echo   - 项目依赖完全隔离
echo   - 不影响系统全局 Python 环境
echo   - 便于版本管理和环境复制
echo.
goto end

:cancel
echo.
echo [取消] 用户取消了清理操作
echo 如果您以后想要清理，可以重新运行此脚本

:end
echo.
echo 按任意键退出...
pause >nul