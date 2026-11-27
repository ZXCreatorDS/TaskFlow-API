from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint("role IN ('operator', 'admin')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="operator"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    comments: Mapped[list[Comment]] = relationship(
        back_populates="author", passive_deletes=True
    )
    tasks: Mapped[list[Task]] = relationship(
        back_populates="assignee", passive_deletes=True
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tasks: Mapped[list[Task]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Label(Base):
    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint("name", name="uq_labels_name"),
        CheckConstraint(
            "length(color) = 7 AND substr(color, 1, 1) = '#'",
            name="ck_labels_color_format",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str] = mapped_column(
        String(7), nullable=False, server_default="#6b7280"
    )

    tasks: Mapped[list[Task]] = relationship(
        back_populates="label", passive_deletes=True
    )


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'done')",
            name="ck_tasks_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name="ck_tasks_priority",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    label_id: Mapped[int | None] = mapped_column(
        ForeignKey("labels.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="open"
    )
    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="medium"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    project: Mapped[Project] = relationship(back_populates="tasks")
    assignee: Mapped[User | None] = relationship(back_populates="tasks")
    label: Mapped[Label | None] = relationship(back_populates="tasks")
    comments: Mapped[list[Comment]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "length(trim(body)) > 0",
            name="ck_comments_body_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    task: Mapped[Task] = relationship(back_populates="comments")
    author: Mapped[User] = relationship(back_populates="comments")
