🏠 Rental Pro - Hệ Thống Quản Lý Cho Thuê (Full Stack)

Rental Pro là giải pháp quản lý tài sản toàn diện: Nhà trọ, Xe cộ, Thiết bị.
"Code sạch, Logic chặt, Giao diện mượt."

🔥 Tính Năng "Ăn Tiền"

Đa dạng tài sản: Không chỉ phòng trọ, quản lý được cả xe hơi, máy ảnh, lều trại... (real_estate, vehicle, item).

Hợp đồng thông minh:

Tự động tính tiền theo ngày/tháng.

Chặn trùng lịch (Conflict Detection): Không bao giờ lo cho thuê trùng ngày.

Xuất PDF: In hợp đồng chuyên nghiệp chỉ với 1 click.

Theo dõi hư hỏng (Damage Tracking):

Ghi nhận hư hỏng kèm mức độ (🔴 Nặng, 🟡 Vừa, 🟢 Nhẹ).

Tính chi phí sửa chữa & trừ tiền cọc/bồi thường trực tiếp.

Tài chính minh bạch: Theo dõi tiền cọc, đã thu, còn nợ real-time.

🛠️ Cài Đặt (Localhost)

1. Database (PostgreSQL)

Tạo database mới trong pgAdmin hoặc Terminal:

CREATE DATABASE rental_db;


2. Cấu hình (.env)

Tạo file .env (copy từ code bên dưới, không commit file này):

DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=rental_db


3. Backend (FastAPI)

# Tạo môi trường ảo (Optional)
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate

# Cài thư viện
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic

# Chạy Server
uvicorn main:app --reload


👉 Server chạy tại: http://localhost:8000

👉 Docs API: http://localhost:8000/docs

4. Frontend

Mở file index.html.

Khuyên dùng Live Server (VS Code Extension) để tránh lỗi CORS.

⚠️ Lưu ý quan trọng

File reset_db.py: Chạy file này (python reset_db.py) sẽ XÓA TRẮNG database và tạo lại bảng. Chỉ dùng khi mới setup hoặc muốn reset dữ liệu.

User Admin mặc định: Hệ thống tự tạo khi có giao dịch đầu tiên (Logic Lazy Load).

📂 Cấu trúc dự án

rental-project/
├── main.py             # Brain (API Logic)
├── models.py           # Skeleton (Database Tables)
├── schemas.py          # Gatekeeper (Data Validation)
├── database.py         # Connection
├── reset_db.py         # Nuclear Button ☢️
├── app.js              # Frontend Logic
├── index.html          # User Interface
└── README.md           # Documentation
