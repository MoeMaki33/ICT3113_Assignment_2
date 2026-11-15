"""Unit tests for A2 cascade routing; no Ollama process required."""
from types import SimpleNamespace

import pytest

from app.services import cascade


def _setup(monkeypatch, setting):
    monkeypatch.setattr(
        cascade, "settings",
        SimpleNamespace(cascade_setting=setting, cascade_small_model="llama3.2:3b",
                        cascade_large_model="llama3.1:8b"),
    )
    request = SimpleNamespace(state=SimpleNamespace())
    return request


@pytest.mark.parametrize("setting,small_answer,expected_escalation", [
    ("A", "Mortgage", False),
    ("A", "Bank account or service", True),
    ("B", "Mortgage", False),
    ("B", "Bank account or service", False),
    ("B", "Credit reporting", True),
])
def test_frozen_settings(monkeypatch, setting, small_answer, expected_escalation):
    request = _setup(monkeypatch, setting)
    calls = []

    def fake_classify(narrative, model=None):
        calls.append((narrative, model))
        return small_answer if model == "llama3.2:3b" else "Credit card"

    monkeypatch.setattr(cascade, "classify_ticket", fake_classify)
    result = cascade.classify_with_cascade("This is a private ticket", request=request)
    assert result.escalated is expected_escalation
    assert request.state.escalated is expected_escalation
    assert request.state.first_model == "llama3.2:3b"
    assert request.state.final_model == ("llama3.1:8b" if expected_escalation else "llama3.2:3b")
    assert result.category == ("Credit card" if expected_escalation else small_answer)
    assert len(calls) == 1 + int(expected_escalation)
    assert calls[0][1] == "llama3.2:3b"
    if expected_escalation:
        assert calls[1][1] == "llama3.1:8b"
    assert result.first_stage_ms >= 0
    assert result.second_stage_ms >= 0


def test_invalid_setting_fails_closed(monkeypatch):
    request = _setup(monkeypatch, "C")
    monkeypatch.setattr(cascade, "classify_ticket", lambda *args, **kwargs: pytest.fail("must not call Ollama"))
    with pytest.raises(ValueError, match="CASCADE_SETTING"):
        cascade.classify_with_cascade("narrative", request=request)


def test_second_stage_failure_keeps_accurate_logging(monkeypatch):
    request = _setup(monkeypatch, "A")

    def fail_large(text, model):
        if model == "llama3.1:8b":
            raise RuntimeError("upstream failed")
        return "Debt collection"

    monkeypatch.setattr(cascade, "classify_ticket", fail_large)
    with pytest.raises(RuntimeError):
        cascade.classify_with_cascade("private narrative", request=request)
    assert request.state.escalated is True
    assert request.state.final_model == "llama3.1:8b"
    assert request.state.first_category == "Debt collection"
