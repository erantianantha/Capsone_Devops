from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

CATEGORIES = [
    "Produce", "Dairy", "Meat", "Bakery", "Grains", "Canned",
    "Frozen", "Spices", "Snacks", "Beverages", "Other",
]


class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="Other", max_length=50)
    quantity: float = Field(default=1, ge=0)
    unit: str = Field(default="pcs", min_length=1, max_length=20)
    expiry_date: date | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=50)
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    expiry_date: date | None = None


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class Stats(BaseModel):
    total_items: int
    expiring_soon: int
    expired: int
    by_category: dict[str, int]
