from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# =======================
# 1. USER SCHEMAS
# =======================
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

# =======================
# 2. PROPERTY SCHEMAS (TÀI SẢN)
# =======================
class PropertyBase(BaseModel):
    name: str
    address: str
    price: float
    description: Optional[str] = None
    # Thêm category để phân loại (real_estate, vehicle, item)
    category: str = "real_estate"

class PropertyCreate(PropertyBase):
    pass

class PropertyResponse(PropertyBase):
    id: int
    status: str
    owner_id: int
    class Config:
        from_attributes = True

# =======================
# 3. CONTRACT SCHEMAS (HỢP ĐỒNG)
# =======================
class ContractBase(BaseModel):
    start_date: date
    end_date: date

# Schema dùng cho Input (Dữ liệu từ Frontend gửi lên)
class ContractCreate(ContractBase):
    property_id: int
    tenant_email: str       # Dùng email để tìm user
    deposit_amount: float   # Tên biến khớp với frontend

# Schema dùng cho Output (Dữ liệu trả về từ Database)
class ContractResponse(ContractBase):
    id: int
    property_id: int
    tenant_id: int
    deposit: float          # Tên cột trong DB là deposit
    is_active: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# =======================
# 4. PAYMENT SCHEMAS (THANH TOÁN)
# =======================
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