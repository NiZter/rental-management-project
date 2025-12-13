from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Dùng SQLite cho nhanh gọn lẹ. File db sẽ tự tạo ra tên là rental.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./rental.db"

# connect_args chỉ cần thiết cho SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Hàm này để lấy DB session mỗi khi gọi API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()