# Church Finder

Ứng dụng tìm kiếm nhà thờ tại Việt Nam.

## Cài đặt và Chạy Local

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Tạo file `.env` và cấu hình các biến môi trường cần thiết

3. Chạy ứng dụng:
```bash
python app.py
```

## Triển khai lên Render.com (Free Tier)

1. Đăng ký tài khoản tại [Render.com](https://render.com)

2. Tạo một Web Service mới:
   - Kết nối với repository GitHub của bạn
   - Chọn branch `main`
   - Chọn Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

3. Cấu hình Environment Variables:
   - Thêm các biến môi trường cần thiết từ file `.env` vào phần Environment của Render

4. Deploy:
   - Render sẽ tự động deploy ứng dụng
   - Mỗi khi push code mới lên GitHub, Render sẽ tự động cập nhật

## Lưu ý

- File `.env` và `service-account.json` không được đưa lên GitHub
- Cần cấu hình các biến môi trường trên Render giống như trong file `.env` local
- Dữ liệu nhà thờ sẽ được tự động cập nhật định kỳ
