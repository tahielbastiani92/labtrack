from django.core.exceptions import ValidationError

from .models import Sample

ALLOWED_TRANSITIONS = {
    Sample.Status.REGISTERED: {
        Sample.Status.PROCESSING,
        Sample.Status.STORED,
        Sample.Status.DISCARDED,
    },
    Sample.Status.PROCESSING: {
        Sample.Status.STORED,
        Sample.Status.CONSUMED,
        Sample.Status.DISCARDED,
    },
    Sample.Status.STORED: {
        Sample.Status.PROCESSING,
        Sample.Status.CONSUMED,
        Sample.Status.DISCARDED,
    },
    Sample.Status.CONSUMED: set(),
    Sample.Status.DISCARDED: set(),
}


def can_transition(current: str, new: str) -> bool:
    if current == new:
        return True
    return new in ALLOWED_TRANSITIONS.get(current, set())


def validate_status_transition(current: str, new: str) -> None:
    if not can_transition(current, new):
        raise ValidationError(
            f"Cannot change sample status from '{current}' to '{new}'."
        )
