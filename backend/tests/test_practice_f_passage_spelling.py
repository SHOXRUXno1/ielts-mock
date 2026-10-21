"""The source spells the novelist's surname with a diaeresis, in UTF-8."""
import sys
from pathlib import Path

import pytest

scripts = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(scripts))
from repair_practice_f_t1_bronte import corrected, NEW_NAME, OLD_NAME


def test_passage_spelling_and_exact_one_character_patch():
    passage = (scripts / 'data/practice_f_t1/reading_p3.txt').read_text(encoding='utf-8')
    body = '\n'.join(line for line in passage.splitlines()[1:] if line.strip())
    assert body.count(NEW_NAME) == 1
    assert OLD_NAME not in body
    original = body.replace(NEW_NAME, OLD_NAME)
    assert corrected(original) == body
    assert corrected(body) == body
    assert len(original) == len(body)
    assert sum(a != b for a, b in zip(original, body)) == 1


def test_unreviewed_passage_change_is_not_overwritten():
    with pytest.raises(ValueError, match='audited original'):
        corrected('Other passage mentioning ' + OLD_NAME)
