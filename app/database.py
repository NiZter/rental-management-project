import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ✅ Load từ .env file
load_dotenv()

# =======================================================
# CẤU HÌNH DATABASE
# =======================================================
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
if not DB_PASSWORD:
    raise ValueError("❌ DB_PASSWORD environment variable is required!  Kiểm tra file .env")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "rental_db")

SQLALCHEMY_DATABASE_URL = f"postgresql://rental_db_7bpv_user:uQVFLFCGPtAF5lLli7NiHojfvMFA67O7@dpg-d4vebveuk2gs739cbpgg-a.singapore-postgres.render.com/rental_db_7bpv"

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    print("✅ Database connected successfully!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
