from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.result_report import (
    NO_ANSWER,
    answer_outcome,
    band_descriptor,
    build_report_context,
    cefr_level,
    content_disposition,
    format_correct_answer,
    format_student_answer,
    render_report_html,
    render_report_pdf,
    report_filenames,
)


class TestBandLabels:
    def test_descriptor_matches_frontend(self):
        assert band_descriptor(None) is None
        assert band_descriptor(9) == "Expert"
        assert band_descriptor(7.5) == "Good"
        assert band_descriptor(3) == "Limited"

    def test_cefr_matches_frontend(self):
        assert cefr_level(None) is None
        assert cefr_level(8.5) == "C2"
        assert cefr_level(7) == "C1"
        assert cefr_level(5.5) == "B2"
        assert cefr_level(4) == "B1"
        assert cefr_level(3.5) == "A2"


class TestFormatStudentAnswer:
    def test_empty_and_missing(self):
        assert format_student_answer(None) == NO_ANSWER
        assert format_student_answer({}) == NO_ANSWER
        assert format_student_answer({"answer": ""}) == NO_ANSWER
        assert format_student_answer({"answer": None}) == NO_ANSWER

    def test_scalar_list_and_dict(self):
        assert format_student_answer({"answer": "hotel"}) == "hotel"
        assert format_student_answer({"answer": ["A", "C"]}) == "A, C"
        assert format_student_answer({"answer": {"item0": "A"}}) == "item0 → A"


class TestFormatCorrectAnswer:
    def test_accepted_answers(self):
        assert format_correct_answer({"accepted_answers": ["yes", "y"]}) == "yes | y"

    def test_correct_list_is_sorted(self):
        assert format_correct_answer({"correct": ["C", "A"]}) == "A | C"

    def test_legacy_answers(self):
        assert format_correct_answer({"answers": ["A", "B"]}) == "A | B"

    def test_dict_and_empty(self):
        assert format_correct_answer({"correct": {"a": "A", "b": "B"}}) == "A | B"
        assert format_correct_answer(None) == ""
        assert format_correct_answer({}) == ""


class TestAnswerOutcome:
    def test_skipped_vs_incorrect(self):
        assert answer_outcome({"response": {}, "is_correct": False}) == "skipped"
        assert answer_outcome({"response": {"answer": "x"}, "is_correct": False}) == "incorrect"
        assert answer_outcome({"response": {"answer": "x"}, "is_correct": True}) == "correct"


def _answer(
    *,
    section_id: str,
    section_type: str,
    order: int,
    number: int,
    student: str,
    correct: str,
    is_correct: bool,
):
    return SimpleNamespace(
        response={"answer": student} if student else {},
        is_correct=is_correct,
        question=SimpleNamespace(
            computed_number=number,
            computed_number_end=number,
            order=number,
            answer_key={"correct": correct},
        ),
        section=SimpleNamespace(id=section_id, type=section_type, order=order),
    )


def _minimal_detail(**overrides):
    data = {
        "test_title": "Cambridge IELTS 15 – Test 1",
        "status": "fully_scored",
        "started_at": datetime(2026, 1, 15, 8, 0, tzinfo=timezone.utc),
        "finished_at": datetime(2026, 1, 15, 10, 45, tzinfo=timezone.utc),
        "created_at": datetime(2026, 1, 15, 8, 0, tzinfo=timezone.utc),
        "overall_band": 6.5,
        "listening_band": 7.0,
        "reading_band": 6.5,
        "writing_band": 6.0,
        "speaking_band": None,
        "listening_raw": 30,
        "reading_raw": 27,
        "answers": [],
        "evaluation_jobs": [],
        "speaking_session": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class TestBuildReportContext:
    def test_missing_bands_do_not_crash(self):
        context = build_report_context(
            _minimal_detail(
                overall_band=None,
                listening_band=None,
                reading_band=None,
                writing_band=None,
                speaking_band=None,
                listening_raw=None,
                reading_raw=None,
            ),
            "Alibek",
        )
        assert context["student_name"] == "Alibek"
        assert context["overall"]["band_label"] == "—"
        assert context["writing"]["state"] == "not_attempted"
        assert context["speaking"]["state"] == "not_attempted"
        assert all(skill["band_label"] == "—" for skill in context["skills"])

    def test_groups_objective_answers_and_scoring_jobs(self):
        context = build_report_context(
            _minimal_detail(
                answers=[
                    _answer(
                        section_id="l1",
                        section_type="listening",
                        order=1,
                        number=1,
                        student="hotel",
                        correct="hotel",
                        is_correct=True,
                    ),
                    _answer(
                        section_id="l1",
                        section_type="listening",
                        order=1,
                        number=2,
                        student="",
                        correct="park",
                        is_correct=False,
                    ),
                ],
                evaluation_jobs=[
                    SimpleNamespace(
                        section_type="writing",
                        status="processing",
                        band_score=None,
                        result=None,
                    )
                ],
            ),
            "Alibek",
        )
        assert context["listening"][0]["label"] == "Part 1"
        assert context["listening"][0]["correct"] == 1
        assert context["listening"][0]["skipped"] == 1
        assert context["writing"]["state"] == "scoring"

    def test_writing_and_speaking_feedback(self):
        context = build_report_context(
            _minimal_detail(
                speaking_band=6.5,
                evaluation_jobs=[
                    SimpleNamespace(
                        section_type="writing",
                        status="done",
                        band_score=6.0,
                        result={
                            "tasks": {
                                "task_1": {
                                    "overall_band": 6.0,
                                    "word_count": 160,
                                    "text": "The chart shows...",
                                    "strengths": ["Clear overview"],
                                    "improvements": ["More data"],
                                    "task_achievement": {
                                        "band": 6,
                                        "feedback": "Covers the main features.",
                                    },
                                }
                            }
                        },
                    ),
                    SimpleNamespace(
                        section_type="speaking",
                        status="done",
                        band_score=6.5,
                        result={
                            "transcript": "Hello, my name is...",
                            "strengths": ["Fluent opening"],
                            "fluency_coherence": {
                                "band": 6.5,
                                "feedback": "Speaks at length.",
                            },
                        },
                    ),
                ],
            ),
            "Alibek",
        )
        assert context["writing"]["ready"] is True
        assert context["writing"]["tasks"][0]["title"] == "Task 1"
        assert context["writing"]["tasks"][0]["essay"] == "The chart shows..."
        assert context["speaking"]["ready"] is True
        assert context["speaking"]["transcript"].startswith("Hello")


class TestFilenames:
    def test_ascii_and_utf8_names(self):
        ascii_name, utf8_name = report_filenames(_minimal_detail())
        assert ascii_name == "ielts-result-2026-01-15.pdf"
        assert utf8_name.endswith("2026-01-15.pdf")
        header = content_disposition(ascii_name, utf8_name)
        assert 'filename="ielts-result-2026-01-15.pdf"' in header
        assert "filename*=UTF-8''" in header


class TestRender:
    def test_html_contains_title_and_empty_states(self):
        html = render_report_html(build_report_context(_minimal_detail(), "Alibek"))
        assert "Cambridge IELTS 15" in html
        assert "Alibek" in html
        assert "Not attempted" in html

    def test_pdf_bytes_start_with_header(self):
        context = build_report_context(_minimal_detail(), "Alibek")
        try:
            pdf = render_report_pdf(context)
        except Exception as exc:  # WeasyPrint needs system libraries
            pytest.skip(f"WeasyPrint system libraries not available: {exc}")
        assert pdf.startswith(b"%PDF-")
