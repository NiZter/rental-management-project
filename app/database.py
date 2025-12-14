from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# =======================================================
# CẤU HÌNH POSTGRESQL
# =======================================================

DB_USER = "postgres"
DB_PASSWORD = "123456"     
DB_HOST = "127.0.0.1"      
DB_PORT = "5432"
DB_NAME = "rental_db"

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()