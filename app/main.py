from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from typing import List

from .database import get_db, engine
from . import models, schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ADMIN RENTAL SYSTEM (NO LOGIN)")


@app.get("/")
def root():
    return {"message": "Admin Rental System is running"}


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
        hashed_password=user.password + "_hash",  # demo
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
def list_properties(db: Session = Depends(get_db)):
    return db.query(models.Property).all()


# ==================================================
# CONTRACT
# ==================================================
@app.post("/contracts/", response_model=schemas.ContractResponse)
def create_contract(data: schemas.ContractCreate, db: Session = Depends(get_db)):
    # ---- validate date ----
    if data.start_date >= data.end_date:
        raise HTTPException(status_code=400, detail="Ngày bắt đầu phải nhỏ hơn ngày kết thúc")

    prop = db.query(models.Property).filter(models.Property.id == data.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Tài sản không tồn tại")

    if prop.status == "rented":
        raise HTTPException(status_code=409, detail="Tài sản đang được thuê")

    tenant = db.query(models.User).filter(models.User.email == data.tenant_email).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Khách hàng chưa tồn tại")

    # ---- check overlap ----
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
            detail="Tài sản đã được thuê trong khoảng thời gian này"
        )

    # ---- tính tiền ----
    days = (data.end_date - data.start_date).days

    if data.rental_type == "daily":
        total_price = days * prop.price
    elif data.rental_type == "monthly":
        months = (days + 29) // 30  # làm tròn lên theo tháng
        total_price = months * prop.price
    else:
        raise HTTPException(status_code=400, detail="Loại thuê không hợp lệ")

    contract = models.Contract(
        property_id=data.property_id,
        tenant_id=tenant.id,
        start_date=data.start_date,
        end_date=data.end_date,
        total_price=total_price,
        deposit=data.deposit,
        status="active"
    )

    # ---- cập nhật trạng thái tài sản nếu hợp đồng đang hiệu lực ----
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


# ==================================================
# PAYMENT
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
