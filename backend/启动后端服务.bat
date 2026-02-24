@echo off
chcp 65001 >nul
echo ========================================
echo 启动后端服务
echo ========================================
echo.

cd /d "%~dp0"

echo 检查Python环境...
python --version
if errorlevel 1 (
    echo.
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.8或更高版本
    echo.
    pause
    exit /b 1
)

echo.
echo 启动Flask服务...
echo 服务地址: http://localhost:5000
echo.
echo ⚠️ 请保持此窗口打开，不要关闭
echo ⚠️ 按 Ctrl+C 可以停止服务
echo.
echo ========================================
echo.

python app.py

pause
