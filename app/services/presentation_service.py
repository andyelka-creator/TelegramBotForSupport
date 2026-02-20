import uuid

from app.db.models.task import Task
from app.schemas.common import TaskStatus, TaskType


TYPE_LABELS = {
    TaskType.ISSUE_NEW: 'Выпуск новой карты',
    TaskType.REPLACE_DAMAGED: 'Замена карты',
    TaskType.TOPUP: 'Пополнение',
}

STATUS_LABELS = {
    TaskStatus.CREATED: 'Создана',
    TaskStatus.DATA_COLLECTED: 'Данные получены от клиента',
    TaskStatus.IN_PROGRESS: 'В работе',
    TaskStatus.DONE_BY_SYSADMIN: 'Выполнено (сисадмин)',
    TaskStatus.CONFIRMED: 'Подтверждена',
    TaskStatus.CLOSED: 'Закрыта',
    TaskStatus.CANCELLED: 'Отменена',
}


def short_uuid(task_id: uuid.UUID) -> str:
    return str(task_id).split('-')[0]


def render_task_card(task: Task, guest_name: str | None = None, photo_attached: bool = False) -> str:
    lines = [
        f'Задача #{short_uuid(task.id)}',
        f'Тип: {TYPE_LABELS.get(task.type, task.type.value)}',
        f'Статус: {STATUS_LABELS.get(task.status, task.status.value)}',
    ]
    if guest_name:
        lines.append(f'Клиент: {guest_name}')
    if photo_attached:
        lines.append('Фото приложено: да')
    return '\n'.join(lines)


def creation_help(task_type: TaskType, link: str | None = None) -> str:
    task_name = TYPE_LABELS.get(task_type, task_type.value)
    if link:
        return f'Задача "{task_name}" создана.\nСсылка для клиента: {link}'
    return f'Задача "{task_name}" создана.'
