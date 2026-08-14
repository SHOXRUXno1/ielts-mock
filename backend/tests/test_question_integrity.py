"""Guards against orphan questions that break take UI / scoring."""

from __future__ import annotations

from types import SimpleNamespace

from app.api.tests import _collect_publish_errors
from app.models.section import SectionType
from app.services.question_integrity import orphan_question_errors


def _q(**kwargs):
    defaults = {
        "task_number": None,
        "image_url": None,
        "content": {},
        "answer_key": {"correct": "A"},
        "question_type": "mcq",
        "question_group_id": "group-1",
        "order": 1,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _section(stype: SectionType, order: int, questions=None, question_groups=None):
    return SimpleNamespace(
        type=stype,
        order=order,
        questions=questions or [],
        question_groups=question_groups or [],
    )


def _writing_section():
    return SimpleNamespace(
        type=SectionType.WRITING,
        order=20,
        questions=[
            _q(task_number=1, image_url="/media/images/chart.png", content={"prompt": "Describe"}),
            _q(task_number=2, order=2, content={"prompt": "Discuss"}),
        ],
        question_groups=[],
    )


def _base_test(*, extra_reading_qs=None):
    reading_qs = extra_reading_qs or [_q(order=1, question_group_id="g1")]
    return SimpleNamespace(
        type="academic",
        sections=[
            _section(SectionType.LISTENING, 1, [_q(order=i) for i in range(1, 11)]),
            _section(SectionType.LISTENING, 2, [_q(order=i) for i in range(1, 11)]),
            _section(SectionType.LISTENING, 3, [_q(order=i) for i in range(1, 11)]),
            _section(SectionType.LISTENING, 4, [_q(order=i) for i in range(1, 11)]),
            _section(SectionType.READING, 10, reading_qs),
            _section(SectionType.READING, 11, []),
            _section(SectionType.READING, 12, []),
            _writing_section(),
            _section(SectionType.SPEAKING, 30, []),
            _section(SectionType.SPEAKING, 31, []),
            _section(SectionType.SPEAKING, 32, []),
        ],
    )


class TestOrphanQuestionErrors:
    def test_reports_null_group(self):
        orphan = _q(order=20, question_type="note_completion", question_group_id=None)
        errs = orphan_question_errors(
            SimpleNamespace(
                sections=[_section(SectionType.READING, 11, [orphan])],
            )
        )
        assert len(errs) == 1
        assert "no question group" in errs[0]
        assert "note_completion" in errs[0]

    def test_ok_when_grouped(self):
        errs = orphan_question_errors(
            SimpleNamespace(
                sections=[_section(SectionType.READING, 11, [_q()])],
            )
        )
        assert errs == []


class TestPublishRejectsOrphans:
    def test_publish_errors_include_orphan(self):
        orphan = _q(
            order=21,
            question_type="note_completion",
            question_group_id=None,
            answer_key={"correct": ["gates"]},
        )
        test = _base_test(extra_reading_qs=[_q(order=1), orphan])
        errors = _collect_publish_errors(test)
        assert any("no question group" in e for e in errors)
