"""
Сайт №2: Кабинет HR-специалиста (Порт 8502).
Предназначен для рекрутеров: просмотр транскриптов интервью,
слепое независимое оценивание и генерация сводных отчетов для ЛПР.
"""
import sys
from pathlib import Path

# Гарантируем корректные пути поиска модулей
_APP_DIR = Path(__file__).resolve().parent
_FRONTEND_DIR = _APP_DIR.parent
for _p in (str(_FRONTEND_DIR), str(_APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st

try:
    from app.api_client import APIClient, DEFAULT_GATEWAY_URL
    from app.views.hr import render_hr_view
except ImportError:
    from api_client import APIClient, DEFAULT_GATEWAY_URL
    from views.hr import render_hr_view

st.set_page_config(
    page_title="HRScreening — Кабинет HR",
    page_icon="🧑‍💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header { font-size: 2rem; font-weight: 700; color: #1E3A8A; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    with st.sidebar:
        st.markdown("# 🧑‍💼 HRScreening")
        st.markdown("**Рабочее место рекрутера**")
        st.caption("Независимая оценка результатов скрининга")
        st.divider()

        st.info("🔒 В этом кабинете действует режим слепого оценивания (оценка ИИ скрыта).")

        st.divider()
        with st.expander("⚙️ Настройки сети", expanded=False):
            gw = st.text_input("Адрес API Gateway:", value=st.session_state.get("gateway_url", DEFAULT_GATEWAY_URL))
            st.session_state["gateway_url"] = gw.strip()

        st.divider()
        st.markdown(
            """
            <div style='font-size: 0.85rem; color: #888;'>
            <b>КГЭУ, ИИНм-2-26</b><br>
            • Depparain (Орехов К.)<br>
            • timikss (Габелия Т.)
            </div>
            """,
            unsafe_allow_html=True,
        )

    client = APIClient(base_url=st.session_state.get("gateway_url", DEFAULT_GATEWAY_URL))
    render_hr_view(client)


if __name__ == "__main__":
    main()
