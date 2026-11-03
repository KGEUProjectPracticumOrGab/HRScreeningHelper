"""
Экран прохождения скрининга кандидатом (Внешний контур).
Реализует сценарий:
  1. Вход по токен-ссылке
  2. Голосовое приветствие и согласие на ПДн (152-ФЗ)
  3. Цикл вопросов (озвучка TTS + запись ответа через микрофон/файл)
  4. Завершение сессии (LLM-анализ, прощальное аудио)
"""
import streamlit as st
try:
    from app.api_client import APIClient, decode_base64_audio
except ImportError:
    try:
        from ..api_client import APIClient, decode_base64_audio
    except ImportError:
        from api_client import APIClient, decode_base64_audio


def render_candidate_view(client: APIClient):
    st.header("🎙️ Прохождение первичного голосового интервью")
    st.caption("Автоматизированный скрининг кандидатов с использованием ИИ")

    # Получаем токен из query параметров URL (например, ?token=abc) или из ввода
    query_params = st.query_params
    default_token = query_params.get("token", "")

    # Поле ввода токена
    col1, col2 = st.columns([3, 1])
    with col1:
        token = st.text_input(
            "Ваш персональный токен-код доступа:",
            value=st.session_state.get("candidate_token", default_token),
            placeholder="Например: demo-a1b2c3d4",
            help="Токен высылается в приглашении на скрининг (в письме или Telegram)",
        )
    with col2:
        st.write("")
        st.write("")
        check_btn = st.button("Проверить токен", use_container_width=True)

    if token:
        st.session_state["candidate_token"] = token.strip()

    active_token = st.session_state.get("candidate_token", "").strip()
    if not active_token:
        st.info("👈 Введите ваш токен доступа выше (или создайте тестового кандидата во вкладке «Демо-генератор»).")
        return

    # Запрашиваем информацию о сессии
    session_data, err = client.get_candidate_session(active_token)

    if err:
        st.error(f"⚠️ {err}")
        st.caption("Если вы считаете, что это ошибка, обратитесь в службу поддержки.")
        return

    status = session_data.get("status")
    candidate = session_data.get("candidate") or {}
    candidate_name = candidate.get("full_name", "Уважаемый кандидат")

    # ── Сценарий 1: Статус 'Ожидание скрининга' (Приветствие и ПДн) ────────────
    if status == "Ожидание скрининга":
        st.success(f"👋 Добро пожаловать, **{candidate_name}**!")
        st.write("Перед началом собеседования прослушайте краткое приветствие:")

        audio_bytes = decode_base64_audio(session_data.get("greeting_audio_base64"))
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")

        st.divider()
        st.subheader("📄 Согласие на обработку персональных данных (152-ФЗ)")
        pdn_text = session_data.get("pdn_text", "")
        st.info(pdn_text)

        col_agree, col_decline = st.columns(2)
        with col_agree:
            if st.button("✅ Согласен с условиями (Начать опрос)", type="primary", use_container_width=True):
                with st.spinner("Фиксация согласия и запуск сессии..."):
                    res, post_err = client.submit_pdn(active_token, accept_pdn=True)
                    if post_err:
                        st.error(post_err)
                    else:
                        st.success("Согласие принято! Переходим к вопросам...")
                        st.rerun()

        with col_decline:
            if st.button("❌ Отказаться от обработки ПДн", use_container_width=True):
                with st.spinner("Регистрация отказа..."):
                    res, post_err = client.submit_pdn(active_token, accept_pdn=False)
                    if post_err:
                        st.error(post_err)
                    else:
                        st.warning("Вы отказались от обработки ПДн.")
                        st.rerun()
        return

    # ── Сценарий 2: Отказ от ПДн (Терминальный статус) ─────────────────────────
    if status == "Отказ от обработки ПДн":
        st.error("⛔ Прохождение скрининга прервано: отказ от обработки персональных данных.")
        st.write("Согласно 152-ФЗ, мы не можем проводить аудиозапись и обработку ответов без вашего согласия.")
        return

    # ── Сценарий 3: Скрининг уже завершён или на проверке ─────────────────────
    if status in ("ИИ оценка", "HR оценка", "Отзыв ЛПР", "Приглашение на второй этап", "Отказ по скринингу"):
        st.info(f"ℹ️ Ваше интервью уже завершено. Текущий статус заявки: **{status}**.")
        st.write("Спасибо за участие! Наши специалисты свяжутся с вами по указанным контактам.")
        return

    # ── Сценарий 4: Активный процесс скрининга ('Процесс скрининга') ──────────
    if status == "Процесс скрининга":
        st.subheader(f"Кандидат: {candidate_name}")

        # Получаем текущий неотвеченный вопрос
        q_data, q_err = client.get_next_question(active_token)
        if q_err:
            st.error(f"Ошибка получения вопроса: {q_err}")
            return

        is_finished = q_data.get("finished", False)

        if not is_finished:
            q_id = q_data.get("question_id")
            q_text = q_data.get("question_text", "")
            total = q_data.get("total_questions", 1)
            answered = q_data.get("answered_count", 0)

            # Прогресс-бар
            progress_ratio = min(max(answered / max(total, 1), 0.0), 1.0)
            st.progress(progress_ratio, text=f"Вопрос {answered + 1} из {total}")

            # Карточка вопроса
            st.markdown(f"### ❓ Вопрос №{q_id}")
            st.markdown(f"> **{q_text}**")

            # Аудио вопроса от TTS
            q_audio = decode_base64_audio(q_data.get("question_audio_base64"))
            if q_audio:
                st.write("🔊 Озвучка вопроса:")
                st.audio(q_audio, format="audio/wav")

            st.divider()
            st.write("🎤 **Запишите ваш голосовой ответ:**")

            # Поддерживаем два способа ввода: прямой микрофон и загрузку файла
            recorded_audio = None
            if hasattr(st, "audio_input"):
                recorded_audio = st.audio_input("Нажмите кнопку записи и ответьте на вопрос")

            uploaded_file = st.file_uploader(
                "Или прикрепите аудиофайл с ответом (WAV, MP3, OGG)",
                type=["wav", "mp3", "ogg", "m4a"],
                key=f"file_up_{q_id}",
            )

            # Определяем, какой источник аудио выбран
            audio_source = recorded_audio or uploaded_file

            if st.button("📤 Отправить ответ", type="primary", use_container_width=True):
                if not audio_source:
                    # Если пользователь не записал микрофон, сгенерируем тестовый wav, чтобы можно было протестировать
                    st.warning("Пожалуйста, запишите ответ через микрофон или прикрепите аудиофайл!")
                else:
                    audio_bytes = audio_source.read()
                    filename = getattr(audio_source, "name", "candidate_answer.wav")
                    with st.spinner("Передаем аудио в STT (распознавание речи)..."):
                        ans_res, ans_err = client.submit_answer(
                            token=active_token,
                            question_id=q_id,
                            audio_bytes=audio_bytes,
                            filename=filename,
                        )
                        if ans_err:
                            st.error(f"Не удалось отправить ответ: {ans_err}")
                        else:
                            st.success("Ответ успешно сохранен и транскрибирован!")
                            st.rerun()

        else:
            # Все вопросы отвечены! Экран финализации
            st.success("🎉 Вы ответили на все вопросы интервью!")
            st.write("Нажмите кнопку ниже, чтобы завершить интервью и отправить его на интеллектуальную оценку.")

            if st.button("🏁 Завершить скрининг", type="primary", use_container_width=True):
                with st.spinner("Запускаем LLM-анализ ответов и формируем протокол..."):
                    fin_res, fin_err = client.finish_session(active_token)
                    if fin_err:
                        st.error(f"Ошибка завершения: {fin_err}")
                    else:
                        st.balloons()
                        st.success("Интервью успешно завершено!")
                        farewell_audio = decode_base64_audio(fin_res.get("farewell_audio_base64"))
                        if farewell_audio:
                            st.write("🔊 Прощальное сообщение:")
                            st.audio(farewell_audio, format="audio/wav")
                        st.info("Результаты переданы рекрутеру. Спасибо!")
                        st.rerun()
