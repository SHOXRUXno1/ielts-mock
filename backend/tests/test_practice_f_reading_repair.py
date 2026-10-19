"""Regression contracts from independently audited public source questions/keys."""
import copy
import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from app.models.answer import Answer
from app.models.question import QuestionType
from app.models.section import Section
from app.services.compound import extract_gap_ids, validate_compound_structure
from app.services.scoring import score_answer, scoring_slots_for_question
import repair_practice_f_reading as repair
from seed_practice_f_common import data_dir
from seed_practice_f_reading import _read_json, _source_structure, build_passage
from seed_practice_f_listening import choice_texts


def build(n):
    folder = data_dir(n)
    questions = _read_json(folder / "reading_questions.json")
    answers = _read_json(folder / "reading_answers.json")
    result = []
    for i in range(1, 4):
        section = Section(id=uuid.uuid4(), order=9+i)
        built = build_passage(n, i, section.id, questions, answers)
        result.append(repair.SectionRows(section, [repair.GroupRows(g, list(g.questions)) for g in built.groups]))
    return result


@pytest.mark.parametrize("n", range(1, 7))
def test_all_six_readings_have_40_slots_and_score_primary_keys(n):
    graph = build(n)
    numbered = repair.numbered(graph)
    assert sum(scoring_slots_for_question(q) for q, _, _ in numbered.values()) == 40
    for q, _, _ in numbered.values():
        correct = q.answer_key["correct"]
        answer = correct if q.question_type == QuestionType.MULTI_SELECT else correct[0] if isinstance(correct, list) else correct
        assert score_answer(q, Answer(response={"answer": answer})) == (scoring_slots_for_question(q), scoring_slots_for_question(q))
        assert score_answer(q, Answer(response={"answer": "__not_a_correct_answer__"}))[0] == 0
    for section in graph:
        for group in section.groups:
            shared = group.record.options_shared or {}
            if "variant" in shared:
                validate_compound_structure(group.record.question_type, shared)
                assert extract_gap_ids(shared) == [q.content["gap_id"] for q in group.questions]


@pytest.mark.parametrize("n", range(1, 7))
def test_reading_choice_labels_are_rendered_once_but_matching_labels_remain(n):
    for section in build(n):
        for group in section.groups:
            for question in group.questions:
                if question.question_type in {QuestionType.MCQ, QuestionType.MULTI_SELECT}:
                    assert question.content["options"] == choice_texts(question.content["options"])
            options = (group.record.options_shared or {}).get("options")
            if options and all("." in option for option in options):
                assert all(option.split(".", 1)[0].strip().isalpha() for option in options)


@pytest.mark.parametrize("n,number,answer", [
    (5, 29, "protective colouring"),
    (5, 31, "alter coloring"), (5, 31, "alter their colouring"), (5, 31, "alter colouring"),
    (5, 32, "on backgrounds"),
    (5, 34, "colorblind"), (5, 34, "colourblind"), (5, 34, "colour-blind"),
    (6, 26, "human"), (6, 27, "realistic"), (6, 27, "detailed realistic"), (6, 27, "detailed,realistic"),
])
def test_source_accepted_alternatives_are_not_rejected(n, number, answer):
    q = repair.numbered(build(n))[number][0]
    assert score_answer(q, Answer(response={"answer": answer})) == (1, 1)


def test_original_test5_question14_is_candle_classification_not_invented_caffeine_mcq():
    graph = build(5)
    numbered = repair.numbered(graph)
    q, group, section = numbered[14]
    assert section.record.order == 10
    assert q.question_type == QuestionType.MATCHING_FEATURES
    assert q.content["question"] == "was often used for trading in place of money"
    assert q.answer_key["correct"] == "B"
    assert group.record.options_shared["options"][1] == "B. Beeswax"
    assert numbered[15][2].record.order == 11
    assert len([n for n, (_, _, s) in numbered.items() if s.record.order == 10]) == 14
    assert all("What is the main idea of the passage?" != q.content.get("question") for q, _, _ in numbered.values())


@pytest.mark.parametrize("n,number,expected", [
    (1, 1, "They have sawlike jaws."),
    (1, 4, "They can be seen in fields at a distance from ponds and streams."),
    (1, 24, "Leather hoses for fire fighting were made by machine."),
    (1, 35, "Factory owners as well as workers died as a result of Luddite rioting."),
    (2, 1, "When did Viking warriors raid an abbey on the coast of England?"),
    (2, 17, "There is a tendency for dyslexia between twins."),
    (2, 34, "a theory explaining the presence of iridium beneath Earth's surface"),
])
def test_restored_source_wording(n, number, expected):
    q = repair.numbered(build(n))[number][0]
    assert q.content.get("statement", q.content.get("question")) == expected


