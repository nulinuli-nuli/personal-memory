"""Pydantic schemas for data validation."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


# ============ Finance Schemas ============

class FinanceRecordCreate(BaseModel):
    """Schema for creating finance record."""
    type: str = Field(..., pattern="^(income|expense)$")
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    primary_category: str
    secondary_category: Optional[str] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None  # 现金/微信/支付宝/信用卡/其他
    merchant: Optional[str] = None  # 商家名称
    is_recurring: bool = False  # 是否周期性
    tags: Optional[List[str]] = None
    raw_text: Optional[str] = None
    record_date: date

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount has at most 2 decimal places."""
        return v.quantize(Decimal("0.01"))


class FinanceRecordResponse(BaseModel):
    """Schema for finance record response."""
    id: int
    type: str
    amount: Decimal
    primary_category: str
    secondary_category: Optional[str]
    description: Optional[str]
    payment_method: Optional[str]
    merchant: Optional[str]
    is_recurring: bool
    tags: Optional[List[str]]
    record_date: date
    created_at: datetime

    class Config:
        from_attributes = True


class FinanceRecordUpdate(BaseModel):
    """Schema for updating finance record."""
    type: Optional[str] = Field(None, pattern="^(income|expense)$")
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    primary_category: Optional[str] = None
    secondary_category: Optional[str] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    merchant: Optional[str] = None
    is_recurring: Optional[bool] = None
    tags: Optional[List[str]] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount has at most 2 decimal places."""
        if v is not None:
            return v.quantize(Decimal("0.01"))
        return v


# ============ Work Schemas ============

class WorkRecordCreate(BaseModel):
    """Schema for creating work record."""
    record_date: date
    task_type: str  # 开发/会议/文档/学习/管理/协作
    task_name: str
    duration_hours: Decimal = Field(..., gt=0, decimal_places=2)
    value_description: Optional[str] = None
    project_id: Optional[int] = None
    priority: str = "medium"  # high/medium/low
    status: str = "completed"  # todo/in_progress/completed/cancelled
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tags: Optional[List[str]] = None
    raw_text: Optional[str] = None

    @field_validator("duration_hours")
    @classmethod
    def validate_duration(cls, v):
        """Ensure duration has at most 2 decimal places."""
        return v.quantize(Decimal("0.01"))

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """Validate priority."""
        if v not in ["high", "medium", "low"]:
            raise ValueError("Priority must be one of: high, medium, low")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate status."""
        if v not in ["todo", "in_progress", "completed", "cancelled"]:
            raise ValueError("Status must be one of: todo, in_progress, completed, cancelled")
        return v


class WorkRecordResponse(BaseModel):
    """Schema for work record response."""
    id: int
    record_date: date
    task_type: str
    task_name: str
    duration_hours: Decimal
    value_description: Optional[str]
    project_id: Optional[int]
    priority: str
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    tags: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class WorkRecordUpdate(BaseModel):
    """Schema for updating work record."""
    task_type: Optional[str] = None
    task_name: Optional[str] = None
    duration_hours: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    value_description: Optional[str] = None
    project_id: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tags: Optional[List[str]] = None


# ============ Conversation Context Schemas ============

class ConversationTurnCreate(BaseModel):
    """Schema for creating conversation turn."""
    user_id: int
    user_input: str
    intent: Optional[str] = None
    domain: Optional[str] = None
    response: str
    turn_metadata: Optional[dict] = None


class ConversationTurnResponse(BaseModel):
    """Schema for conversation turn response."""
    id: int
    user_id: int
    timestamp: datetime
    user_input: str
    intent: Optional[str]
    domain: Optional[str]
    response: str
    turn_metadata: dict

    class Config:
        from_attributes = True


class ConversationContextResponse(BaseModel):
    """Schema for conversation context response."""
    id: int
    user_id: int
    current_intent: Optional[str]
    current_domain: Optional[str]
    state: dict
    updated_at: datetime

    class Config:
        from_attributes = True
