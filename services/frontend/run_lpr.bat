@echo off
title HRScreeningHelper - 3. Кабинет ЛПР (8503)
cd /d "%~dp0"
echo ==========================================================
echo  3. Запуск Кабинета ЛПР (руководитель, финальное решение)
echo  Адрес в браузере: http://localhost:8503
echo ==========================================================
..\..\.venv\Scripts\streamlit.exe run app/lpr_app.py --server.port 8503
pause
