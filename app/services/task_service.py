import json
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.task import Task
from app.repositories.audit import AuditRepository
from app.repositories.invite_tokens import InviteTokenRepository
from app.repositories.tasks import TaskRepository
from app.schemas.common import Role, TaskStatus, TaskType
from app.services.audit_service import AuditService
from app.services.invite_service import InviteService
from app.services.pds_payload_service import PDSPayloadService
from app.services.permission_service import PermissionService
from app.services.state_machine import validate_transition


@dataclass(slots=True)
class TransitionResult:
    task_id: uuid.UUID
    old_status: TaskStatus
    new_status: TaskStatus
    applied: bool


@dataclass(slots=True)
class CreateTaskResult:
    task: Task
    task_id: uuid.UUID
    task_type: TaskType
    invite_token: uuid.UUID | None = None


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tasks = TaskRepository(session)
        self.audit = AuditService(AuditRepository(session))
        self.payload_service = PDSPayloadService()
        self.permissions = PermissionService()
        self.invites = InviteService(InviteTokenRepository(session))

    async def create_task(self, task_type: TaskType, actor_id: int, initial_data: dict | None = None):
        result = await self.create_task_with_invite(task_type=task_type, actor_id=actor_id, initial_data=initial_data)
        return result.task

    async def create_task_with_invite(
        self,
        task_type: TaskType,
        actor_id: int,
        initial_data: dict | None = None,
        invite_expires_hours: int = 24,
    ) -> CreateTaskResult:
        async with self.session.begin():
            task = await self.tasks.create_task(task_type=task_type, created_by=actor_id)
            if initial_data:
                await self.tasks.set_data(task.id, initial_data)
            await self.audit.log(task.id, actor_id, 'TASK_CREATED', {'type': task_type.value})

            invite_token: uuid.UUID | None = None
            if task_type in {TaskType.ISSUE_NEW, TaskType.REPLACE_DAMAGED}:
                invite = await self.invites.create_token(task_id=task.id, expires_hours=invite_expires_hours)
                invite_token = invite.token

            return CreateTaskResult(task=task, task_id=task.id, task_type=task.type, invite_token=invite_token)

    async def fill_data(self, task_id: uuid.UUID, actor_id: int, payload: dict, auto_commit: bool = True):
        task = await self.tasks.get(task_id)
        if task is None:
            raise ValueError('Task not found')

        await self.tasks.set_data(task_id, payload)
        if task.status == TaskStatus.CREATED:
            validate_transition(task.status, TaskStatus.DATA_COLLECTED)
            task.status = TaskStatus.DATA_COLLECTED
        await self.audit.log(task.id, actor_id, 'TASK_DATA_FILLED', {'keys': sorted(payload.keys())})
        if auto_commit:
            await self.session.commit()
        return task

    async def transition(self, task_id: uuid.UUID, actor_id: int, actor_role: Role, new_status: TaskStatus) -> TransitionResult:
        self.permissions.ensure_can_transition(actor_role, new_status)

        async with self.session.begin():
            task = await self.tasks.get_for_update(task_id)
            if task is None:
                raise ValueError('Task not found')

            old_status = task.status
            if old_status == new_status:
                return TransitionResult(task_id=task.id, old_status=old_status, new_status=new_status, applied=False)

            validate_transition(old_status, new_status)
            task.status = new_status
            if new_status == TaskStatus.IN_PROGRESS and task.assigned_to is None:
                task.assigned_to = actor_id

            await self.audit.log(task.id, actor_id, 'STATUS_CHANGED', {'from': old_status.value, 'to': new_status.value})
            return TransitionResult(task_id=task.id, old_status=old_status, new_status=new_status, applied=True)

    async def change_status(self, task_id: uuid.UUID, actor_id: int, actor_role: Role, new_status: TaskStatus):
        result = await self.transition(task_id, actor_id, actor_role, new_status)
        return await self.tasks.get(result.task_id)

    async def build_pds_payload_json(self, task_id: uuid.UUID, actor_id: int) -> str:
        task = await self.tasks.get(task_id)
        if task is None:
            raise ValueError('Task not found')
        data_row = await self.tasks.get_data(task_id)
        data = data_row.json_data if data_row else {}

        payload = self.payload_service.build_payload(
            task_id=task.id,
            task_type=task.type,
            created_at=task.created_at,
            data=data,
        )
        await self.audit.log(task.id, actor_id, 'PDS_JSON_COPIED', {'operation': task.type.value})
        await self.session.commit()
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

    async def build_pds_steps(self, task_id: uuid.UUID, actor_id: int) -> str:
        task = await self.tasks.get(task_id)
        if task is None:
            raise ValueError('Task not found')
        data_row = await self.tasks.get_data(task_id)
        data = data_row.json_data if data_row else {}

        steps = self.payload_service.build_steps(task.type, data)
        await self.audit.log(task.id, actor_id, 'PDS_STEPS_COPIED', {'operation': task.type.value})
        await self.session.commit()
        return steps

    async def regenerate_invite(self, task_id: uuid.UUID, actor_id: int, expires_hours: int) -> uuid.UUID:
        async with self.session.begin():
            task = await self.tasks.get(task_id)
            if task is None:
                raise ValueError('Task not found')
            if task.type not in {TaskType.ISSUE_NEW, TaskType.REPLACE_DAMAGED}:
                raise ValueError('Task type does not support invite links')

            invite = await self.invites.regenerate_token(task_id=task_id, expires_hours=expires_hours)
            await self.audit.log(
                task_id=task_id,
                actor_id=actor_id,
                action='INVITE_TOKEN_REGENERATED',
                metadata={'token': str(invite.token)},
            )
            return invite.token

    async def get_active_invite(self, task_id: uuid.UUID) -> uuid.UUID | None:
        invite = await self.invites.get_latest_active_token(task_id)
        if invite is None:
            return None
        return invite.token
