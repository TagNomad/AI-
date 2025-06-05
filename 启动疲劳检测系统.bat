@echo off
chcp 65001 >nul
cls
title 智能驾驶安全监测系统 v3.0

echo ╔════════════════════════════════════════════════╗
echo ║       智能驾驶安全监测系统 v3.0                ║
echo ║       AI-Powered Drowsiness Detection          ║
echo ╔════════════════════════════════════════════════╗
echo.

REM 设置Python路径（如果系统PATH中没有Python，请修改这里）
set PYTHON_PATH=python

REM 检查Python
echo 检查Python环境...
%PYTHON_PATH% --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ 错误：未找到Python！
    echo.
    echo 请确保：
    echo 1. Python已正确安装
    echo 2. Python已添加到系统PATH环境变量
    echo 3. 或修改本文件中的PYTHON_PATH变量
    echo.
    pause
    exit /b 1
)

echo ✅ Python环境正常
echo.

REM 启动程序
echo 正在启动疲劳检测系统...
echo ════════════════════════════════════════════════
echo.

%PYTHON_PATH% DrowsinessDetector_modern.py

REM 检查退出代码
if errorlevel 1 (
    echo.
    echo ════════════════════════════════════════════════
    echo ❌ 程序运行出错！
    echo.
    echo 可能的原因：
    echo 1. 缺少必要的Python库（opencv-python, ultralytics, pillow等）
    echo 2. 模型文件缺失（请检查runs文件夹）
    echo 3. 摄像头无法访问
    echo.
    echo 请查看上方的错误信息。
    echo ════════════════════════════════════════════════
) else (
    echo.
    echo ════════════════════════════════════════════════
    echo ✅ 程序正常退出
    echo ════════════════════════════════════════════════
)

echo.
pause 