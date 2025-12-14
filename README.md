# 🏠 Rental Pro - Hệ Thống Quản Lý Cho Thuê (Full Stack)

Rental Pro là giải pháp quản lý tài sản toàn diện: Nhà trọ, Xe cộ, Thiết bị.
"Code sạch, Logic chặt, Giao diện mượt."

# 🔥 Tính Năng

Đa dạng tài sản: Không chỉ phòng trọ, quản lý được cả xe hơi, máy ảnh, lều trại... (real_estate, vehicle, item).

Hợp đồng thông minh:

Tự động tính tiền theo ngày/tháng.

Chặn trùng lịch (Conflict Detection): Không bao giờ lo cho thuê trùng ngày.

Xuất PDF: In hợp đồng chuyên nghiệp chỉ với 1 click.

Theo dõi hư hỏng (Damage Tracking):

Ghi nhận hư hỏng kèm mức độ (🔴 Nặng, 🟡 Vừa, 🟢 Nhẹ).

Tính chi phí sửa chữa & trừ tiền cọc/bồi thường trực tiếp.

Tài chính minh bạch: Theo dõi tiền cọc, đã thu, còn nợ real-time.


# 👉 Server chạy tại: http://localhost:8000

# 👉 Docs API: http://localhost:5500


# ⚠️ Lưu ý quan trọng

File reset_db.py: Chạy file này (python reset_db.py) sẽ XÓA TRẮNG database và tạo lại bảng. Chỉ dùng khi mới setup hoặc muốn reset dữ liệu.

User Admin mặc định: Hệ thống tự tạo khi có giao dịch đầu tiên (Logic Lazy Load).

# 📂 Cấu trúc dự án
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
└── README.md               # Documentation

