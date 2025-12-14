🏠 HỆ THỐNG QUẢN LÝ CHO THUÊ BẤT ĐỘNG SẢN (ADMIN RENTAL API)

        Đây là dịch vụ Backend API được xây dựng bằng FastAPI, SQLAlchemy và PostgreSQL, dùng để quản lý các nghiệp vụ cho thuê tài sản như bất động sản, xe cộ, hoặc thiết bị.

✨ Tính năng nổi bật

        Quản lý Tài sản (Property): Thêm, xóa, tìm kiếm tài sản theo giá, danh mục, và từ khóa.

        Quản lý Hợp đồng (Contract):

                Tạo hợp đồng với cơ chế tính tổng giá động (theo ngày hoặc tháng).
                
                Tự động kiểm tra trùng lịch (overlap) thuê.
                
                Tự động tạo tài khoản khách thuê (Tenant) nếu chưa có, chỉ cần email.
                
                Tự động cập nhật trạng thái tài sản khi hợp đồng đang hiệu lực.

        Quản lý Thanh toán (Payment): Ghi nhận các giao dịch thanh toán, bao gồm tiền cọc.

        API Báo cáo Hư hỏng (Damage Report): Tính năng mới cho phép theo dõi, cập nhật chi phí và đánh dấu đã sửa chữa đối với các hư hỏng phát sinh.

        Xuất Hợp đồng (HTML/PDF): Endpoint đặc biệt giúp tải về hợp đồng dưới dạng file HTML có thể in (print to PDF) trực tiếp từ trình duyệt.

        Cơ chế người dùng: Tự động tạo tài khoản Admin cho Chủ sở hữu.

🛠️ Công nghệ sử dụng

        Backend Framework: Python (FastAPI)

        Cơ sở dữ liệu: PostgreSQL

        ORM: SQLAlchemy

        Validation: Pydantic

        Cấu hình: python-dotenv

