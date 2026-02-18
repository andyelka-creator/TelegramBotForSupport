import uuid
from datetime import datetime

from pydantic import BaseModel


class InviteRead(BaseModel):
    token: uuid.UUID
    task_id: uuid.UUID
    expires_at: datetime
    used_at: datetime | None