@pytest.mark.parametrize("n,number,phrases", [
    (1, 7, ["When they are almost fully grown, they leave the water."]),
    (2, 6, ["Other groups of Vikings raided areas of Portugal and Spain.", "After settling in northwest Russia, they expanded their territories toward the south."]),
    (5, 28, ["There are four different types of camouflage.", "However, not all animals can easily change their appearance.", "Therefore, the predator has a hard time targeting one animal out of a group."]),
    (6, 1, ["The reproduction of plants occurs in different ways.", "Some plants pollinate themselves."]),
])
def test_complete_summary_context_not_short_fragments(n, number, phrases):
    _, group, _ = repair.numbered(build(n))[number]
    shared = group.record.options_shared
    assert shared["variant"] == "summary"
    text = " ".join(s.get("value", "") for p in shared["paragraphs"] for s in p["segments"])
    for phrase in phrases:
        assert phrase in text


def test_original_chart_and_theory_note_structure_preserved():
    chart = repair.numbered(build(1))[14][1]
    assert chart.record.question_type == QuestionType.TABLE_COMPLETION
    assert chart.record.options_shared["headers"] == ["Cause", "Effect"]
    assert len(chart.record.options_shared["rows"]) == 7
    notes = repair.numbered(build(2))[27][1].record.options_shared
    assert [s["heading"] for s in notes["sections"]] == ["Catastrophe Theory", "Gradualist Theory"]
    assert extract_gap_ids(notes) == [f"q{n}" for n in range(27, 33)]


def test_source_structure_rejects_omitted_reordered_and_duplicate_blanks():
    group = {"type": "completion", "instruction": "NO MORE THAN TWO WORDS", "questions": [1, 2]}
    for paragraphs in (["{{1}}"], ["{{2}} {{1}}"], ["{{1}} {{1}} {{2}}"]):
        with pytest.raises(ValueError):
            _source_structure({**group, "paragraphs": paragraphs}, None)


def test_idempotent_repair_has_no_updates():
    graph = build(5)
    plan = repair.plan_repair(5, graph, copy.deepcopy(graph))
    assert plan.updates == []
    assert plan.empty_groups == []


def test_unreviewed_drift_refuses_overwrite():
    desired = build(5)
    current = copy.deepcopy(desired)
    repair.numbered(current)[14][0].content = {"question": "unreviewed edit"}
    with pytest.raises(ValueError, match="audited baseline"):
        repair.plan_repair(5, current, desired)


def test_plan_keeps_question_identity_and_does_not_mutate_during_planning(monkeypatch):
    current = build(1)
    desired = copy.deepcopy(current)
    q = repair.numbered(current)[1][0]
    q.content = {"question": "old abbreviated wording"}
    before = repair.fingerprint(current)
    monkeypatch.setitem(repair.AUDITED_BEFORE, 1, before)
    ids = [row.id for row, _, _ in repair.numbered(current).values()]
    plan = repair.plan_repair(1, current, desired)
    assert repair.fingerprint(current) == before
    assert len(plan.updates) == 1
    assert plan.updates[0].record.id == ids[0]
    assert "id" not in plan.updates[0].fields
    for update in plan.updates:
        for name, val in update.fields.items():
            setattr(update.record, name, val)
    assert repair.fingerprint(current) == repair.fingerprint(desired)
    assert [row.id for row, _, _ in repair.numbered(current).values()] == ids


def test_active_attempt_aborts_before_backup_or_assignments(monkeypatch, tmp_path):
    current = build(1)
    desired = copy.deepcopy(current)
    repair.numbered(current)[1][0].content = {"question": "old"}
    before = repair.fingerprint(current)
    monkeypatch.setitem(repair.AUDITED_BEFORE, 1, before)
    monkeypatch.setattr(repair, "load_graph", AsyncMock(return_value=current))
    monkeypatch.setattr(repair, "desired_graph", AsyncMock(return_value=desired))
    monkeypatch.setattr(repair, "unfinished_count", AsyncMock(return_value=1))
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock())
    backup = tmp_path / "backup.json"
    # All awaits are immediate AsyncMocks. Drive this negative preflight directly:
    # it must raise before assigning fields or scheduling any real I/O.
    operation = repair.repair(db, apply=True, backup=backup)
    try:
        with pytest.raises(ValueError, match="unfinished attempts"):
            operation.send(None)
    finally:
        operation.close()
    assert repair.fingerprint(current) == before
    assert not backup.exists()
    db.add.assert_not_called()
    db.delete.assert_not_called()
    db.commit.assert_not_called()


def test_backup_never_overwrites(tmp_path):
    path = tmp_path / "backup.json"
    repair.write_backup(path, {"original": True})
    with pytest.raises(FileExistsError):
        repair.write_backup(path, {"original": False})
    assert '"original": true' in path.read_text()


