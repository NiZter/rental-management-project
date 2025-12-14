from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import date, datetime

# ==================================================
# USER
# ==================================================
class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=100)


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str

    class Config:
        from_attributes = True


# ==================================================
# PROPERTY
# ==================================================
class PropertyBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=5, max_length=255)
    price: float = Field(gt=0)
    description: Optional[str] = Field(default=None, max_length=500)
    category: str = Field(default="real_estate", max_length=50)


class PropertyCreate(PropertyBase):
    owner_id: int = Field(gt=0)


class PropertyResponse(PropertyBase):
    id: int
    status: str
    owner_id: int

    class Config:
        from_attributes = True


# ==================================================
# CONTRACT
# ==================================================
class ContractBase(BaseModel):
    start_date: date
    end_date: date


class ContractCreate(ContractBase):
    property_id: int = Field(gt=0)
    tenant_email: EmailStr
    deposit: float = Field(ge=0)
    rental_type: Literal["daily", "monthly"] = "daily"


class ContractResponse(ContractBase):
    id: int
    property_id: int
    tenant_id: int
    total_price: float
    deposit: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================================================
# PAYMENT
# ==================================================
class PaymentBase(BaseModel):
    amount: float = Field(gt=0)
    payment_date: date
    note: Optional[str] = Field(default=None, max_length=255)


class PaymentCreate(PaymentBase):
    contract_id: int = Field(gt=0)


class PaymentResponse(PaymentBase):
    id: int
    status: str

    class Config:
        from_attributes = True
