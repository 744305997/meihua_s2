@echo off
title 医案校准器 · 自动生成参数配置包

:: 检查虚拟环境是否存在，不存在则创建并安装依赖
if not exist "venv\Scripts\activate.bat" (
    echo 首次使用，正在初始化环境，请稍候...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install streamlit matplotlib pandas --quiet
    echo 环境初始化完成，正在启动校准器...
) else (
    call venv\Scripts\activate.bat
)

:: 启动 Streamlit 应用（校准器界面）
streamlit run case_calibrator.py

pause