def test_in_place_sql_rehearsal_retains_historical_answers_and_is_idempotent(monkeypatch, tmp_path):
    """Exercise real ORM/FKs in isolated SQLite; PostgreSQL row locks are not simulated."""
    from sqlalchemy import create_engine, select, text
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.ext.compiler import compiles, deregister
    from sqlalchemy.orm import Session
    from app.models.attempt import Attempt
    from app.models.base import Base
    from app.models.question import Question
    from app.models.question_group import QuestionGroup
    from app.models.test import Test as TestModel
    from app.models.user import User

    compiles(JSONB, "sqlite")(lambda _type, _compiler, **_kw: "JSON")
    engine = create_engine("sqlite:///:memory:")
    try:
        tables = [m.__table__ for m in (User, TestModel, Section, QuestionGroup, Question, Attempt, Answer)]
        Base.metadata.create_all(engine, tables=tables)
        with Session(engine, expire_on_commit=False) as db:
            db.execute(text("PRAGMA foreign_keys=ON"))
            # This constraint is added by Alembic, not declared on the ORM model.
            # Reproduce it so SQL flush ordering is tested, not just final values.
            db.execute(text('CREATE UNIQUE INDEX uq_question_group_order ON questions (question_group_id, "order")'))
            original_q14_id = None
            for n in repair.AUDITED_BEFORE:
                graph = build(n)
                if n == 5:
                    q14, classification, p1 = repair.numbered(graph)[14]
                    p2 = graph[1]
                    classification.questions.remove(q14)
                    for g in p2.groups:
                        g.record.order += 1
                        for q in g.questions:
                            q.order += 1
                    obsolete = QuestionGroup(id=uuid.uuid4(), section_id=p2.record.id, order=1,
                                             question_type="mcq", instruction="Old inserted MCQ")
                    q14.section_id = p2.record.id
                    q14.question_group_id = obsolete.id
                    q14.order = 1
                    q14.question_type = "mcq"
                    q14.content = {"question": "What is the main idea of the passage?", "options": ["A. old", "B. old", "C. old"]}
                    p2.groups.insert(0, repair.GroupRows(obsolete, [q14]))
                    original_q14_id = q14.id
                    monkeypatch.setitem(repair.AUDITED_BEFORE, 5, repair.fingerprint(graph))
                test = TestModel(id=uuid.uuid4(), title=f"Test {n}", book_slug="practice-set-f", test_number=n)
                db.add(test)
                db.flush()
                # Fresh ORM rows: relationships must be unloaded, just like the CLI.
                for s in repair.payload(graph, include_ids=True):
                    sid = uuid.UUID(s["id"])
                    db.add(Section(id=sid, test_id=test.id, type="reading", order=s["order"]))
                    db.flush()
                    for g in s["groups"]:
                        gid = uuid.UUID(g["id"])
                        db.add(QuestionGroup(id=gid, section_id=sid, order=g["order"], question_type=g["type"],
                                             instruction=g["instruction"], options_shared=g["options_shared"]))
                        db.flush()
                        for q in g["questions"]:
                            db.add(Question(id=uuid.UUID(q["id"]), section_id=sid, question_group_id=gid,
                                            order=q["order"], question_type=q["type"], content=q["content"], answer_key=q["answer_key"]))
                db.flush()
                if n == 5:
                    attempt = Attempt(id=uuid.uuid4(), test_id=test.id, mode="single_section", practice_section_type="reading",
                                      status="auto_scored", reading_raw=25, reading_band=6.0, practice_correct=25, practice_total=40)
                    db.add(attempt)
                    db.flush()
                    saved_answer = Answer(id=uuid.uuid4(), attempt_id=attempt.id, question_id=original_q14_id,
                                          response={"answer": "A"}, is_correct=False, score=0)
                    db.add(saved_answer)
            db.commit()
            db.expunge_all()
            old_ids = set(db.scalars(select(Question.id)))
            answer_id, attempt_id = saved_answer.id, attempt.id

            class ImmediateSession:
                async def execute(self, statement):
                    if str(statement).startswith("SET LOCAL"):
                        return None  # Only PostgreSQL lock/time limits; no content SQL skipped.
                    return db.execute(statement)

                async def flush(self):
                    db.flush()

                async def delete(self, row):
                    db.delete(row)

                async def commit(self):
                    db.commit()

                async def rollback(self):
                    db.rollback()

            def drive(operation):
                try:
                    operation.send(None)
                except StopIteration as done:
                    return done.value
                finally:
                    operation.close()
                pytest.fail("Unexpected asynchronous I/O in an isolated SQLite rehearsal")

            updates = drive(repair.repair(ImmediateSession(), apply=True, backup=tmp_path / "before.json"))
            assert updates > 0
            assert set(db.scalars(select(Question.id))) == old_ids
            assert db.get(Answer, answer_id).question_id == original_q14_id
            assert db.get(Answer, answer_id).response == {"answer": "A"}
            assert db.get(Answer, answer_id).is_correct is False
            assert db.get(Answer, answer_id).score == 0
            assert db.get(Attempt, attempt_id).reading_raw == 25
            assert db.get(Attempt, attempt_id).reading_band == 6.0
            assert drive(repair.repair(ImmediateSession(), apply=False)) == 0
    finally:
        engine.dispose()
        deregister(JSONB)
