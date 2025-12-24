@echo off
REM FORGEDAN 启动脚本 (Windows)
REM 使用方法: start_web.bat

cd /d "%~dp0"
set PYTHONPATH=%~dp0

echo ============================================
echo   FORGEDAN Web 界面
echo ============================================
echo.
echo 正在启动 Web 服务器...
echo 访问地址: http://127.0.0.1:5000
echo 按 Ctrl+C 停止
echo.

python -m forgedan.cli web

pause
