"""
Сайт №1: Портал Кандидата + Демо-генератор (Порт 8501).
Предназначен для соискателей: прохождение голосового интервью и согласие на ПДн.
Включает песочницу для тестирования и создания демо-кандидатов.
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
    from app.views.candidate import render_candidate_view
    from app.views.demo import render_demo_view
except ImportError:
    from api_client import APIClient, DEFAULT_GATEWAY_URL
    from views.candidate import render_candidate_view
    from views.demo import render_demo_view

st.set_page_config(
    page_title="HRScreening — Портал Кандидата",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Оформление
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
        st.markdown("# 🎙️ HRScreening")
        st.markdown("**Портал соискателя**")
        st.caption("Голосовое онлайн-интервью для кандидатов")
        st.divider()

        pages = [
            "👤 Моё интервью",
            "🧪 Демо-генератор (песочница)",
        ]

        if "candidate_nav" not in st.session_state:
            st.session_state["candidate_nav"] = pages[0]

        curr_idx = pages.index(st.session_state["candidate_nav"]) if st.session_state["candidate_nav"] in pages else 0
        selected_page = st.radio("Раздел:", pages, index=curr_idx)
        st.session_state["candidate_nav"] = selected_page

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

    if selected_page == "👤 Моё интервью":
        render_candidate_view(client)
    elif selected_page == "🧪 Демо-генератор (песочница)":
        render_demo_view(client)


if __name__ == "__main__":
    main()
