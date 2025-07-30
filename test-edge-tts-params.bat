@echo off
echo ================================================================================
echo                    Test Edge-TTS Parameter Formats
echo ================================================================================
echo.
echo This script will test different edge-tts parameter formats
echo.
pause

if not exist "temp" mkdir temp

echo [1/5] Testing with correct percentage rate format...
set "TEST_FILE1=%CD%\temp\test_rate_percent.mp3"
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --rate "+0%" --text "正确的百分比格式测试" --write-media "%TEST_FILE1%"
if exist "%TEST_FILE1%" (
    echo ✅ Rate +0%% works
    del "%TEST_FILE1%"
) else (
    echo ❌ Rate +0%% failed
)

echo.
echo [2/5] Testing with correct Hz pitch format...
set "TEST_FILE2=%CD%\temp\test_pitch_hz.mp3"
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --pitch "+0Hz" --text "正确的赫兹格式测试" --write-media "%TEST_FILE2%"
if exist "%TEST_FILE2%" (
    echo ✅ Pitch +0Hz works
    del "%TEST_FILE2%"
) else (
    echo ❌ Pitch +0Hz failed
)

echo.
echo [3/5] Testing with both rate and pitch...
set "TEST_FILE3=%CD%\temp\test_both_params.mp3"
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --rate "+0%" --pitch "+0Hz" --text "完整参数测试" --write-media "%TEST_FILE3%"
if exist "%TEST_FILE3%" (
    echo ✅ Both parameters work
    del "%TEST_FILE3%"
) else (
    echo ❌ Both parameters failed
)

echo.
echo [4/5] Testing with different rate values...
for %%r in ("+0%" "-25%" "+50%") do (
    set "TEST_FILE4=%CD%\temp\test_rate_%%~r.mp3"
    echo Testing rate: %%r
    python -m edge_tts --voice zh-CN-XiaoxiaoNeural --rate "%%r" --text "速度测试" --write-media "!TEST_FILE4!" 2>nul
    if exist "!TEST_FILE4!" (
        echo ✅ Rate %%r works
        del "!TEST_FILE4!"
    ) else (
        echo ❌ Rate %%r failed
    )
)

echo.
echo [5/5] Testing with different pitch values...
for %%p in ("+0Hz" "-50Hz" "+100Hz") do (
    set "TEST_FILE5=%CD%\temp\test_pitch_%%~p.mp3"
    echo Testing pitch: %%p
    python -m edge_tts --voice zh-CN-XiaoxiaoNeural --pitch "%%p" --text "音调测试" --write-media "!TEST_FILE5!" 2>nul
    if exist "!TEST_FILE5!" (
        echo ✅ Pitch %%p works
        del "!TEST_FILE5!"
    ) else (
        echo ❌ Pitch %%p failed
    )
)

echo.
echo ================================================================================
echo                           Parameter Format Guide
echo ================================================================================
echo.
echo Edge-TTS Parameter Requirements:
echo.
echo Rate (语速):
echo   - Must be in percentage format: +0%%, -25%%, +50%%
echo   - NOT: "medium", "fast", "slow"
echo.
echo Pitch (音调):  
echo   - Must be in Hz format: +0Hz, -100Hz, +200Hz
echo   - NOT: "medium", "high", "low"
echo.
echo Voice (语音):
echo   - Use exact voice names: zh-CN-XiaoxiaoNeural
echo   - NOT: simplified names
echo.
echo Now the application should work with correct parameter conversion!
echo.
pause