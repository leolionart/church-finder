# Church Finder

Ứng dụng web giúp tìm kiếm nhà thờ và giờ lễ tại Sài Gòn.

## Tính năng

- Hiển thị bản đồ với vị trí các nhà thờ
- Lọc nhà thờ theo giờ lễ (4:00 - 6:30 và 17:00 - 20:00)
- Xem thông tin chi tiết về từng nhà thờ
- Tự động định vị vị trí người dùng

## Công nghệ sử dụng

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- Maps: Leaflet.js với OpenStreetMap
- Deploy: Render.com

## Cài đặt local

1. Clone repository:
```bash
git clone https://github.com/yourusername/church-finder.git
cd church-finder
```

2. Tạo và kích hoạt môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # trên Unix
# hoặc
.\venv\Scripts\activate  # trên Windows
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Chạy ứng dụng:
```bash
python app.py
```

5. Truy cập http://localhost:5002

## Deploy lên Render.com

1. Tạo tài khoản trên Render.com
2. Tạo Web Service mới và kết nối với GitHub repository
3. Cấu hình như sau:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Python Version: 3.8.0
4. Click "Create Web Service"

## Cấu trúc dự án

```
church-finder/
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── Procfile           # Gunicorn configuration
├── render.yaml        # Render.com configuration
├── static/
│   ├── script.js     # Frontend JavaScript
│   └── style.css     # CSS styles
└── templates/
    └── index.html    # Main HTML template
