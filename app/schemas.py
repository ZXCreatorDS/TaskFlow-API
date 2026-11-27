from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

Role = Literal["operator", "admin"]
TaskStatus = Literal["open", "in_progress", "done"]
TaskPriority = Literal["low", "medium", "high"]
HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$")]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserCreate(InputModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=255)
    role: Role = "operator"


class UserUpdate(InputModel):
    email: EmailStr | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: Role | None = None

    @field_validator("email", "display_name", "role")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value


class UserRead(ORMModel):
    id: int
    email: EmailStr
    display_name: str
    role: Role
    created_at: datetime


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
class ProjectCreate(InputModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectUpdate(InputModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value


class ProjectRead(ORMModel):
    id: int
    name: str
    description: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------
class LabelCreate(InputModel):
    name: str = Field(min_length=1, max_length=64)
    color: HexColor = "#6b7280"


class LabelUpdate(InputModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    color: HexColor | None = None

    @field_validator("name", "color")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value


class LabelRead(ORMModel):
    id: int
    name: str
    color: HexColor


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
class TaskCreate(InputModel):
    project_id: int
    assignee_id: int | None = None
    label_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = "open"
    priority: TaskPriority = "medium"


class TaskUpdate(InputModel):
    project_id: int | None = None
    assignee_id: int | None = None
    label_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None

    @field_validator("project_id", "title", "status", "priority")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value


class TaskRead(ORMModel):
    id: int
    project_id: int
    assignee_id: int | None
    label_id: int | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------
class CommentCreate(InputModel):
    task_id: int
    author_id: int
    body: str = Field(min_length=1)

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("body must not be empty")
        return value


class CommentUpdate(InputModel):
    task_id: int | None = None
    author_id: int | None = None
    body: str | None = Field(default=None, min_length=1)

    @field_validator("task_id", "author_id")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("body must not be empty")
        return value


class CommentRead(ORMModel):
    id: int
    task_id: int
    author_id: int
    body: str
    created_at: datetime
