from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from typing import List, Optional

from .database import get_db, engine
from . import models, schemas

# Tạo bảng nếu chưa có
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ADMIN RENTAL SYSTEM (FINAL)")

# --- CẤU HÌNH CORS (BẮT BUỘC ĐỂ FRONTEND CHẠY) ---
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

@app.get("/")
def root():
    return {"message": "System is running with Pydantic Validation & Fixed Logic"}


# ==================================================
# USER
# ==================================================
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username đã tồn tại")

    new_user = models.User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=user.password + "_hash",
        role="user"
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
    # Pydantic (schemas.py) đã lo vụ check giá > 0 và string length.
    # Ở đây chỉ cần check logic DB.

    owner = db.query(models.User).filter(models.User.id == prop.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner không tồn tại")
    
    new_prop = models.Property(
        name=prop.name,
        address=prop.address,
        price=prop.price,
        description=prop.description,
        category=prop.category,
        owner_id=prop.owner_id,
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
    """
    API Lấy danh sách tài sản có hỗ trợ bộ lọc (Filter)
    """
    query = db.query(models.Property)

    if category:
        query = query.filter(models.Property.category == category)
    if min_price is not None:
        query = query.filter(models.Property.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Property.price <= max_price)
    if keyword:
        # Tìm gần đúng theo tên (SQLAlchemy like/contains)
        query = query.filter(models.Property.name.contains(keyword))

    return query.all()


# ==================================================
# CONTRACT
# ==================================================
@app.post("/contracts/", response_model=schemas.ContractResponse)
def create_contract(data: schemas.ContractCreate, db: Session = Depends(get_db)):
    # 1. Validate input logic
    if data.start_date >= data.end_date:
        raise HTTPException(status_code=400, detail="Ngày bắt đầu phải nhỏ hơn ngày kết thúc")

    prop = db.query(models.Property).filter(models.Property.id == data.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Tài sản không tồn tại")

    # [QUAN TRỌNG] Đã xóa đoạn check prop.status == 'rented'
    # Để cho phép đặt lịch tương lai.

    tenant = db.query(models.User).filter(models.User.email == data.tenant_email).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Khách hàng (Email) chưa tồn tại")

    # 2. Check Overlap (Trùng lịch) - Logic cốt lõi
    overlap = db.query(models.Contract).filter(
        models.Contract.property_id == data.property_id,
        models.Contract.status == "active",
        and_(
            models.Contract.start_date <= data.end_date,
            models.Contract.end_date >= data.start_date
        )
    ).first()

    if overlap:
        raise HTTPException(
            status_code=409,
            detail=f"Trùng lịch! Tài sản đã được thuê từ {overlap.start_date} đến {overlap.end_date}"
        )

    # 3. Tính tiền
    days = (data.end_date - data.start_date).days
    
    if data.rental_type == "daily":
        total_price = days * prop.price
    elif data.rental_type == "monthly":
        # Làm tròn tháng (ví dụ 40 ngày -> 2 tháng)
        months = max(1, (days + 15) // 30) 
        total_price = months * prop.price
    else:
        # Fallback an toàn
        total_price = days * prop.price

    # 4. Tạo hợp đồng
    contract = models.Contract(
        property_id=data.property_id,
        tenant_id=tenant.id,
        start_date=data.start_date,
        end_date=data.end_date,
        total_price=total_price,
        deposit=data.deposit,  # Map đúng với schemas.py
        status="active"
    )

    # 5. Cập nhật UI status (Chỉ update nếu ngày thuê bao gồm hôm nay)
    if data.start_date <= date.today() <= data.end_date:
        prop.status = "rented"
    
    try:
        db.add(contract)
        db.add(prop)
        db.commit()
        db.refresh(contract)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
    return contract


@app.get("/contracts/", response_model=List[schemas.ContractResponse])
def list_contracts(db: Session = Depends(get_db)):
    return db.query(models.Contract).all()


# ==================================================
# PAYMENT
# ==================================================
@app.post("/payments/", response_model=schemas.PaymentResponse)
def create_payment(pay: schemas.PaymentCreate, db: Session = Depends(get_db)):
    # Pydantic đã check amount > 0 rồi
    
    contract = db.query(models.Contract).filter(models.Contract.id == pay.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Hợp đồng không tồn tại")

    payment = models.Payment(
        contract_id=pay.contract_id,
        amount=pay.amount,
        payment_date=pay.payment_date,
        note=pay.note,
        status="paid"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@app.get("/contracts/{contract_id}/payments", response_model=List[schemas.PaymentResponse])
def list_payments(contract_id: int, db: Session = Depends(get_db)):
    return db.query(models.Payment).filter(
        models.Payment.contract_id == contract_id
    ).all()