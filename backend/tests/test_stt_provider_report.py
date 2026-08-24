"""The arithmetic behind the engine report, checked against hand-made sittings.

The report exists to settle an argument about whether one engine hears worse than
the other, so its counts have to be right before anyone acts on them. The two
that matter most are the denominator — unlabelled turns from before the record
existed must never be silently attributed to an engine — and the split sittings,
since a candidate whose answers were shared between two models is the case the
report is really looking for.
"""

import uuid
from types import SimpleNamespace

from scripts.stt_provider_report import collect, render


def turn(role: str, text: str, provider: str | None = None, **stt) -> dict:
    entry: dict = {"role": role, "text": text, "phase": stt.pop("phase", "part1")}
    if provider:
        entry["stt"] = {"provider": provider, "latency_ms": 0, "reason": None, **stt}
    return entry


def sitting(*turns: dict, band: float | None = 6.5) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(), history_json=list(turns), overall_band=band
    )


class TestCounting:
    def test_turns_are_counted_against_the_engine_that_heard_them(self):
        report = collect(
            [
                sitting(
                    turn("candidate", "I live in Tashkent.", "groq"),
                    turn("examiner", "And do you work?"),
                    turn("candidate", "Yes, I am a student.", "gemini"),
                )
            ]
        )

        assert report.labelled_turns == 2
        assert report.by_provider["groq"].turns == 1
        assert report.by_provider["gemini"].turns == 1

    def test_the_examiner_is_not_a_candidate(self):
        report = collect([sitting(turn("examiner", "Where do you live?"))])

        assert report.labelled_turns == 0
        assert report.unlabelled_turns == 0

    def test_silence_and_near_silence_are_told_apart(self):
        report = collect(
            [
                sitting(
                    turn("candidate", "", "groq"),
                    turn("candidate", "(no speech detected)", "groq"),
                    turn("candidate", "Yes.", "groq"),
                    turn("candidate", "I have lived here all my life.", "groq"),
                )
            ]
        )

        tally = report.by_provider["groq"]
        assert (tally.turns, tally.empty, tally.short) == (4, 2, 1)

    def test_the_median_ignores_turns_that_never_timed_themselves(self):
        report = collect(
            [
                sitting(
                    turn("candidate", "One.", "groq", latency_ms=400),
                    turn("candidate", "Two.", "groq", latency_ms=800),
                    turn("candidate", "Three.", "groq", latency_ms=0),
                )
            ]
        )

        assert report.by_provider["groq"].median_latency_ms == 600

    def test_reasons_are_counted_only_when_given(self):
        report = collect(
            [
                sitting(
                    turn("candidate", "One.", "groq"),
                    turn("candidate", "Two.", "gemini", reason="groq_budget_spent"),
                    turn("candidate", "Three.", "gemini", reason="groq_budget_spent"),
                    turn("candidate", "Four.", "gemini", reason="groq_http_429"),
                )
            ]
        )

        assert report.reasons == {"groq_budget_spent": 2, "groq_http_429": 1}


class TestOlderSittingsAreNotAttributed:
    """An unlabelled turn is not a Groq turn."""

    def test_they_are_kept_out_of_the_denominator(self):
        report = collect(
            [
                sitting(turn("candidate", "Older answer.")),
                sitting(turn("candidate", "Newer answer.", "groq")),
            ]
        )

        assert report.labelled_turns == 1
        assert report.unlabelled_turns == 1
        assert "unknown" not in report.by_provider

    def test_a_wholly_unlabelled_sitting_is_counted_apart(self):
        report = collect([sitting(turn("candidate", "Older answer."))])

        assert report.unlabelled_sittings == 1
        assert report.labelled_sittings == 0

    def test_a_part_labelled_sitting_counts_as_labelled(self):
        """It started before the deploy and finished after it."""
        report = collect(
            [
                sitting(
                    turn("candidate", "Older answer."),
                    turn("candidate", "Newer answer.", "groq"),
                )
            ]
        )

        assert (report.labelled_sittings, report.unlabelled_sittings) == (1, 0)
        assert report.unlabelled_turns == 1


class TestSplitSittings:
    def test_one_engine_throughout_is_not_a_split(self):
        report = collect(
            [
                sitting(
                    turn("candidate", "One.", "groq"),
                    turn("candidate", "Two.", "groq"),
                )
            ]
        )

        assert report.split == []

    def test_two_engines_in_one_sitting_is_reported_with_its_band(self):
        report = collect(
            [
                sitting(
                    turn("candidate", "One.", "groq"),
                    turn("candidate", "Two.", "gemini"),
                    turn("candidate", "Three.", "gemini"),
                    band=5.5,
                )
            ]
        )

        assert len(report.split) == 1
        assert report.split[0].counts == {"groq": 1, "gemini": 2}
        assert report.split[0].band == 5.5


class TestRendering:
    def test_no_labels_yet_says_so_instead_of_showing_zeroes(self):
        text = "\n".join(
            render(collect([sitting(turn("candidate", "Older."))]), 30, False)
        )

        assert "No turn carries an engine label yet" in text
        assert "1 turn(s) across 1 sitting(s) predate the record." in text

    def test_a_clean_run_says_the_fallback_never_ran(self):
        text = "\n".join(
            render(collect([sitting(turn("candidate", "One.", "groq"))]), 30, False)
        )

        assert "The fallback never ran" in text

    def test_quiet_turns_are_listed_only_when_asked_for(self):
        report = collect([sitting(turn("candidate", "", "gemini"))])

        assert "nothing was heard" not in "\n".join(render(report, 30, False))
        assert "nothing was heard" in "\n".join(render(report, 30, True))
