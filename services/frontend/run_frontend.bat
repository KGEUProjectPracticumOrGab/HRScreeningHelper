@echo off
title HRScreeningHelper - Frontend (Streamlit)
cd /d "%~dp0"
echo ========================================================
echo  Запуск веб-интерфейса Streamlit (HRScreeningHelper)
echo  Интерфейс откроется в браузере: http://localhost:8501
echo ========================================================
..\..\.venv\Scripts\streamlit.exe run app/main.py
pause
