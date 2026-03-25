from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.task import STATUS_LABEL_RU, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    status: TaskStatus = TaskStatus.pending
    priority: int = 0


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus | None = None
    priority: int | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TaskStatus
    priority: int
    created_at: datetime

    @computed_field
    @property
    def status_label(self) -> str:
        return STATUS_LABEL_RU[self.status]
