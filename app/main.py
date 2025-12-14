from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

# Import các module cùng thư mục
from . import models, schemas, database

app = FastAPI(title="Rental System - Hệ Thống Cho Thuê Đa Năng (De Tai 17)")

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
    return {"message": "Hệ thống Cho Thuê Đa Năng (Nhà, Xe, Đồ dùng) đang chạy!"}

# --- API USER ---
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email này đã tồn tại trong hệ thống!")
    
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

# --- API PROPERTY (NÂNG CẤP ĐA NGÀNH) ---
@app.post("/properties/", response_model=schemas.PropertyResponse)
def create_property(prop: schemas.PropertyCreate, owner_id: int, db: Session = Depends(get_db)):
    # Validate giá tiền
    if prop.price < 0:
        raise HTTPException(status_code=400, detail="Giá thuê không được âm!")

    # Validate category hợp lệ (Tùy chọn, để chặt chẽ hơn)
    valid_categories = ["real_estate", "vehicle", "item"]
    if prop.category not in valid_categories:
         raise HTTPException(status_code=400, detail="Loại tài sản không hợp lệ (chỉ chấp nhận: real_estate, vehicle, item)")

    owner = db.query(models.User).filter(models.User.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Không tìm thấy chủ sở hữu ID này")

    new_prop = models.Property(**prop.dict(), owner_id=owner_id)
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return new_prop

@app.get("/properties/", response_model=List[schemas.PropertyResponse])
def read_properties(
    skip: int = 0, 
    limit: int = 100, 
    min_price: Optional[float] = None, 
    max_price: Optional[float] = None,
    keyword: Optional[str] = None,
    category: Optional[str] = None,     # <-- THÊM BỘ LỌC CATEGORY
    db: Session = Depends(get_db)
):
    query = db.query(models.Property)

    # Logic lọc dữ liệu
    if category:
        query = query.filter(models.Property.category == category)
    if min_price is not None:
        query = query.filter(models.Property.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Property.price <= max_price)
    if keyword:
        query = query.filter(models.Property.name.contains(keyword))

    properties = query.offset(skip).limit(limit).all()
    return properties

# --- API CONTRACT (LOGIC GIỮ NGUYÊN) ---
@app.post("/contracts/", response_model=schemas.ContractResponse)
def create_contract(contract: schemas.ContractCreate, db: Session = Depends(get_db)):
    if contract.start_date >= contract.end_date:
        raise HTTPException(status_code=400, detail="Ngày kết thúc phải sau ngày bắt đầu!")
    
    if contract.deposit_amount < 0:
         raise HTTPException(status_code=400, detail="Tiền cọc không được âm!")

    db_property = db.query(models.Property).filter(models.Property.id == contract.property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Tài sản không tồn tại")
    
    if db_property.status != "available":
        raise HTTPException(status_code=400, detail="Tài sản này đang được thuê, vui lòng chọn cái khác!")

    tenant = db.query(models.User).filter(models.User.email == contract.tenant_email).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Email khách thuê chưa đăng ký hệ thống")

    new_contract = models.Contract(
        property_id=contract.property_id,
        tenant_id=tenant.id,
        start_date=contract.start_date,
        end_date=contract.end_date,
        deposit=contract.deposit_amount,
        is_active=True
    )
    
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
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Số tiền thanh toán phải lớn hơn 0!")

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