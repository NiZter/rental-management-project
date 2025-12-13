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

# --- Contract Schemas (ĐÃ SỬA LẠI CHO KHỚP) ---
class ContractBase(BaseModel):
    start_date: date
    end_date: date

# Schema dùng khi tạo (Input từ JS gửi lên)
class ContractCreate(ContractBase):
    property_id: int
    tenant_email: str       # Khớp với JS gửi email
    deposit_amount: float   # Khớp với JS gửi deposit_amount

# Schema dùng khi trả về (Output từ DB ra)
class ContractResponse(ContractBase):
    id: int
    property_id: int
    tenant_id: int
    deposit: float          # Trong DB tên cột là deposit
    is_active: bool
    
    class Config:
        from_attributes = True