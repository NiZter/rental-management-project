from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import date

# Import các module cùng thư mục
from . import models, schemas, database

app = FastAPI(title="Rental Management System (De Tai 17)")

# --- CẤU HÌNH CORS ---
origins = [
    "http://localhost",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tạo bảng database
models.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hệ thống quản lý nhà trọ (Rental) đang chạy ngon!"}

# --- API USER ---
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email này đăng ký rồi!")
    
    fake_hashed_password = user.password + "notreallyhashed"
    new_user = models.User(
        email=user.email, 
        username=user.username, 
        full_name=user.full_name,
        hashed_password=fake_hashed_password,
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/", response_model=List[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# --- API PROPERTY ---
@app.post("/properties/", response_model=schemas.PropertyResponse)
def create_property(prop: schemas.PropertyCreate, owner_id: int, db: Session = Depends(get_db)):
    owner = db.query(models.User).filter(models.User.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Không tìm thấy chủ trọ ID này")

    new_prop = models.Property(**prop.dict(), owner_id=owner_id)
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return new_prop

@app.get("/properties/", response_model=List[schemas.PropertyResponse])
def read_properties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    properties = db.query(models.Property).offset(skip).limit(limit).all()
    return properties

# --- API CONTRACT ---
@app.post("/contracts/", response_model=schemas.ContractResponse)
def create_contract(contract: schemas.ContractCreate, db: Session = Depends(get_db)):
    # 1. Tìm nhà
    db_property = db.query(models.Property).filter(models.Property.id == contract.property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Nhà không tồn tại")
    
    if db_property.status != "available":
        raise HTTPException(status_code=400, detail="Nhà này đang có người thuê hoặc bảo trì rồi!")

    # 2. Tìm khách thuê
    tenant = db.query(models.User).filter(models.User.email == contract.tenant_email).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Email khách thuê chưa đăng ký hệ thống")

    # 3. Tạo hợp đồng
    new_contract = models.Contract(
        property_id=contract.property_id,
        tenant_id=tenant.id,
        start_date=contract.start_date,
        end_date=contract.end_date,
        deposit=contract.deposit_amount,
        is_active=True
    )
    
    # 4. Cập nhật trạng thái nhà
    db_property.status = "rented"
    
    try:
        db.add(new_contract)
        db.add(db_property)
        db.flush()
        db.refresh(new_contract)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu DB: {str(e)}")
    
    return new_contract

@app.get("/contracts/", response_model=List[schemas.ContractResponse])
def read_contracts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    contracts = db.query(models.Contract).offset(skip).limit(limit).all()
    return contracts

# --- API PAYMENT ---
@app.post("/payments/", response_model=schemas.PaymentResponse)
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    # Check hợp đồng có tồn tại không
    contract = db.query(models.Contract).filter(models.Contract.id == payment.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Hợp đồng không tồn tại")

    new_payment = models.Payment(
        contract_id=payment.contract_id,
        amount=payment.amount,
        payment_date=payment.payment_date,
        note=payment.note,
        is_paid=True
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

@app.get("/contracts/{contract_id}/payments", response_model=List[schemas.PaymentResponse])
def read_payments_by_contract(contract_id: int, db: Session = Depends(get_db)):
    payments = db.query(models.Payment).filter(models.Payment.contract_id == contract_id).all()
    return payments