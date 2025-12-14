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
    image_url: Optional[str] = None

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None

class PropertyResponse(PropertyBase):
    id: int
    status: str
    owner_id: int
    class Config: from_attributes = True

# --- Contract ---
class ContractBase(BaseModel):
    start_date: date
    end_date: date

class ContractCreate(ContractBase):
    property_id: int
    tenant_email: str
    deposit: float 
    rental_type: str = "daily" 

class ContractResponse(ContractBase):
    id: int
    property_id: int
    tenant_id: int
    deposit: float
    total_price: float
    status: str
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