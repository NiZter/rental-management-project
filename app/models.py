from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Date, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . database import Base

# --- 1. USER ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String) 
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user") 
    
    properties = relationship("Property", back_populates="owner")
    contracts = relationship("Contract", back_populates="tenant")

# --- 2. PROPERTY ---
class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    description = Column(Text, nullable=True)
    price = Column(Float)
    category = Column(String, default="real_estate") 
    image_url = Column(String, nullable=True)
    status = Column(String, default="available")
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="properties")
    contracts = relationship("Contract", back_populates="property")
    damages = relationship("DamageReport", back_populates="property")

# --- 3. CONTRACT ---
class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    tenant_id = Column(Integer, ForeignKey("users.id"))
    
    start_date = Column(Date)
    end_date = Column(Date)
    
    total_price = Column(Float, default=0) 
    deposit = Column(Float, default=0)
    status = Column(String, default="active")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    property = relationship("Property", back_populates="contracts")
    tenant = relationship("User", back_populates="contracts")
    payments = relationship("Payment", back_populates="contract")
    damages = relationship("DamageReport", back_populates="contract")

# --- 4. PAYMENT ---
class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    amount = Column(Float)
    payment_date = Column(Date)
    note = Column(String, nullable=True)
    is_paid = Column(Boolean, default=True)
    
    contract = relationship("Contract", back_populates="payments")

# --- 5. DAMAGE REPORT ✅ MỚI ---
class DamageReport(Base):
    __tablename__ = "damage_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    property_id = Column(Integer, ForeignKey("properties.id"))
    
    description = Column(Text)
    severity = Column(String, default="medium")
    repair_cost = Column(Float, default=0)
    status = Column(String, default="pending")
    
    reported_date = Column(Date)
    repaired_date = Column(Date, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    contract = relationship("Contract", back_populates="damages")
    property = relationship("Property", back_populates="damages")