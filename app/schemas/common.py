from enum import StrEnum


class Role(StrEnum):
    ADMIN = 'ADMIN'
    SYSADMIN = 'SYSADMIN'


class TaskType(StrEnum):
    ISSUE_NEW = 'ISSUE_NEW'
    REPLACE_DAMAGED = 'REPLACE_DAMAGED'
    TOPUP = 'TOPUP'


class TaskStatus(StrEnum):
    CREATED = 'CREATED'
    DATA_COLLECTED = 'DATA_COLLECTED'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE_BY_SYSADMIN = 'DONE_BY_SYSADMIN'
    CONFIRMED = 'CONFIRMED'
    CLOSED = 'CLOSED'
    CANCELLED = 'CANCELLED'


class ExecutionMode(StrEnum):
    ASSISTED = 'ASSISTED'
