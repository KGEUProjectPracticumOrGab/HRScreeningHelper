"""
Главная точка входа фронтенда с поддержкой выбора режима через переменную APP_MODE.
Допустимые режимы:
  - candidate (по умолчанию) — Сайт Кандидата + Демо-генератор (Порт 8501)
  - hr — Кабинет HR-специалиста (Порт 8502)
  - lpr — Кабинет ЛПР (Порт 8503)
"""
import os
import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
_FRONTEND_DIR = _APP_DIR.parent
for _p in (str(_FRONTEND_DIR), str(_APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

mode = os.getenv("APP_MODE", "candidate").strip().lower()

if mode == "hr":
    try:
        from app.hr_app import main
    except ImportError:
        from hr_app import main
elif mode == "lpr":
    try:
        from app.lpr_app import main
    except ImportError:
        from lpr_app import main
else:
    try:
        from app.candidate_app import main
    except ImportError:
        from candidate_app import main

if __name__ == "__main__":
    main()
