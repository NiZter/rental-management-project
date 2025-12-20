import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load từ .env file (chỉ tác dụng ở Localhost)
load_dotenv()

# =======================================================
# CẤU HÌNH DATABASE (AUTO DETECT)
# =======================================================

# 1. Ưu tiên lấy Connection String từ biến môi trường (Render thường cung cấp cái này)
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Nếu có DATABASE_URL, xử lý fix lỗi "postgres://" cũ của SQLAlchemy
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("🌍 Đang sử dụng cấu hình DATABASE_URL từ môi trường Cloud.")

# 3. Nếu không có, tự lắp ghép từ các biến lẻ (Dùng cho Localhost)
else:
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "rental_db")
    
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print("🏠 Đang sử dụng cấu hình Localhost.")

# =======================================================
# KẾT NỐI
# =======================================================
try:
    engine = create_engine(DATABASE_URL)
    print("✅ Database connected successfully!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    # Không raise lỗi ngay để tránh sập app khi import, nhưng log ra để biết
    pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
