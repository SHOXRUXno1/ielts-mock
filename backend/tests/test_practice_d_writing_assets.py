"""Regression checks for the canonical Set D Writing Task 1 figures."""

from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree


ASSETS = Path(__file__).resolve().parents[1] / "scripts" / "assets"


def test_test1_freight_table_has_all_source_values() -> None:
    chart = ASSETS / "practice_d_t1_writing_task1_v2.svg"
    root = ElementTree.parse(chart).getroot()
    labels = [element.text for element in root.iter() if element.tag.endswith("text")]

    assert labels[:13] == [
        "Growth of global freight by 2050 and projected carbon emissions",
        "Freight volume", "[in billion tons/km]", "Growth", "[in %]",
        "CO₂ emission", "(in million tons)", "Growth", "[in %]",
        "2010", "2050", "2010", "2050",
    ]
    assert labels[13:] == [
        "Air", "191", "1 111", "482", "150", "767", "411",
        "Road", "6 388", "30 945", "384", "1 118", "4 519", "304",
        "Rail", "4 262", "19 126", "349", "62", "217", "250",
        "Sea", "60 053", "256 433", "327", "779", "2 630", "238",
        "70 894", "307 615", "334", "2 108", "8 132", "286",
    ]


def test_tests_2_to_4_keep_the_verified_figures() -> None:
    expected = {
        "practice_d_t2_writing_task1_v2.jpg": "c672a67494c1c84844b62a8f23e98a886b019194f6ca9ef56a273e8cd24262e3",
        "practice_d_t3_writing_task1.png": "2c18f90b307355b4aa9f6eb6fb02380f72b9bd001377a812b9bbddfd5045a309",
        "practice_d_t4_writing_task1.png": "3122a88ad1ab5ff8f9a2794c71a372b589b1c39c22aebedd4ac0ef35d1df3547",
    }
    for filename, digest in expected.items():
        assert sha256((ASSETS / filename).read_bytes()).hexdigest() == digest
