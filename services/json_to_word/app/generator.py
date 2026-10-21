"""
Генератор .docx-отчётов по результатам HR-скрининга.

Использует библиотеку python-docx для создания структурированного документа Word.
Не требует шаблона — документ строится программно.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def generate_screening_report(data: dict, output_dir: str = "./reports") -> str:
    """
    Создаёт .docx-отчёт по результатам скрининга кандидата.

    Args:
        data: словарь с ключами:
            response_id, candidate_name, candidate_contact,
            vacancy_id, answers_json, ai_score, hr_score, hr_comment, lpr_decision
        output_dir: директория для сохранения файла отчёта

    Returns:
        Абсолютный путь к сгенерированному .docx-файлу.
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as exc:
        logger.error("python-docx не установлен: %s", exc)
        raise

    # Создаём директорию для отчётов, если она не существует
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    response_id = data.get("response_id", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screening_report_{response_id}_{timestamp}.docx"
    full_path = output_path / filename

    doc = Document()

    # ── Поля страницы ─────────────────────────────────────────────────────────
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # ── Заголовок отчёта ──────────────────────────────────────────────────────
    title = doc.add_heading("Отчёт по скринингу кандидата", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    doc.add_paragraph()

    # ── Раздел 1: Информация о кандидате ─────────────────────────────────────
    doc.add_heading("1. Информация о кандидате", level=1)
    table = doc.add_table(rows=4, cols=2)
    table.style = "Table Grid"

    def _cell(row: int, col: int, text: str, bold: bool = False):
        """Вспомогательная функция заполнения ячейки таблицы."""
        cell = table.cell(row, col)
        cell.text = text
        if bold:
            for run in cell.paragraphs[0].runs:
                run.bold = True

    _cell(0, 0, "ФИО кандидата", bold=True)
    _cell(0, 1, str(data.get("candidate_name", "—")))
    _cell(1, 0, "Контакт", bold=True)
    _cell(1, 1, str(data.get("candidate_contact", "—")))
    _cell(2, 0, "ID отклика", bold=True)
    _cell(2, 1, str(response_id))
    _cell(3, 0, "ID вакансии", bold=True)
    _cell(3, 1, str(data.get("vacancy_id", "—")))

    doc.add_paragraph()

    # ── Раздел 2: Итоговые оценки ─────────────────────────────────────────────
    doc.add_heading("2. Итоговые оценки", level=1)
    score_table = doc.add_table(rows=3, cols=2)
    score_table.style = "Table Grid"

    ai_score = data.get("ai_score")
    hr_score = data.get("hr_score")
    lpr_decision = data.get("lpr_decision")

    score_table.cell(0, 0).text = "AI оценка (из 10)"
    score_table.cell(0, 1).text = f"{ai_score:.2f}" if ai_score is not None else "—"
    score_table.cell(1, 0).text = "HR оценка (из 10)"
    score_table.cell(1, 1).text = f"{hr_score:.2f}" if hr_score is not None else "—"
    score_table.cell(2, 0).text = "Решение ЛПР"
    score_table.cell(2, 1).text = lpr_decision or "Ожидается"

    doc.add_paragraph()

    # ── Раздел 3: Комментарий HR ──────────────────────────────────────────────
    hr_comment = data.get("hr_comment")
    if hr_comment:
        doc.add_heading("3. Комментарий HR-специалиста", level=1)
        doc.add_paragraph(hr_comment)
        doc.add_paragraph()

    # ── Раздел 4: Вопросы и ответы кандидата ─────────────────────────────────
    answers_json = data.get("answers_json") or {}
    questions: list = answers_json.get("questions", [])

    if questions:
        doc.add_heading("4. Вопросы и ответы кандидата", level=1)
        for i, q in enumerate(questions, start=1):
            doc.add_heading(f"Вопрос {i}: {q.get('question_text', '—')}", level=2)

            # Эталонный ответ
            p = doc.add_paragraph()
            p.add_run("Эталонный ответ: ").bold = True
            p.add_run(q.get("reference_answer") or "—")

            # Транскрипт ответа кандидата
            p2 = doc.add_paragraph()
            p2.add_run("Ответ кандидата (транскрипт): ").bold = True
            p2.add_run(q.get("candidate_transcript") or "—")

            # AI-оценка по вопросу
            ai_q_score = q.get("ai_question_score")
            ai_comment = q.get("ai_comment")
            if ai_q_score is not None:
                p3 = doc.add_paragraph()
                p3.add_run(f"AI оценка: {ai_q_score}/10").bold = True
                if ai_comment:
                    doc.add_paragraph(f"AI комментарий: {ai_comment}")

            doc.add_paragraph()

    # ── Раздел 5: Итоговый AI-фидбек ─────────────────────────────────────────
    summary = answers_json.get("summary_ai_feedback")
    if summary:
        doc.add_heading("5. Итоговый AI-фидбек", level=1)
        doc.add_paragraph(summary)

    doc.save(str(full_path))
    logger.info("Отчёт сохранён: %s", full_path)
    return str(full_path)
