"""Tests for pre-built evaluation presets."""

import pytest
from jev.models import ChoiceQuestion, NoulQuestion, ScoreQuestion
from jev.presets import PRESETS, get_preset_by_id


def test_presets_exist():
    assert len(PRESETS) >= 3


def test_all_presets_have_three_primitives():
    for p in PRESETS:
        assert p.id
        assert p.title
        assert p.description
        assert p.state is not None
        assert len(p.questions) >= 3

        types = {q.type for q in p.questions.values()}
        assert "noul" in types, f"Preset {p.id} missing Noul question"
        assert "choice" in types, f"Preset {p.id} missing Choice question"
        assert "score" in types, f"Preset {p.id} missing Score question"


def test_get_preset_by_id():
    p = get_preset_by_id("support_triage")
    assert p.id == "support_triage"

    with pytest.raises(ValueError):
        get_preset_by_id("non_existent_preset")
