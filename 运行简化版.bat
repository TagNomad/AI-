@echo off
chcp 65001 >nul
cls
title 智能驾驶安全监测系统 v3.0 (简化版)

echo ╔════════════════════════════════════════════════╗
echo ║     智能驾驶安全监测系统 v3.0 (简化版)         ║
echo ║     Simplified Drowsiness Detection            ║
echo ╚════════════════════════════════════════════════╝
echo.

echo 正在启动简化版程序...
echo 此版本会自动检测依赖库并给出安装提示
echo ════════════════════════════════════════════════
echo.

python DrowsinessDetector_simple.py

echo.
echo ════════════════════════════════════════════════
echo 程序已退出
pause 