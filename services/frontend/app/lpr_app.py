"""
Сайт №3: Кабинет ЛПР (Руководителя / Нанимающего менеджера) (Порт 8503).
Предназначен для лиц, принимающих решения: просмотр двойной независимой оценки (ИИ + HR),
скачивание .docx отчетов, согласование перехода на второй этап или отказ.
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
    from app.views.lpr import render_lpr_view
except ImportError:
    from api_client import APIClient, DEFAULT_GATEWAY_URL
    from views.lpr import render_lpr_view

st.set_page_config(
    page_title="HRScreening — Кабинет ЛПР",
    page_icon="👔",
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
        st.markdown("# 👔 HRScreening")
        st.markdown("**Кабинет руководителя (ЛПР)**")
        st.caption("Финальное согласование и архив решений")
        st.divider()

        st.info("⚖️ Здесь сопоставляются две независимые оценки: ИИ-модели и эксперта HR.")

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
    render_lpr_view(client)


if __name__ == "__main__":
    main()
