from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Float,
    Date,
    DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


# ==================================================
# USER
# ==================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)

    hashed_password = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # user | admin

    # one user -> many properties
    properties = relationship(
        "Property",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    # one user -> many contracts (as tenant)
    contracts = relationship(
        "Contract",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )


# ==================================================
# PROPERTY
# ==================================================
class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, index=True, nullable=False)
    address = Column(String, nullable=False)
    description = Column(String, nullable=True)

    price = Column(Float, nullable=False)
    category = Column(String, default="real_estate")

    # available | rented
    status = Column(String, default="available")

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="properties")

    # one property -> many contracts
    contracts = relationship(
        "Contract",
        back_populates="property",
        cascade="all, delete-orphan"
    )


# ==================================================
# CONTRACT
# ==================================================
class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)

    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    total_price = Column(Float, default=0)
    deposit = Column(Float, default=0)

    # active | ended | cancelled
    status = Column(String, default="active")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    property = relationship("Property", back_populates="contracts")
    tenant = relationship("User", back_populates="contracts")

    payments = relationship(
        "Payment",
        back_populates="contract",
        cascade="all, delete-orphan"
    )


# ==================================================
# PAYMENT
# ==================================================
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    contract_id = Column(
        Integer,
        ForeignKey("contracts.id"),
        nullable=False
    )

    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    note = Column(String, nullable=True)

    # paid | pending
    status = Column(String, default="paid")

    contract = relationship("Contract", back_populates="payments")
