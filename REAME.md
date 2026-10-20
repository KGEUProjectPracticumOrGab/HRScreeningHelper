# HRScreeningHelper 🤖🎯

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

> **Интеллектуальная микросервисная платформа автоматизированного голосового скрининга кандидатов.**

---

## 💡 О проекте и предыстории (HRTech)

**HRScreeningHelper** — это логическое развитие и духовное наследие нашего предыдущего проекта, связанного с парсингом, структурированием и глубоким анализом неструктурированных файлов резюме. 

В современной индустрии **HRTech** узким горлышком любого найма остается первичный скрининг: рекрутеры тратят сотни часов на рутинные созвоны с десятками кандидатов, а человеческий фактор часто приводит к субъективным оценкам. Наша система решает эту проблему комплексным подходом:
* **Автоматизация интервью:** ИИ-агент проводит голосовой опрос кандидата с помощью синтеза (`TTS`) и распознавания речи (`STT`).
* **Интеллектуальный анализ:** Локальные LLM оценивают ответы соискателя в строгом сравнении с эталонными требованиями вакансии.
* **Двойная независимая оценка:** Система исключает предвзятость, сопоставляя автоматический балл ИИ (`AI_score`) с независимым экспертным мнением HR-специалиста (`HR_score`) перед передачей отчета лицу, принимающему решения (ЛПР).

---

## 📚 Документация

Полная архитектурная спецификация проекта, детальное описание бизнес-процессов, схемы (`BPMN`, `C4`, `Sequence`, `ER`, `Use Case`, `State Machine`), спецификация API REST и модель данных доступны по ссылке:

👉 **[Перейти к полной документации проекта (docs/hr_screening_helper_docs.md)](docs/hr_screening_helper_docs.md)**

---

## 👥 Авторы и разработка

Проект разрабатывается в рамках выполнения учебного проекта в **КГЭУ** студентами группы **ИИНм-2-26**:

* **Depparain** — Орехов Кирилл ([GitHub профиль](https://github.com/Depparain))
* **timikss** — Габелия Тимур ([GitHub профиль](https://github.com/timikss))

---

## 🛠️ Быстрый старт

Инструкции по развертыванию микросервисов, настройке окружения (`.env`) и запуску через Docker Compose будут добавлены по мере реализации бэкенда.