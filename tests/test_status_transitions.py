import pytest

from app.schemas.common import TaskStatus
from app.services.state_machine import StateMachineError, validate_transition

pytestmark = pytest.mark.unit


def test_valid_status_transition_chain():
    validate_transition(TaskStatus.CREATED, TaskStatus.DATA_COLLECTED)
    validate_transition(TaskStatus.DATA_COLLECTED, TaskStatus.IN_PROGRESS)
    validate_transition(TaskStatus.IN_PROGRESS, TaskStatus.DONE_BY_SYSADMIN)
    validate_transition(TaskStatus.DONE_BY_SYSADMIN, TaskStatus.CONFIRMED)
    validate_transition(TaskStatus.CONFIRMED, TaskStatus.CLOSED)


def test_invalid_status_transition_raises():
    with pytest.raises(StateMachineError):
        validate_transition(TaskStatus.CREATED, TaskStatus.IN_PROGRESS)

    with pytest.raises(StateMachineError):
        validate_transition(TaskStatus.IN_PROGRESS, TaskStatus.CONFIRMED)
