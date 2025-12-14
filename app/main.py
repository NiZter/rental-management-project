from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse 
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from typing import List, Optional

from database import get_db, engine
from import models, schemas

# Tạo bảng trong DB (nếu chưa có)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RENTAL PRO - POSTGRES EDITION")

# --- CORS ---
origins = ["http://localhost", "http://localhost:5500", "http://127.0.0.1:5500", "*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root(): return {"message": "System is running with PostgreSQL"}

# ==================================================
# USER HELPER
# ==================================================
def get_or_create_admin(db: Session):
    admin = db.query(models.User).filter(models.User.id == 1).first()
    if not admin:
        admin = models.User(
            id=1,
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
    tenant = db.query(models.User).filter(models.User.email == email).first()
    if not tenant:
        username_gen = email.split('@')[0]
        if db.query(models.User).filter(models.User.username == username_gen).first():
            import random
            username_gen = f"{username_gen}_{random.randint(100, 999)}"

        tenant = models.User(
            email=email,
            username=username_gen,
            full_name=username_gen.capitalize(),
            hashed_password="default_password",
            role="user"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant

# --- USER API ---
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user: return db_user
    
    new_user = models.User(
        email=user.email, username=user.username, full_name=user.full_name,
        hashed_password=user.password + "hash", role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

# ==================================================
# PROPERTY
# ==================================================
@app.post("/properties/", response_model=schemas.PropertyResponse)
def create_property(prop: schemas.PropertyCreate, db: Session = Depends(get_db)):
    admin = get_or_create_admin(db)
    new_prop = models.Property(
        name=prop.name, address=prop.address, price=prop.price,
        description=prop.description, category=prop.category,
        owner_id=admin.id, status="available"
    )
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return new_prop

@app.get("/properties/", response_model=List[schemas.PropertyResponse])
def list_properties(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Property)
    if category: query = query.filter(models.Property.category == category)
    return query.all()

# ==================================================
# CONTRACT
# ==================================================
@app.post("/contracts/", response_model=schemas.ContractResponse)
def create_contract(data: schemas.ContractCreate, db: Session = Depends(get_db)):
    if data.start_date >= data.end_date:
        raise HTTPException(400, detail="Ngày kết thúc phải sau ngày bắt đầu")

    prop = db.query(models.Property).filter(models.Property.id == data.property_id).first()
    if not prop: raise HTTPException(404, detail="Tài sản không tồn tại")

    # Check trùng lịch (chỉ check các HĐ đang active)
    overlap = db.query(models.Contract).filter(
        models.Contract.property_id == data.property_id,
        models.Contract.status == "active",
        and_(models.Contract.start_date <= data.end_date, models.Contract.end_date >= data.start_date)
    ).first()
    if overlap:
        raise HTTPException(409, detail=f"Trùng lịch thuê (HĐ #{overlap.id})")

    tenant = get_or_create_tenant(db, data.tenant_email)

    # Tính tiền
    days = (data.end_date - data.start_date).days
    if data.rental_type == "monthly":
        total_price = max(1, (days + 15) // 30) * prop.price
    else:
        total_price = days * prop.price

    contract = models.Contract(
        property_id=data.property_id, tenant_id=tenant.id,
        start_date=data.start_date, end_date=data.end_date,
        total_price=total_price, deposit=data.deposit,
        status="active"
    )

    if data.start_date <= date.today() <= data.end_date:
        prop.status = "rented"
    
    db.add(contract)
    db.add(prop)
    db.commit()
    db.refresh(contract)
    return contract

@app.get("/contracts/", response_model=List[schemas.ContractResponse])
def list_contracts(db: Session = Depends(get_db)):
    return db.query(models.Contract).all()

# --- FEATURE: DOWNLOAD CONTRACT ---
@app.get("/contracts/{contract_id}/download")
def download_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract: raise HTTPException(404, detail="Không tìm thấy HĐ")
    
    owner = db.query(models.User).filter(models.User.id == 1).first()
    tenant = contract.tenant
    prop = contract.property

    content = f"""
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
-----------------------------

HỢP ĐỒNG THUÊ TÀI SẢN
(Mã số: {contract.id})

BÊN A (Chủ tài sản): {owner.full_name if owner else 'Admin'} - {owner.email if owner else ''}
BÊN B (Khách thuê):  {tenant.full_name} - {tenant.email}

1. Tài sản: {prop.name} ({prop.category})
   Địa chỉ: {prop.address}

2. Thời hạn: {contract.start_date} đến {contract.end_date}

3. Chi phí:
   - Tổng tiền thuê: {contract.total_price:,.0f} VNĐ
   - Tiền cọc: {contract.deposit:,.0f} VNĐ (Đã thu)

Hai bên cam kết thực hiện đúng điều khoản.
(Ký tên)
"""
    filename = f"Hop_dong_{contract.id}.txt"
    return PlainTextResponse(content, media_type="text/plain", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })

# ==================================================
# PAYMENT
# ==================================================
@app.post("/payments/", response_model=schemas.PaymentResponse)
def create_payment(pay: schemas.PaymentCreate, db: Session = Depends(get_db)):
    contract = db.query(models.Contract).filter(models.Contract.id == pay.contract_id).first()
    if not contract: raise HTTPException(404, detail="Hợp đồng không tồn tại")
    
    payment = models.Payment(
        contract_id=pay.contract_id, amount=pay.amount,
        payment_date=pay.payment_date, note=pay.note, is_paid=True
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@app.get("/contracts/{contract_id}/payments", response_model=List[schemas.PaymentResponse])
def list_payments(contract_id: int, db: Session = Depends(get_db)):
    return db.query(models.Payment).filter(models.Payment.contract_id == contract_id).all()