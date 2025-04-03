from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import atexit

load_dotenv()

app = Flask(__name__)

# Sample data
SAMPLE_CHURCHES = [
    {
        "name": "Nhà thờ Đức Bà Sài Gòn",
        "address": "01 Công xã Paris, Bến Nghé, Quận 1, Thành phố Hồ Chí Minh",
        "lat": 10.7797,
        "lng": 106.6990,
        "mass_times": "5:30, 17:30"
    },
    {
        "name": "Nhà thờ Tân Định",
        "address": "289 Hai Bà Trưng, Phường 8, Quận 3, Thành phố Hồ Chí Minh",
        "lat": 10.7897,
        "lng": 106.6910,
        "mass_times": "5:00, 17:00, 18:30"
    },
    {
        "name": "Nhà thờ Huyện Sĩ",
        "address": "1 Tôn Thất Tùng, Phạm Ngũ Lão, Quận 1, Thành phố Hồ Chí Minh",
        "lat": 10.7703,
        "lng": 106.6916,
        "mass_times": "5:30, 17:00"
    },
    {
        "name": "Nhà thờ Chợ Quán",
        "address": "120 Trần Bình Trọng, Phường 3, Quận 5, Thành phố Hồ Chí Minh",
        "lat": 10.7597,
        "lng": 106.6832,
        "mass_times": "5:00, 18:00"
    },
    {
        "name": "Nhà thờ Thị Nghè",
        "address": "178 Hai Bà Trưng, Đa Kao, Quận 1, Thành phố Hồ Chí Minh",
        "lat": 10.7897,
        "lng": 106.7010,
        "mass_times": "5:30, 17:30, 19:00"
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/default-churches', methods=['POST'])
def default_churches():
    try:
        data = request.get_json()
        lat = data.get('lat', 10.7797)  # Default to Notre Dame Cathedral location
        lng = data.get('lng', 106.6990)
        
        return jsonify({
            "success": True,
            "churches": SAMPLE_CHURCHES
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port)
