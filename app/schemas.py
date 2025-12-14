from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# --- User ---
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
class UserCreate(UserBase):
    password: str
class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str
    class Config: from_attributes = True

# --- Property ---
class PropertyBase(BaseModel):
    name: str
    address: str
    price: float
    description: Optional[str] = None
    category: str = "real_estate"
class PropertyCreate(PropertyBase):
    pass
class PropertyResponse(PropertyBase):
    id: int
    status: str
    owner_id: int
    class Config: from_attributes = True

# --- Contract (CẬP NHẬT) ---
class ContractBase(BaseModel):
    start_date: date
    end_date: date

class ContractCreate(ContractBase):
    property_id: int
    tenant_email: str
    deposit_amount: float
    # Thêm tùy chọn tính giá
    rental_type: str = "daily" # "daily" (Ngày) hoặc "monthly" (Tháng)

class ContractResponse(ContractBase):
    id: int
    property_id: int
    tenant_id: int
    deposit: float
    total_price: float # Trả về tổng tiền
    is_active: bool
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

# --- Payment ---
class PaymentBase(BaseModel):
    amount: float
    payment_date: date
    note: Optional[str] = None
class PaymentCreate(PaymentBase):
    contract_id: int
class PaymentResponse(PaymentBase):
    id: int
    is_paid: bool
    class Config: from_attributes = True