@echo off
title 四诊合参模拟器

if not exist "venv\Scripts\activate.bat" (
    echo 首次使用，正在初始化环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install streamlit matplotlib pandas --quiet
) else (
    call venv\Scripts\activate.bat
)

echo 正在启动四诊合参模拟器...
streamlit run app_stage2.py
pause