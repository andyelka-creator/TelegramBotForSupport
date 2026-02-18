from app.schemas.common import Role, TaskStatus
from app.services.state_machine import StateMachineError


class PermissionDeniedError(StateMachineError):
    pass


class PermissionService:
    @staticmethod
    def ensure_can_transition(actor_role: Role, new_status: TaskStatus) -> None:
        if new_status == TaskStatus.DONE_BY_SYSADMIN and actor_role != Role.SYSADMIN:
            raise PermissionDeniedError('Only SYSADMIN can set DONE_BY_SYSADMIN')

        if new_status in {TaskStatus.CONFIRMED, TaskStatus.CLOSED, TaskStatus.CANCELLED} and actor_role != Role.ADMIN:
            raise PermissionDeniedError('Only ADMIN can set CONFIRMED/CLOSED/CANCELLED')
