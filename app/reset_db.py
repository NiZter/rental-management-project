from database import engine
import models 

print("⚠️  CẢNH BÁO: ĐANG RESET TOÀN BỘ DATABASE!")
print("Dữ liệu cũ sẽ bị xóa sạch. Bạn có chắc không? (Ctrl+C để hủy)")
# import time; time.sleep(3) # Bật cái này lên nếu sợ lỡ tay

try:
    models.Base.metadata.drop_all(bind=engine)
    print("✅ Đã xóa bảng cũ.")

    models.Base.metadata.create_all(bind=engine)
    print("✅ Đã tạo bảng mới (kèm cột image_url và password hash).")
    
    print("🚀 Done! Nhớ chạy lại Main App để nó tự tạo Admin User mới nhé.")

except Exception as e:
    print(f"❌ Lỗi: {e}")