@echo off
title HRScreeningHelper - 2. Кабинет HR (8502)
cd /d "%~dp0"
echo ==========================================================
echo  2. Запуск Кабинета HR-специалиста (слепая оценка)
echo  Адрес в браузере: http://localhost:8502
echo ==========================================================
..\..\.venv\Scripts\streamlit.exe run app/hr_app.py --server.port 8502
pause
