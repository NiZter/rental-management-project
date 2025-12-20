from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime
from typing import List, Optional
from uuid import uuid4

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
    return {"message": "Hihihihi ckao cau nka"}


# ==================================================
# HELPER FUNCTIONS (AUTO CREATE USER)
# ==================================================
def get_or_create_admin(db: Session):
    """Tự động tìm hoặc tạo ông chủ"""
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    
    if not admin:
        try:
            admin = models.User(
                email="admin@rental.com", 
                username="admin", 
                full_name="System Admin", 
                hashed_password="123", 
                role="admin"
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        except Exception as e:
            db.rollback()
            admin = db.query(models.User).filter(models.User.username == "admin").first()
            if not admin:
                raise HTTPException(status_code=500, detail=f"Cannot create admin: {str(e)}")
    return admin

def get_or_create_tenant(db: Session, email: str):
    """Tự động tìm hoặc tạo khách thuê"""
    tenant = db.query(models.User).filter(models.User.email == email).first()
    
    if not tenant:
        base_name = email.split('@')[0]
        username_gen = f"{base_name}_{uuid4().hex[:8]}"
        
        try:
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
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Cannot create tenant: {str(e)}")
    
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
    admin = get_or_create_admin(db)
    
    new_prop = models.Property(
        name=prop.name,
        address=prop.address,
        price=prop.price,
        description=prop.description,
        category=prop.category,
        image_url=prop.image_url,
        owner_id=admin.id,
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
    db: Session = Depends(get_db),
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
