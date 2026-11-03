"""
Кабинет HR-специалиста (Внутренний контур).
Реализует сценарий:
  1. Просмотр списка откликов
  2. Слепое оценивание (транскрипт ответов БЕЗ подсказок ИИ)
  3. Выставление независимого балла и текстовой характеристики
  4. Генерация .docx-отчета и передача ЛПР
"""
import streamlit as st
import pandas as pd
try:
    from app.api_client import APIClient
except ImportError:
    try:
        from ..api_client import APIClient
    except ImportError:
        from api_client import APIClient


def render_hr_view(client: APIClient):
    st.header("🧑‍💼 Кабинет HR-специалиста")
    st.caption("Независимая экспертная оценка транскрипций скрининга")

    # Получаем список всех откликов
    responses, err = client.get_all_responses()

    if err:
        st.error(f"Не удалось получить список откликов: {err}")
        return

    if not responses:
        st.warning("В базе данных пока нет ни одного отклика. Создайте тестового кандидата во вкладке «Демо-генератор».")
        return

    # Фильтрация по статусам
    col_filter, col_refresh = st.columns([3, 1])
    with col_filter:
        status_options = ["Все статусы", "HR оценка", "Процесс скрининга", "Отзыв ЛПР", "Завершённые"]
        selected_filter = st.selectbox("Фильтр по статусу:", status_options, index=1 if any(r.get("status") == "HR оценка" for r in responses) else 0)
    with col_refresh:
        st.write("")
        st.write("")
        if st.button("🔄 Обновить список", use_container_width=True):
            st.rerun()

    # Фильтруем список
    filtered_responses = responses
    if selected_filter == "HR оценка":
        filtered_responses = [r for r in responses if r.get("status") == "HR оценка"]
    elif selected_filter == "Процесс скрининга":
        filtered_responses = [r for r in responses if r.get("status") == "Процесс скрининга"]
    elif selected_filter == "Отзыв ЛПР":
        filtered_responses = [r for r in responses if r.get("status") == "Отзыв ЛПР"]
    elif selected_filter == "Завершённые":
        filtered_responses = [r for r in responses if r.get("status") in ("Приглашение на второй этап", "Отказ по скринингу")]

    # Таблица откликов
    table_data = []
    for r in filtered_responses:
        c = r.get("candidate") or {}
        table_data.append({
            "ID отклика": r.get("id"),
            "ФИО кандидата": c.get("full_name", "Не указано"),
            "Контакты": c.get("contact_info", "Не указано"),
            "Статус": r.get("status"),
            "Дата создания": str(r.get("created_at", ""))[:19],
        })

    if table_data:
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    else:
        st.info("Нет кандидатов, соответствующих выбранному фильтру.")
        return

    st.divider()
    st.subheader("📝 Экспертная оценка кандидата")

    # Селектор кандидата для проверки
    candidate_options = {
        f"#{r['id']} — {(r.get('candidate') or {}).get('full_name', 'Кандидат')} ({r.get('status')})": r["id"]
        for r in filtered_responses
    }

    selected_label = st.selectbox("Выберите отклик для проверки:", list(candidate_options.keys()))
    selected_response_id = candidate_options[selected_label]

    # Загружаем транскрипт (слепое оценивание!)
    with st.spinner("Загрузка транскрипта..."):
        transcript_data, t_err = client.get_transcript(selected_response_id)

    if t_err:
        st.error(f"Ошибка загрузки транскрипта: {t_err}")
        return

    curr_status = transcript_data.get("status")
    candidate_info = transcript_data.get("candidate") or {}

    # Информационная плашка
    st.info(
        f"**Кандидат:** {candidate_info.get('full_name')} | **Контакты:** {candidate_info.get('contact_info')} | **Текущий статус:** {curr_status}"
    )

    # Примечание о слепом оценивании
    st.markdown(
        """
        > 🔒 **Режим слепого независимого оценивания (NFR):**
        > В данном интерфейсе баллы и комментарии искусственного интеллекта намеренно скрыты. 
        > Это исключает предвзятость при выставлении экспертной оценки HR.
        """
    )

    questions = transcript_data.get("questions", [])
    if not questions:
        st.warning("Пока нет транскрибированных ответов по данному кандидату.")
        return

    st.write("### 💬 Вопросы и транскрипция ответов соискателя:")
    for idx, q in enumerate(questions, 1):
        with st.expander(f"Вопрос №{idx}: {q.get('question_text')}", expanded=True):
            st.markdown("**Расшифровка ответа соискателя (STT):**")
            cand_ans = q.get("candidate_transcript")
            if cand_ans:
                st.code(cand_ans, language="text")
            else:
                st.caption("Ответ еще не записан или не распознан.")

    st.divider()

    # Форма выставления оценки доступна только если статус 'HR оценка'
    if curr_status == "HR оценка":
        st.subheader("🎯 Форма выставления HR-оценки")
        with st.form("hr_review_form"):
            hr_score = st.slider(
                "Балл кандидата (по шкале от 1 до 10):",
                min_value=1.0,
                max_value=10.0,
                value=7.5,
                step=0.5,
                help="Ваша независимая экспертная оценка технической грамотности и коммуникации кандидата",
            )
            hr_comment = st.text_area(
                "Экспертная характеристика и комментарий:",
                placeholder="Уверенно ответил на вопросы о многопоточности, понимает разницу между типами данных. Рекомендуется к рассмотрению.",
                help="Данный комментарий войдёт в сводный .docx отчёт для ЛПР",
                height=120,
            )

            submit_btn = st.form_submit_button(
                "💾 Сохранить оценку и отправить отчёт ЛПР", type="primary", use_container_width=True
            )

            if submit_btn:
                if not hr_comment.strip():
                    st.error("Пожалуйста, напишите краткую текстовую характеристику кандидата!")
                else:
                    with st.spinner("Сохранение оценки, генерация .docx отчета и отправка уведомления ЛПР..."):
                        rev_res, rev_err = client.submit_hr_review(
                            selected_response_id, hr_score=hr_score, hr_comment=hr_comment.strip()
                        )
                        if rev_err:
                            st.error(f"Не удалось сохранить оценку: {rev_err}")
                        else:
                            st.success("✅ HR-оценка успешно сохранена!")
                            st.info("Сводный .docx-отчет сформирован. Кандидат переведён на этап «Отзыв ЛПР».")
                            st.rerun()
    else:
        st.info(f"ℹ️ Выставление оценки недоступно: отклик находится в статусе «{curr_status}». Оценка выставляется на этапе «HR оценка».")
