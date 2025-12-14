# Nếu chạy từ ~/rental-project
from app.database import engine
from app.models import Base

print("⚠️  CẢNH BÁO:  ĐANG RESET TOÀN BỘ DATABASE!")
print("Dữ liệu cũ sẽ bị xóa sạch.  Bạn có chắc không? (Ctrl+C để hủy)")

try:
    Base.metadata. drop_all(bind=engine)
    print("✅ Đã xóa bảng cũ.")

    Base.metadata.create_all(bind=engine)
    print("✅ Đã tạo bảng mới (kèm cột image_url và password hash).")
    
    print("🚀 Done! Nhớ chạy lại Main App để nó tự tạo Admin User mới nhé.")

except Exception as e:
    print(f"❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()