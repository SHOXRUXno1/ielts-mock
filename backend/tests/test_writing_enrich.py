"""Unit tests for Jumpinto-level writing result enrichment."""

from app.services.llm import (
    _WRITING_CRITERION_KEYS,
    _coerce_writing_criteria_to_int,
    _enrich_writing_result,
    _normalize_key_points,
    _normalize_optional_string,
    _normalize_sentence_analysis,
)


class TestNormalizeKeyPoints:
    def test_valid_items(self):
        raw = [
            {"point": "Peak at 20m in 1980", "covered": True},
            {"point": "Decline after 1990", "covered": False},
        ]
        assert _normalize_key_points(raw) == raw

    def test_skips_bad_items(self):
        raw = [
            {"point": "", "covered": True},
            {"covered": True},
            "not a dict",
            {"point": "  Valid  ", "covered": 1},
        ]
        out = _normalize_key_points(raw)
        assert len(out) == 1
        assert out[0]["point"] == "Valid"
        assert out[0]["covered"] is True

    def test_non_list(self):
        assert _normalize_key_points(None) == []
        assert _normalize_key_points({"point": "x"}) == []


class TestNormalizeSentenceAnalysis:
    def test_valid_and_filter(self):
        raw = [
            {
                "sentence": "The graph shows X.",
                "category": "hit_key_point",
                "comment": "Good overview",
                "reference": "Overview",
            },
            {
                "sentence": "Bad cat.",
                "category": "unknown_category",
                "comment": "nope",
            },
            {
                "sentence": "However, data wrong.",
                "category": "grammatical_error",
                "comment": "Subject-verb",
            },
        ]
        out = _normalize_sentence_analysis(raw)
        assert len(out) == 2
        assert out[0]["reference"] == "Overview"
        assert out[1]["category"] == "grammatical_error"
        assert "reference" not in out[1]


class TestEnrichWritingResult:
    def test_task1_keeps_new_fields(self):
        result = {
            "overall_band": 7.0,
            "key_points": [{"point": "Peak 20m", "covered": True}],
            "sentence_analysis": [
                {
                    "sentence": "A.",
                    "category": "hit_key_point",
                    "comment": "ok",
                }
            ],
            "overall_review": " Solid work. ",
            "optimized_composition": "Rewritten text.",
        }
        out = _enrich_writing_result(result, is_task1=True)
        assert len(out["key_points"]) == 1
        assert len(out["sentence_analysis"]) == 1
        assert out["overall_review"] == "Solid work."
        assert out["optimized_composition"] == "Rewritten text."

    def test_task2_drops_key_points(self):
        result = {
            "key_points": [{"point": "should drop", "covered": False}],
            "sentence_analysis": [
                {
                    "sentence": "A.",
                    "category": "linking_issue",
                    "comment": "weak link",
                }
            ],
            "overall_review": "",
            "optimized_composition": None,
        }
        out = _enrich_writing_result(result, is_task1=False)
        assert "key_points" not in out
        assert len(out["sentence_analysis"]) == 1
        assert "overall_review" not in out
        assert "optimized_composition" not in out

    def test_incomplete_json_fallback(self):
        """Missing Jumpinto fields must not raise; legacy shape preserved."""
        result = {
            "task_achievement": {"band": 6.5, "feedback": "ok"},
            "overall_band": 6.5,
            "strengths": ["Clear"],
            "improvements": [],
            "errors": [],
        }
        out = _enrich_writing_result(result, is_task1=True)
        assert out["overall_band"] == 6.5
        assert out["strengths"] == ["Clear"]
        assert "key_points" not in out
        assert "sentence_analysis" not in out
        assert "optimized_composition" not in out


class TestNormalizeOptionalString:
    def test_empty_and_valid(self):
        assert _normalize_optional_string("  hi  ") == "hi"
        assert _normalize_optional_string("") is None
        assert _normalize_optional_string(None) is None
        assert _normalize_optional_string(12) is None


class TestCoerceWritingCriteriaToInt:
    """IELTS: individual criteria must be whole bands 0-9."""

    def test_rounds_half_bands(self):
        # Python round uses banker's rounding: 6.5 -> 6, 7.5 -> 8, 8.5 -> 8.
        result = {
            "task_achievement": {"band": 6.5, "feedback": "a"},
            "coherence_cohesion": {"band": 7.4, "feedback": "b"},
            "lexical_resource": {"band": 8.5, "feedback": "c"},
            "grammatical_range": {"band": 7.6, "feedback": "d"},
        }
        out = _coerce_writing_criteria_to_int(result)
        assert out["task_achievement"]["band"] == 6  # banker's round 6.5 -> 6
        assert out["coherence_cohesion"]["band"] == 7
        assert out["lexical_resource"]["band"] == 8  # banker's round 8.5 -> 8
        assert out["grammatical_range"]["band"] == 8

    def test_integers_unchanged(self):
        result = {
            "task_achievement": {"band": 7, "feedback": "ok"},
            "coherence_cohesion": {"band": 6.0, "feedback": "ok"},
            "lexical_resource": {"band": 8, "feedback": "ok"},
            "grammatical_range": {"band": 5, "feedback": "ok"},
        }
        out = _coerce_writing_criteria_to_int(result)
        assert out["task_achievement"]["band"] == 7
        assert out["coherence_cohesion"]["band"] == 6
        assert out["lexical_resource"]["band"] == 8
        assert out["grammatical_range"]["band"] == 5

    def test_clamps_out_of_range(self):
        result = {
            "task_achievement": {"band": 9.7, "feedback": "high"},
            "coherence_cohesion": {"band": -1.2, "feedback": "low"},
            "lexical_resource": {"band": 10, "feedback": "over"},
            "grammatical_range": {"band": 0, "feedback": "zero"},
        }
        out = _coerce_writing_criteria_to_int(result)
        assert out["task_achievement"]["band"] == 9
        assert out["coherence_cohesion"]["band"] == 0
        assert out["lexical_resource"]["band"] == 9
        assert out["grammatical_range"]["band"] == 0

    def test_non_numeric_band_skipped(self):
        result = {
            "task_achievement": {"band": "n/a", "feedback": "bad"},
            "coherence_cohesion": {"band": 6.5, "feedback": "ok"},
        }
        out = _coerce_writing_criteria_to_int(result)
        assert out["task_achievement"]["band"] == "n/a"
        assert out["coherence_cohesion"]["band"] == 6

    def test_task_response_key(self):
        result = {"task_response": {"band": 7.4, "feedback": "essay"}}
        out = _coerce_writing_criteria_to_int(result)
        assert out["task_response"]["band"] == 7

    def test_task_band_from_integer_criteria(self):
        """Task band = round(avg * 2) / 2 from coerced integer criteria."""
        result = {
            "task_achievement": {"band": 7.2, "feedback": "a"},
            "coherence_cohesion": {"band": 7.1, "feedback": "b"},
            "lexical_resource": {"band": 6.4, "feedback": "c"},
            "grammatical_range": {"band": 6.3, "feedback": "d"},
            "overall_band": 9.0,  # Gemini lie — must be overwritten by caller
        }
        out = _coerce_writing_criteria_to_int(result)
        bands = [
            float(out[k]["band"])
            for k in _WRITING_CRITERION_KEYS
            if isinstance(out.get(k), dict) and out[k].get("band") is not None
        ]
        # After coercion: 7, 7, 6, 6 → avg 6.5
        assert bands == [7.0, 7.0, 6.0, 6.0]
        task_band = round(sum(bands) / len(bands) * 2) / 2
        assert task_band == 6.5
