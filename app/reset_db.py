from database import engine
import models 

print("⚠️  ĐANG TIẾN HÀNH RESET DATABASE...")

try:
    # 1. Xóa toàn bộ bảng cũ (Drop tables)
    models.Base.metadata.drop_all(bind=engine)
    print("✅ Đã xóa sạch bảng cũ.")

    # 2. Tạo lại bảng mới (Create tables)
    models.Base.metadata.create_all(bind=engine)
    print("✅ Đã tạo lại bảng mới với cấu trúc chuẩn (bao gồm cột is_paid).")
    
    print("🚀 Xong! Ông có thể chạy lại main.py ngay bây giờ.")

except Exception as e:
    print(f"❌ Có lỗi xảy ra: {e}")
    print("Gợi ý: Kiểm tra lại password hoặc kết nối trong database.py")