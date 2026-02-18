import uuid

from app.db.models.task import Task
from app.schemas.common import TaskType


def short_uuid(task_id: uuid.UUID) -> str:
    return str(task_id).split('-')[0]


def render_task_card(task: Task, guest_name: str | None = None, photo_attached: bool = False) -> str:
    lines = [
        f'Task #{short_uuid(task.id)}',
        f'Type: {task.type.value}',
        f'Status: {task.status.value}',
    ]
    if guest_name:
        lines.append(f'Guest: {guest_name}')
    if photo_attached:
        lines.append('Photo attached: yes')
    return '\n'.join(lines)


def creation_help(task_type: TaskType, link: str | None = None) -> str:
    if link:
        return f'{task_type.value} task created. Intake link: {link}'
    return f'{task_type.value} task created.'
