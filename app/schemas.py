from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# --- User Schemas ---
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
    class Config:
        from_attributes = True

# --- Property Schemas ---
class PropertyBase(BaseModel):
    name: str
    address: str
    price: float
    description: Optional[str] = None

class PropertyCreate(PropertyBase):
    pass

class PropertyResponse(PropertyBase):
    id: int
    status: str
    owner_id: int
    class Config:
        from_attributes = True

# --- Contract Schemas ---
class ContractBase(BaseModel):
    start_date: date
    end_date: date

class ContractCreate(ContractBase):
    property_id: int
    tenant_email: str
    deposit_amount: float

class ContractResponse(ContractBase):
    id: int
    property_id: int
    tenant_id: int
    deposit: float
    is_active: bool
    class Config:
        from_attributes = True

# --- Payment Schemas ---
class PaymentBase(BaseModel):
    amount: float
    payment_date: date
    note: Optional[str] = None

class PaymentCreate(PaymentBase):
    contract_id: int

class PaymentResponse(PaymentBase):
    id: int
    is_paid: bool
    class Config:
        from_attributes = True