"""SQLAlchemy ORM models."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Integer, String, Text, Numeric, TIMESTAMP, ForeignKey, JSON, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feishu_user_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Shanghai")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    finance_records: Mapped[list["FinanceRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    work_records: Mapped[list["WorkRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    conversation_contexts: Mapped[list["ConversationContext"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    conversation_turns: Mapped[list["ConversationTurn"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class FinanceRecord(Base):
    """Finance record model with primary and secondary categories."""
    __tablename__ = "finance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(10))  # 'income' | 'expense'
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    primary_category: Mapped[str] = mapped_column(String(50))  # Primary category
    secondary_category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Secondary category
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 现金/微信/支付宝/信用卡/其他
    merchant: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 商家名称
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否周期性
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)  # 标签数组
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    record_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="finance_records")


class WorkRecord(Base):
    """Work record model with task types."""
    __tablename__ = "work_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    record_date: Mapped[date] = mapped_column(Date)
    task_type: Mapped[str] = mapped_column(String(50))  # 开发/会议/文档/学习/管理/协作
    task_name: Mapped[str] = mapped_column(String(200))
    duration_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    value_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 项目关联（可选）
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # high/medium/low
    status: Mapped[str] = mapped_column(String(20), default="completed")  # todo/in_progress/completed/cancelled
    start_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)  # 开始时间
    end_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)  # 结束时间
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)  # 标签数组
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="work_records")


class ConversationContext(Base):
    """Conversation context for multi-turn dialogue."""
    __tablename__ = "conversation_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    current_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    state: Mapped[dict] = mapped_column(JSON, default={})
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="conversation_contexts")


class ConversationTurn(Base):
    """Individual conversation turn for dialogue history."""
    __tablename__ = "conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    user_input: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    response: Mapped[str] = mapped_column(Text)
    turn_metadata: Mapped[dict] = mapped_column(JSON, default={})

    # Relationship
    user: Mapped["User"] = relationship(back_populates="conversation_turns")
