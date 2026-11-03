"""
Кабинет ЛПР (Лица, принимающего решения — руководителя / нанимающего менеджера).
Реализует сценарий:
  1. Просмотр откликов со статусом 'Отзыв ЛПР'
  2. Сопоставление двух независимых оценок: AI_score и HR_score
  3. Скачивание сформированного .docx отчёта
  4. Вынесение финального вердикта (Приглашение / Отказ) и отправка обратной связи кандидату
  5. Просмотр архива ранее принятых решений
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


def render_lpr_view(client: APIClient):
    st.header("👔 Кабинет ЛПР (Лицо, принимающее решения)")
    st.caption("Финальное согласование кандидатов на основе двойной оценки (ИИ + HR)")

    # Получаем список всех откликов
    responses, err = client.get_all_responses()

    if err:
        st.error(f"Не удалось получить список откликов: {err}")
        return

    if not responses:
        st.warning("В базе данных пока нет откликов.")
        return

    # Фильтруем кандидатов: ожидающие решения и архив
    lpr_candidates = [r for r in responses if r.get("status") == "Отзыв ЛПР"]
    decided_candidates = [
        r for r in responses
        if r.get("status") in ("Приглашение на второй этап", "Отказ по скринингу")
    ]

    tab_pending, tab_archive = st.tabs([
        f"⏳ Требуют решения ({len(lpr_candidates)})",
        f"📁 Архив решений ({len(decided_candidates)})",
    ])

    # ── Вкладка 1: Кандидаты, ожидающие решения ───────────────────────────────
    with tab_pending:
        if not lpr_candidates:
            st.info("Нет кандидатов, ожидающих решения ЛПР.")
        else:
            candidate_options = {
                f"#{r['id']} — {(r.get('candidate') or {}).get('full_name', 'Кандидат')}": r["id"]
                for r in lpr_candidates
            }

            col_sel, col_ref = st.columns([3, 1])
            with col_sel:
                selected_label = st.selectbox(
                    "Выберите кандидата для рассмотрения:",
                    list(candidate_options.keys()),
                    key="sel_lpr_pending",
                )
                selected_response_id = candidate_options[selected_label]
            with col_ref:
                st.write("")
                st.write("")
                if st.button("🔄 Обновить", use_container_width=True, key="ref_lpr_pending"):
                    st.rerun()

            # Загружаем полные результаты
            with st.spinner("Загрузка результатов скрининга..."):
                full_data, f_err = client.get_full_result(selected_response_id)

            if f_err:
                st.error(f"Ошибка загрузки: {f_err}")
            else:
                resp_info = full_data.get("response") or {}
                scr_info = full_data.get("screening_result") or {}
                cand_info = resp_info.get("candidate") or {}

                # Информация о кандидате
                st.subheader(f"Кандидат: {cand_info.get('full_name')}")
                st.write(
                    f"📞 **Контакты:** {cand_info.get('contact_info')} | "
                    f"🔗 **Резюме:** {cand_info.get('resume_link') or 'Не прикреплено'}"
                )

                st.divider()
                st.markdown("### ⚖️ Двойная независимая оценка кандидата")

                col_ai, col_hr = st.columns(2)
                with col_ai:
                    ai_score = scr_info.get("ai_score")
                    score_text = f"{ai_score:.1f} / 10.0" if ai_score is not None else "Н/Д"
                    st.metric(label="🤖 Оценка ИИ (LLM)", value=score_text)
                    st.caption("Сравнение транскриптов ответов соискателя с эталонными ответами пула вопросов.")

                with col_hr:
                    hr_score = scr_info.get("hr_score")
                    hr_score_text = f"{hr_score:.1f} / 10.0" if hr_score is not None else "Н/Д"
                    st.metric(label="🧑‍💼 Экспертная оценка HR", value=hr_score_text)
                    st.caption("Независимый балл, выставленный рекрутером вслепую без знания оценки ИИ.")

                st.markdown("#### 💬 Характеристика от HR-специалиста:")
                st.info(scr_info.get("hr_comment") or "Комментарий отсутствует.")

                answers_json = scr_info.get("answers_json") or {}
                if answers_json.get("summary_ai_feedback"):
                    st.markdown("#### 🧠 Заключение языковой модели (LLM Summary):")
                    st.success(answers_json.get("summary_ai_feedback"))

                # Скачивание отчета
                st.divider()
                st.markdown("### 📄 Сводный отчёт (.docx)")
                report_bytes, rep_err = client.download_report(selected_response_id)
                if report_bytes:
                    cand_name = (cand_info.get("full_name") or "Кандидат").replace(" ", "_")
                    st.download_button(
                        label="📥 Скачать сформированный Word-отчет (.docx)",
                        data=report_bytes,
                        file_name=f"Screening_Report_{cand_name}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="secondary",
                        use_container_width=True,
                    )
                else:
                    st.caption("Файл отчета формируется сервисом JSONtoWord...")

                # Вынесение резолюции
                st.divider()
                st.markdown("### 🎯 Резолюция ЛПР")
                st.write("Выберите итоговое решение. Система автоматически сформирует персонализированное письмо и отправит его кандидату:")

                col_approve, col_reject = st.columns(2)
                with col_approve:
                    if st.button("🟢 Пригласить на второй этап", type="primary", use_container_width=True):
                        with st.spinner("Генерация письма и отправка уведомления кандидату..."):
                            dec_res, dec_err = client.submit_lpr_decision(selected_response_id, decision="approved")
                            if dec_err:
                                st.error(f"Ошибка сохранения: {dec_err}")
                            else:
                                st.balloons()
                                st.success("✅ Кандидат успешно приглашён на второй этап собеседования!")
                                st.info("Письмо-приглашение отправлено кандидату через NotificationsCenter.")
                                st.rerun()

                with col_reject:
                    if st.button("🔴 Отказать по скринингу", use_container_width=True):
                        with st.spinner("Генерация мотивированного отказа и отправка..."):
                            dec_res, dec_err = client.submit_lpr_decision(selected_response_id, decision="rejected")
                            if dec_err:
                                st.error(f"Ошибка сохранения: {dec_err}")
                            else:
                                st.warning("Кандидату отправлен мотивированный отказ.")
                                st.rerun()

    # ── Вкладка 2: Архив решений ──────────────────────────────────────────────
    with tab_archive:
        if not decided_candidates:
            st.info("Архив решений пока пуст.")
        else:
            archive_data = []
            for r in decided_candidates:
                c = r.get("candidate") or {}
                archive_data.append({
                    "ID отклика": r.get("id"),
                    "ФИО соискателя": c.get("full_name", "Не указано"),
                    "Контакты": c.get("contact_info", "Не указано"),
                    "Итоговое решение": r.get("status"),
                    "Дата создания": str(r.get("created_at", ""))[:19],
                })
            st.dataframe(pd.DataFrame(archive_data), use_container_width=True)

            # Просмотр деталей и скачивание отчета по кандидату из архива
            st.divider()
            st.subheader("🔍 Просмотр данных архивного кандидата")
            archived_options = {
                f"#{r['id']} — {(r.get('candidate') or {}).get('full_name', 'Кандидат')} ({r.get('status')})": r["id"]
                for r in decided_candidates
            }
            sel_arch_label = st.selectbox(
                "Выберите кандидата из архива:",
                list(archived_options.keys()),
                key="sel_arch_candidate",
            )
            sel_arch_id = archived_options[sel_arch_label]

            arch_full, arch_err = client.get_full_result(sel_arch_id)
            if not arch_err and arch_full:
                arch_scr = arch_full.get("screening_result") or {}
                col_a1, col_a2, col_a3 = st.columns(3)
                with col_a1:
                    st.metric("Решение", (arch_full.get("response") or {}).get("status", "—"))
                with col_a2:
                    st.metric("Оценка ИИ", f"{arch_scr.get('ai_score', 0):.1f} / 10.0")
                with col_a3:
                    st.metric("Оценка HR", f"{arch_scr.get('hr_score', 0):.1f} / 10.0")

                if arch_scr.get("hr_comment"):
                    st.markdown("**Характеристика HR:**")
                    st.info(arch_scr.get("hr_comment"))

                arch_rep, rep_err = client.download_report(sel_arch_id)
                if arch_rep:
                    st.download_button(
                        label="📥 Скачать Word-отчет кандидата из архива (.docx)",
                        data=arch_rep,
                        file_name=f"Archived_Report_{sel_arch_id}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_arch_{sel_arch_id}",
                    )
