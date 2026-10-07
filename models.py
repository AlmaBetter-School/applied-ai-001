"""Small, explicit contracts between the model, API and application."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Understanding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["order_status", "other"]
    order_id: str | None = Field(description="One 32-character order ID supplied by the user in this conversation, or null.")


class Order(BaseModel):
    order_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    status: Literal["approved", "canceled", "created", "delivered",
                    "invoiced", "processing", "shipped", "unavailable"]
    expected_delivery: date | None
    latest_update: str = Field(min_length=1, max_length=500)


class Resolution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tone: Literal["neutral", "empathetic"]
    next_step: Literal["track", "contact_support", "check_delivery"]


class Reply(BaseModel):
    message: str
    status: str
    order: Order | None = None
