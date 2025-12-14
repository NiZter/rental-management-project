from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from typing import List, Optional

from .database import get_db, engine
from . import models, schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RENTAL PRO - AUTO PILOT MODE")

# --- CORS ---
origins = ["http://localhost", "http://localhost:5500", "http://127.0.0.1:5500", "*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root(): return {"message": "System is running in Auto-Pilot Mode"}

# ==================================================
# USER & HELPER (HÀM PHỤ TRỢ)
# ==================================================
def get_or_create_admin(db: Session):
    """Tự động tìm hoặc tạo ông chủ ID=1"""
    admin = db.query(models.User).filter(models.User.id == 1).first()
    if not admin:
        admin = models.User(
            id=1, # Fix cứng ID 1 là chủ
            email="admin@rental.com",
            username="admin",
            full_name="Administrator",
            hashed_password="admin_secret",
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin

def get_or_create_tenant(db: Session, email: str):
    """Tự động tìm hoặc tạo khách thuê dựa trên email"""
    tenant = db.query(models.User).filter(models.User.email == email).first()
    if not tenant:
        # Tự tạo username từ email (vd: khach@gmail.com -> khach)
        username_gen = email.split('@')[0]
        # Check trùng username thì thêm số ngẫu nhiên (đơn giản hóa cho demo)
        if db.query(models.User).filter(models.User.username == username_gen).first():
            import random
            username_gen = f"{username_gen}_{random.randint(100, 999)}"

        tenant = models.User(
            email=email,
            username=username_gen,
            full_name=username_gen.capitalize(),
            hashed_password="default_password", # Mật khẩu mặc định
            role="user"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant

# --- USER API ---
@app.get("/users/", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

# ==================================================
# PROPERTY
# ==================================================
@app.post("/properties/", response_model=schemas.PropertyResponse)
def create_property(prop: schemas.PropertyCreate, db: Session = Depends(get_db)):
    # 1. Đảm bảo Admin luôn tồn tại (Auto Create Admin)
    admin = get_or_create_admin(db)
    
    # 2. Tạo tài sản gán cho Admin
    new_prop = models.Property(
        name=prop.name,
        address=prop.address,
        price=prop.price,
        description=prop.description,
        category=prop.category,
        owner_id=admin.id, # Luôn gán cho Admin
        status="available"
    )
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return new_prop

@app.get("/properties/", response_model=List[schemas.PropertyResponse])
def list_properties(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Property)
    if category: query = query.filter(models.Property.category == category)
    if min_price is not None: query = query.filter(models.Property.price >= min_price)
    if max_price is not None: query = query.filter(models.Property.price <= max_price)
    if keyword: query = query.filter(models.Property.name.contains(keyword))
    return query.all()

# ==================================================
# CONTRACT
# ==================================================
@app.post("/contracts/", response_model=schemas.ContractResponse)
def create_contract(data: schemas.ContractCreate, db: Session = Depends(get_db)):
    # 1. Validate
    if data.start_date >= data.end_date:
        raise HTTPException(400, detail="Ngày kết thúc phải sau ngày bắt đầu")

    prop = db.query(models.Property).filter(models.Property.id == data.property_id).first()
    if not prop: raise HTTPException(404, detail="Tài sản không tồn tại")

    # 2. Check Overlap (Chống trùng lịch)
    overlap = db.query(models.Contract).filter(
        models.Contract.property_id == data.property_id,
        models.Contract.status == "active",
        and_(models.Contract.start_date <= data.end_date, models.Contract.end_date >= data.start_date)
    ).first()
    if overlap:
        raise HTTPException(409, detail=f"Trùng lịch! Đã có khách thuê từ {overlap.start_date} đến {overlap.end_date}")

    # 3. TỰ ĐỘNG TẠO KHÁCH (Auto Create Tenant)
    # Không cần báo lỗi 404 nữa, chưa có thì tạo luôn
    tenant = get_or_create_tenant(db, data.tenant_email)

    # 4. Tính tiền
    days = (data.end_date - data.start_date).days
    if data.rental_type == "monthly":
        total_price = max(1, (days + 15) // 30) * prop.price
    else:
        total_price = days * prop.price

    # 5. Lưu
    contract = models.Contract(
        property_id=data.property_id,
        tenant_id=tenant.id,
        start_date=data.start_date,
        end_date=data.end_date,
        total_price=total_price,
        deposit=data.deposit,
        status="active"
    )

    # Update UI status
    if data.start_date <= date.today() <= data.end_date:
        prop.status = "rented"
    
    try:
        db.add(contract)
        db.add(prop)
        db.commit()
        db.refresh(contract)
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=str(e))
        
    return contract

@app.get("/contracts/", response_model=List[schemas.ContractResponse])
def list_contracts(db: Session = Depends(get_db)):
    return db.query(models.Contract).all()

# --- PAYMENT ---
@app.post("/payments/", response_model=schemas.PaymentResponse)
def create_payment(pay: schemas.PaymentCreate, db: Session = Depends(get_db)):
    contract = db.query(models.Contract).filter(models.Contract.id == pay.contract_id).first()
    if not contract: raise HTTPException(404, detail="Hợp đồng không tồn tại")
    payment = models.Payment(contract_id=pay.contract_id, amount=pay.amount, payment_date=pay.payment_date, note=pay.note, status="paid")
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@app.get("/contracts/{contract_id}/payments", response_model=List[schemas.PaymentResponse])
def list_payments(contract_id: int, db: Session = Depends(get_db)):
    return db.query(models.Payment).filter(models.Payment.contract_id == contract_id).all()