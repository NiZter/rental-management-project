from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="owner") # owner (chủ trọ) hoặc tenant (khách thuê)

    # Quan hệ ngược
    properties = relationship("Property", back_populates="owner")
    contracts = relationship("Contract", back_populates="tenant")

class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Ví dụ: Phòng 101, Nhà Nguyên Căn A
    address = Column(String)
    price = Column(Float)
    status = Column(String, default="available") # available, rented, maintaining
    description = Column(String, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="properties")
    contracts = relationship("Contract", back_populates="property")

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    tenant_id = Column(Integer, ForeignKey("users.id"))
    
    start_date = Column(Date)
    end_date = Column(Date)
    deposit = Column(Float, default=0) # Tiền cọc
    is_active = Column(Boolean, default=True)
    
    property = relationship("Property", back_populates="contracts")
    tenant = relationship("User", back_populates="contracts")