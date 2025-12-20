from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime
from typing import List, Optional
from uuid import uuid4

from . database import get_db, engine
from .  import models, schemas

# Tạo bảng nếu chưa có
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="hihihihihi ckao cau nka")

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
    return {"message": "System is running with Postgres Sequence Fix"}


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
    tenant = db. query(models.User).filter(models.User.email == email).first()
    
    if not tenant:
        base_name = email.split('@')[0]
        username_gen = f"{base_name}_{uuid4().hex[:8]}"
        
        try:
            tenant = models.User(
                email=email,
                username=username_gen,
                full_name=base_name. capitalize(),
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
@app. post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas. UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username đã tồn tại")

    new_user = models.User(
        email=user.email,
        username=user.username,
        full_name=user. full_name,
        hashed_password=user.password + "_hash",
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users/", response_model=List[schemas. UserResponse])
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
    db: Session = Depends(get_db)
):
    query = db.query(models.Property)

    if category:
        query = query.filter(models.Property. category == category)
    if min_price is not None:
        query = query.filter(models.Property.price >= min_price)
    if max_price is not None: 
        query = query.filter(models.Property.price <= max_price)
    if keyword:
        query = query.filter(models. Property.name.contains(keyword))

    return query.all()


@app.delete("/properties/{property_id}")
def delete_property(property_id: int, db: Session = Depends(get_db)):
    """Xóa tài sản"""
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Tài sản không tồn tại")
    
    active_contract = db.query(models.Contract).filter(
        models.Contract.property_id == property_id,
        models.Contract.status == "active"
    ).first()
    
    if active_contract:
        raise HTTPException(
            status_code=409,
            detail=f"Không thể xóa - tài sản đang có hợp đồng HĐ#{active_contract.id}"
        )
    
    db.delete(prop)
    db.commit()
    return {"message": "Tài sản đã bị xóa"}


# ==================================================
# CONTRACT API
# ==================================================
@app.post("/contracts/", response_model=schemas. ContractResponse)
def create_contract(data: schemas.ContractCreate, db: Session = Depends(get_db)):
    if data.start_date >= data.end_date:
        raise HTTPException(status_code=400, detail="Ngày bắt đầu phải nhỏ hơn ngày kết thúc")

    prop = db.query(models.Property).filter(models.Property.id == data.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Tài sản không tồn tại")

    tenant = get_or_create_tenant(db, data.tenant_email)

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
            detail=f"Trùng lịch!  Đã có khách thuê từ {overlap.start_date} đến {overlap.end_date}"
        )

    days = (data.end_date - data.start_date).days
    
    if data.rental_type == "daily": 
        total_price = days * prop.price
    elif data.rental_type == "monthly":
        months = max(1, (days + 15) // 30) 
        total_price = months * prop.price
    else:
        total_price = days * prop.price

    contract = models.Contract(
        property_id=data.property_id,
        tenant_id=tenant.id,
        start_date=data.start_date,
        end_date=data.end_date,
        total_price=total_price,
        deposit=data.deposit,
        status="active"
    )

    if data.start_date <= date.today() <= data.end_date:
        prop.status = "rented"
    
    try:
        db.add(contract)
        db.add(prop)
        db.flush() 
        
        if data.deposit > 0:
            deposit_payment = models.Payment(
                contract_id=contract.id,
                amount=data.deposit,
                payment_date=date.today(),
                note="Thanh toán tiền cọc (Auto)",
                is_paid=True
            )
            db.add(deposit_payment)

        db.commit()
        db.refresh(contract)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
    return contract


@app. get("/contracts/", response_model=List[schemas.ContractResponse])
def list_contracts(db: Session = Depends(get_db)):
    return db.query(models.Contract).all()


@app.delete("/contracts/{contract_id}")
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    """Xóa hợp đồng"""
    contract = db.query(models. Contract).filter(models.Contract. id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Hợp đồng không tồn tại")
    
    prop = contract.property
    prop.status = "available"
    
    db.delete(contract)
    db.commit()
    return {"message": "Hợp đồng đã bị hủy"}


# ==================================================
# PAYMENT API
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
        is_paid=True
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@app.put("/payments/{payment_id}", response_model=schemas.PaymentResponse)
def update_payment(payment_id: int, pay:  schemas.PaymentCreate, db: Session = Depends(get_db)):
    """Cập nhật thanh toán"""
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Thanh toán không tồn tại")

    contract = db.query(models.Contract).filter(models.Contract.id == pay.contract_id).first()
    if not contract: 
        raise HTTPException(status_code=404, detail="Hợp đồng không tồn tại")

    payment.amount = pay.amount
    payment.payment_date = pay. payment_date
    payment.note = pay.note
    
    db.commit()
    db.refresh(payment)
    return payment


@app.delete("/payments/{payment_id}")
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    """Xóa thanh toán"""
    payment = db. query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Thanh toán không tồn tại")

    db.delete(payment)
    db.commit()
    return {"message":  f"Đã xóa thanh toán #{payment_id}"}


@app.get("/contracts/{contract_id}/payments", response_model=List[schemas. PaymentResponse])
def list_payments(contract_id: int, db: Session = Depends(get_db)):
    return db.query(models.Payment).filter(
        models.Payment.contract_id == contract_id
    ).all()


# ==================================================
# CONTRACT DOWNLOAD PDF ✅ MỚI
# ==================================================
@app.get("/contracts/{contract_id}/download")
def download_contract(contract_id:  int, db: Session = Depends(get_db)):
    """Tải hợp đồng dưới dạng HTML (in PDF)"""
    contract = db. query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract: 
        raise HTTPException(status_code=404, detail="Hợp đồng không tồn tại")

    tenant = contract.tenant
    prop = contract.property
    
    payments = db.query(models.Payment).filter(models.Payment.contract_id == contract_id).all()
    paid = sum(p.amount for p in payments)
    remaining = contract.total_price - paid

    # Xác định trạng thái
    status_text = "✅ ĐÃ THANH TOÁN ĐỦ" if remaining <= 0 else f"⏳ CÒN THIẾU {remaining: ,.0f}đ"
    status_class = "status-paid" if remaining <= 0 else "status-pending"
    
    # Xây dựng bảng thanh toán
    payment_rows = ""
    if not payments:
        payment_rows = '<tr><td colspan="4" style="text-align: center; color: #6b7280;">Chưa có giao dịch nào</td></tr>'
    else:
        for idx, payment in enumerate(payments, 1):
            payment_rows += f"""
            <tr>
                <td>{idx}</td>
                <td>{payment.payment_date.strftime('%d/%m/%Y')}</td>
                <td>{payment.note or '—'}</td>
                <td style="text-align: right; font-weight: bold; color: #10b981;">{payment.amount:,.0f}đ</td>
            </tr>
            """

    html_content = f"""
<! DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hợp Đồng Cho Thuê #{contract_id}</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #333;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            color: #667eea;
            font-size: 28px;
        }}
        . contract-number {{
            color: #6b7280;
            font-size: 14px;
            margin-top: 5px;
        }}
        . section {{
            margin-bottom: 30px;
        }}
        . section-title {{
            background:  #f3f4f6;
            padding: 12px 15px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }}
        . info-row {{
            display: flex;
            margin-bottom: 12px;
            padding: 8px 0;
            border-bottom:  1px solid #e5e7eb;
        }}
        .info-label {{
            flex: 0 0 200px;
            font-weight: bold;
            color: #374151;
        }}
        . info-value {{
            flex:  1;
            color: #1f2937;
        }}
        .highlight {{
            background:  #fef08a;
            padding: 15px;
            border-radius:  8px;
            margin-bottom: 20px;
        }}
        .highlight-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 40px;
            padding-top:  20px;
            border-top: 2px solid #e5e7eb;
            text-align: center;
            font-size: 12px;
            color: #6b7280;
        }}
        .signature-area {{
            display: flex;
            justify-content: space-around;
            margin-top: 40px;
            padding-top: 30px;
        }}
        .signature-box {{
            text-align: center;
            flex: 1;
        }}
        .signature-box-line {{
            border-bottom: 2px solid #000;
            margin:  50px 0 10px 0;
            min-width: 150px;
        }}
        . signature-box-label {{
            font-size: 12px;
            font-weight: bold;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        . status-paid {{
            background: #d1fae5;
            color: #065f46;
        }}
        .status-pending {{
            background: #fed7aa;
            color: #92400e;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        thead {{
            background:  #f3f4f6;
        }}
        th {{
            padding: 10px;
            text-align:  left;
            border-bottom:  2px solid #667eea;
        }}
        td {{
            padding: 10px;
            border-bottom:  1px solid #e5e7eb;
        }}
        . print-button {{
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            margin-bottom: 20px;
            font-weight: bold;
        }}
        .print-button:hover {{
            background: #764ba2;
        }}
        @media print {{
            body {{
                padding: 0;
            }}
            .print-button {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-button" onclick="window.print()">
        🖨️ In / In PDF
    </button>

    <div class="header">
        <h1>HỢP ĐỒNG CHO THUÊ</h1>
        <div class="contract-number">Số:  HĐ-{contract_id: 04d} | Ngày lập:  {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>

    <div class="section">
        <div class="status-badge {status_class}">
            {status_text}
        </div>
    </div>

    <div class="section">
        <div class="section-title">📋 THÔNG TIN HỢP ĐỒNG</div>
        <div class="info-row">
            <div class="info-label">Mã hợp đồng:</div>
            <div class="info-value">HĐ-{contract_id: 04d}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Trạng thái:</div>
            <div class="info-value">{contract.status. upper()}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Ngày bắt đầu:</div>
            <div class="info-value">{contract.start_date.strftime('%d/%m/%Y')}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Ngày kết thúc:</div>
            <div class="info-value">{contract.end_date.strftime('%d/%m/%Y')}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">🏠 THÔNG TIN TÀI SẢN CHO THUÊ</div>
        <div class="info-row">
            <div class="info-label">Tên tài sản:</div>
            <div class="info-value">{prop.name}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Địa chỉ:</div>
            <div class="info-value">{prop.address}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Loại: </div>
            <div class="info-value">{prop.category}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Giá thuê/ngày: </div>
            <div class="info-value">{prop.price: ,.0f}đ</div>
        </div>
        <div class="info-row">
            <div class="info-label">Trạng thái tài sản:</div>
            <div class="info-value">{prop.status}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">👤 THÔNG TIN KHÁCH THUÊ</div>
        <div class="info-row">
            <div class="info-label">Tên: </div>
            <div class="info-value">{tenant.full_name or tenant.username}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Email:</div>
            <div class="info-value">{tenant. email}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Tên đăng nhập:</div>
            <div class="info-value">{tenant.username}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">💰 THÔNG TIN THANH TOÁN</div>
        <div class="highlight">
            <div class="highlight-row">
                <span>Tổng tiền hợp đồng:</span>
                <span>{contract.total_price:,.0f}đ</span>
            </div>
            <div class="highlight-row">
                <span>Tiền cọc:</span>
                <span>{contract.deposit: ,.0f}đ</span>
            </div>
            <div class="highlight-row">
                <span>Đã thanh toán:</span>
                <span style="color: #10b981;">{paid:,.0f}đ</span>
            </div>
            <div class="highlight-row" style="color: {'#065f46' if remaining <= 0 else '#dc2626'}; font-size: 18px; margin-top: 10px;">
                <span>Còn thiếu:</span>
                <span>{remaining:,.0f}đ</span>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">📊 LỊCH SỬ THANH TOÁN</div>
        <table>
            <thead>
                <tr>
                    <th>STT</th>
                    <th>Ngày</th>
                    <th>Ghi chú</th>
                    <th style="text-align:  right;">Số tiền</th>
                </tr>
            </thead>
            <tbody>
                {payment_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <div class="section-title">📝 ĐIỀU KHOẢN VÀ ĐIỀU KIỆN</div>
        <ul style="line-height: 1.8; color: #1f2937;">
            <li>Khách thuê phải trả tiền đúng hạn theo hợp đồng</li>
            <li>Khách thuê chịu trách nhiệm bảo quản tài sản</li>
            <li>Chủ nhà sẽ ghi nhận mọi thanh toán ngay khi nhận tiền</li>
            <li>Trong trường hợp hư hỏng, khách thuê phải bồi thường theo định giá</li>
            <li>Hợp đồng sẽ tự động kết thúc khi hết thời gian cho thuê</li>
        </ul>
    </div>

    <div class="signature-area">
        <div class="signature-box">
            <div class="signature-box-label">Chủ nhà/Chủ tài sản</div>
            <div class="signature-box-line"></div>
            <small>Ký tên, ngày tháng</small>
        </div>
        <div class="signature-box">
            <div class="signature-box-label">Khách thuê</div>
            <div class="signature-box-line"></div>
            <small>Ký tên, ngày tháng</small>
        </div>
    </div>

    <div class="footer">
        <p>Hợp đồng này được tạo bởi Rental Pro | © 2024</p>
        <p>Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)

# ==================================================
# DAMAGE TRACKING API ✅ MỚI
# ==================================================
@app.post("/damage-reports/", response_model=schemas.DamageReportResponse)
def create_damage_report(damage:  schemas.DamageReportCreate, db: Session = Depends(get_db)):
    """Báo cáo hư hỏng"""
    contract = db.query(models.Contract).filter(models.Contract.id == damage.contract_id).first()
    if not contract: 
        raise HTTPException(status_code=404, detail="Hợp đồng không tồn tại")
    
    prop = db.query(models.Property).filter(models.Property.id == damage.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Tài sản không tồn tại")
    
    new_damage = models.DamageReport(
        contract_id=damage.contract_id,
        property_id=damage.property_id,
        description=damage.description,
        severity=damage.severity,
        repair_cost=damage.repair_cost,
        reported_date=damage.reported_date,
        status="pending"
    )
    
    db.add(new_damage)
    db.commit()
    db.refresh(new_damage)
    return new_damage


@app.get("/contracts/{contract_id}/damages", response_model=List[schemas. DamageReportResponse])
def list_damages(contract_id: int, db: Session = Depends(get_db)):
    """Lấy danh sách hư hỏng của hợp đồng"""
    return db.query(models.DamageReport).filter(
        models.DamageReport.contract_id == contract_id
    ).all()


@app.put("/damage-reports/{damage_id}", response_model=schemas.DamageReportResponse)
def update_damage(damage_id: int, damage:  schemas.DamageReportCreate, db: Session = Depends(get_db)):
    """Cập nhật báo cáo hư hỏng"""
    report = db.query(models.DamageReport).filter(models.DamageReport.id == damage_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")
    
    report.description = damage. description
    report.severity = damage.severity
    report.repair_cost = damage.repair_cost
    report.reported_date = damage.reported_date
    
    db.commit()
    db.refresh(report)
    return report


@app.patch("/damage-reports/{damage_id}/mark-repaired")
def mark_repaired(damage_id: int, db: Session = Depends(get_db)):
    """Đánh dấu đã sửa chữa"""
    report = db.query(models.DamageReport).filter(models.DamageReport. id == damage_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")
    
    report.status = "repaired"
    report.repaired_date = date.today()
    
    db.commit()
    db.refresh(report)
    return report


@app.delete("/damage-reports/{damage_id}")
def delete_damage(damage_id: int, db: Session = Depends(get_db)):
    """Xóa báo cáo hư hỏng"""
    report = db.query(models.DamageReport).filter(models.DamageReport.id == damage_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")
    
    db.delete(report)
    db.commit()
    return {"message": "Đã xóa báo cáo hư hỏng"}
