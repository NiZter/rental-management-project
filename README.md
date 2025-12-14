# Rental Pro - Hệ Thống Quản Lý Cho Thuê

Rental Pro là giải pháp quản lý tài sản toàn diện: Nhà trọ, Xe cộ, Thiết bị.

---
## 🚀 Live Demo
```text
https://rental-management-project.vercel.app/
```

---
## 🔥 Tính Năng Nổi Bật

### 1. Đa dạng tài sản

Không chỉ phòng trọ, quản lý được cả xe hơi, máy ảnh, lều trại... (real_estate, vehicle, item).

### 2. Hợp đồng thông minh

Tự động tính tiền theo ngày/tháng.

Chặn trùng lịch (Conflict Detection): Không bao giờ lo cho thuê trùng ngày.

Xuất PDF: In hợp đồng chuyên nghiệp chỉ với 1 click.

### 3. Theo dõi hư hỏng (Damage Tracking)

Ghi nhận hư hỏng kèm mức độ (🔴 Nặng, 🟡 Vừa, 🟢 Nhẹ).

Tính chi phí sửa chữa & trừ tiền cọc/bồi thường trực tiếp.

### 4. Tài chính minh bạch

Theo dõi tiền cọc, đã thu, còn nợ real-time.

---
### 👉 Server (Backend):
```text
http://localhost:8000
```

### 👉 Live Server (Frontend):
```text
http://localhost:5500
```

===
## 📥 Clone project về máy
### 1. Clone source code từ GitHub
```
git clone https://github.com/NiZter/rental-management-project.git
```

### 2. Di chuyển vào thư mục project
```cd rental-management-project```

### 3. Tạo môi trường ảo
```python -m venv venv```

### 4. Kích hoạt môi trường ảo
#### Windows
```venv\Scripts\activate```

#### Linux / macOS
```source venv/bin/activate
```

### 5. Cài đặt thư viện cần thiết
```pip install -r requirements.txt```

### 6. Tạo file môi trường
```cp .env.example .env```

#### Sau đó chỉnh trong .env:
```DATABASE_URL=postgresql://username:password@localhost:5432/rental_db```

### 7. Chạy FastAPI server
```uvicorn app.main:app --reload```

---
## ⚠️ Lưu ý quan trọng

File reset_db.py: Chạy file này (python reset_db.py) sẽ XÓA TRẮNG database và tạo lại bảng. Chỉ dùng khi mới setup hoặc muốn reset dữ liệu.

---
## 📂 Cấu trúc dự án

```
rental-project/
├── app/                    # Backend (API)
│   ├── main.py             # Brain (API Logic)
│   ├── models.py           # Skeleton (Database Tables)
│   ├── schemas.py          # Gatekeeper (Data Validation)
│   ├── database.py         # Database Connection
│   └── reset_db.py         # Nuclear Button
│
├── frontend/               # Frontend
│   ├── app.js              # Frontend Logic
│   └── index.html          # User Interface
│
├── .env
├── .gitignore
└── README.md               # Documentation
```
