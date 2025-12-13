from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware  # <--- Mới thêm
from sqlalchemy.orm import Session
from typing import List

# Import relative
from . import models, schemas, database

app = FastAPI(title="Rental Management System (De Tai 17)")

# --- CẤU HÌNH CORS (QUAN TRỌNG) ---
origins = [
    "http://localhost",
    "http://localhost:5500", # Port mặc định của Live Server VS Code
    "http://127.0.0.1:5500",
    "*" # Mở toang cửa cho dễ dev, lên production thì sửa lại sau
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------------------

# Tạo bảng tự động
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
        raise HTTPException(status_code=400, detail="Email này đăng ký rồi cha nội!")
    
    fake_hashed_password = user.password + "notreallyhashed"
    new_user = models.User(
        email=user.email, 
        username=user.username, 
        full_name=user.full_name,
        hashed_password=fake_hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- API PROPERTY ---
@app.post("/properties/", response_model=schemas.PropertyResponse)
def create_property(prop: schemas.PropertyCreate, owner_id: int, db: Session = Depends(get_db)):
    # Check owner
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