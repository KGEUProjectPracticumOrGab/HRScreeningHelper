@echo off
title HRScreeningHelper - Запуск всех 3 сайтов
cd /d "%~dp0"
echo ==========================================================
echo  Запуск всех 3 сайтов системы HRScreeningHelper:
echo  1. Кандидат + Демо: http://localhost:8501
echo  2. HR-специалист:   http://localhost:8502
echo  3. Руководитель ЛПР: http://localhost:8503
echo ==========================================================

start "HRScreening - Кандидат (8501)" cmd /k "..\..\.venv\Scripts\streamlit.exe run app/candidate_app.py --server.port 8501"
start "HRScreening - HR (8502)" cmd /k "..\..\.venv\Scripts\streamlit.exe run app/hr_app.py --server.port 8502"
start "HRScreening - ЛПР (8503)" cmd /k "..\..\.venv\Scripts\streamlit.exe run app/lpr_app.py --server.port 8503"

echo Все три сайта запущены в отдельных окнах!
pause
