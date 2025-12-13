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
    deposit: float

class ContractCreate(ContractBase):
    property_id: int
    tenant_id: int

class ContractResponse(ContractBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True