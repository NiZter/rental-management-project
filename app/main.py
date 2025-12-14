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

app = FastAPI(title="ADMIN RENTAL SYSTEM (AUTO PILOT - PG FIX)")

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

@app.get("/")
def root():
    return {"message": "System is running with Postgres Sequence Fix"}


# ==================================================
# HELPER FUNCTIONS (AUTO CREATE USER)
# ==================================================
def get_or_create_admin(db: Session):
    """
    Tự động tìm hoặc tạo ông chủ.
    FIX: Tìm theo username, không ép ID = 1 để tránh lỗi Sequence của Postgres.
    """
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    
    if not admin:
        admin = models.User(
            # id=1,  <-- XÓA DÒNG NÀY (Để DB tự tăng ID)
            email="admin@rental.com", 
            username="admin", 
            full_name="System Admin", 
            hashed_password="123", 
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
        # Tạo username từ email
        import random
        base_name = email.split('@')[0]
        # Thêm số ngẫu nhiên để tránh trùng username
        username_gen = f"{base_name}_{random.randint(1000, 9999)}"
        
        tenant = models.User(
            email=email,
            username=username_gen,
            full_name=base_name.capitalize(),
            hashed_password="123",
            role="user"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


# ==================================================
# USER API
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
# PROPERTY API
# ==================================================
@app.post("/properties/", response_model=schemas.PropertyResponse)
def create_property(prop: schemas.PropertyCreate, db: Session = Depends(get_db)):
    # 1. Đảm bảo Admin luôn tồn tại
    admin = get_or_create_admin(db)
    
    # 2. Tạo tài sản gán cho Admin (Bỏ qua prop.owner_id từ frontend gửi lên)
    new_prop = models.Property(
        name=prop.name,
        address=prop.address,
        price=prop.price,
        description=prop.description,
        category=prop.category,
        owner_id=admin.id, # Lấy ID thật của admin trong DB
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

    if category:
        query = query.filter(models.Property.category == category)
    if min_price is not None:
        query = query.filter(models.Property.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Property.price <= max_price)
    if keyword:
        query = query.filter(models.Property.name.contains(keyword))

    return query.all()


# ==================================================
# CONTRACT API
# ==================================================
@app.post("/contracts/", response_model=schemas.ContractResponse)
def create_contract(data: schemas.ContractCreate, db: Session = Depends(get_db)):
    # 1. Validate logic
    if data.start_date >= data.end_date:
        raise HTTPException(status_code=400, detail="Ngày bắt đầu phải nhỏ hơn ngày kết thúc")

    prop = db.query(models.Property).filter(models.Property.id == data.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Tài sản không tồn tại")

    # 2. Auto Create Tenant (Lấy hoặc Tạo)
    tenant = get_or_create_tenant(db, data.tenant_email)

    # 3. Check Overlap (Trùng lịch)
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
            detail=f"Trùng lịch! Đã có khách thuê từ {overlap.start_date} đến {overlap.end_date}"
        )

    # 4. Tính tiền
    days = (data.end_date - data.start_date).days
    
    if data.rental_type == "daily":
        total_price = days * prop.price
    elif data.rental_type == "monthly":
        months = max(1, (days + 15) // 30) 
        total_price = months * prop.price
    else:
        total_price = days * prop.price

    # 5. Tạo Contract
    contract = models.Contract(
        property_id=data.property_id,
        tenant_id=tenant.id,
        start_date=data.start_date,
        end_date=data.end_date,
        total_price=total_price,
        deposit=data.deposit,
        status="active"
    )

    # 6. Cập nhật trạng thái nhà nếu đang ở ngay
    if data.start_date <= date.today() <= data.end_date:
        prop.status = "rented"
    
    try:
        db.add(contract)
        db.add(prop)
        
        # Flush để lấy contract.id trước khi tạo phiếu thu
        db.flush() 
        
        # --- AUTO CREATE PAYMENT FOR DEPOSIT ---
        if data.deposit > 0:
            deposit_payment = models.Payment(
                contract_id=contract.id,
                amount=data.deposit,
                payment_date=date.today(),
                note="Thanh toán tiền cọc (Auto)",
                status="paid"
            )
            db.add(deposit_payment)
        # ---------------------------------------

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
# PAYMENT API
# ==================================================
@app.post("/payments/", response_model=schemas.PaymentResponse)
def create_payment(pay: schemas.PaymentCreate, db: Session = Depends(get_db)):
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