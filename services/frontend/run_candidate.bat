@echo off
title HRScreeningHelper - 1. Сайт Кандидата (8501)
cd /d "%~dp0"
echo ==========================================================
echo  1. Запуск Портала Кандидата (+ Демо-генератор)
echo  Адрес в браузере: http://localhost:8501
echo ==========================================================
..\..\.venv\Scripts\streamlit.exe run app/candidate_app.py --server.port 8501
pause
