import pytest

from apps.samples.rules import can_transition


@pytest.mark.parametrize(
    ("current", "new"),
    [
        ("registered", "processing"),
        ("registered", "stored"),
        ("registered", "discarded"),
        ("processing", "stored"),
        ("processing", "consumed"),
        ("processing", "discarded"),
        ("stored", "processing"),
        ("stored", "consumed"),
        ("stored", "discarded"),
        ("registered", "registered"),
        ("consumed", "consumed"),
    ],
)
def test_allowed_transitions(current, new):
    assert can_transition(current, new)


@pytest.mark.parametrize(
    ("current", "new"),
    [
        ("registered", "consumed"),
        ("processing", "registered"),
        ("stored", "registered"),
        ("consumed", "registered"),
        ("consumed", "stored"),
        ("discarded", "processing"),
    ],
)
def test_rejected_transitions(current, new):
    assert not can_transition(current, new)
