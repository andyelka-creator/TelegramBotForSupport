from app.schemas.common import TaskStatus


class StateMachineError(ValueError):
    pass


ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {TaskStatus.DATA_COLLECTED},
    TaskStatus.DATA_COLLECTED: {TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS: {TaskStatus.DONE_BY_SYSADMIN},
    TaskStatus.DONE_BY_SYSADMIN: {TaskStatus.CONFIRMED},
    TaskStatus.CONFIRMED: {TaskStatus.CLOSED},
    TaskStatus.CLOSED: set(),
    TaskStatus.CANCELLED: set(),
}


def can_transition(current: TaskStatus, new: TaskStatus) -> bool:
    if new == TaskStatus.CANCELLED:
        return current != TaskStatus.CANCELLED
    return new in ALLOWED_TRANSITIONS.get(current, set())


def validate_transition(current: TaskStatus, new: TaskStatus) -> None:
    if not can_transition(current, new):
        raise StateMachineError(f'Forbidden transition: {current} -> {new}')
