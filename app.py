from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import atexit
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import threading
import time

load_dotenv()

app = Flask(__name__)

# Google Sheets configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1aAEJCJKnPBmN-oOOSiwtEL6jAyBr1M1o1uj-pFj1taY'  # Your Google Sheet ID
RANGE_NAME = 'Churches!A2:F'  # Adjust based on your sheet structure

# Cache for churches data
churches_cache = []
last_fetch_time = None
cache_lock = threading.Lock()

def get_google_sheets_service():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            'service-account.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error setting up Google Sheets service: {e}")
        return None

def fetch_churches_from_sheets(force_refresh=False):
    global churches_cache, last_fetch_time
    
    # Return cached data if available and not forcing refresh
    with cache_lock:
        if not force_refresh and churches_cache and last_fetch_time:
            return churches_cache

    try:
        service = get_google_sheets_service()
        if not service:
            return []

        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])

        churches = []
        for row in values:
            if len(row) >= 5:  # Ensure row has required fields
                try:
                    church = {
                        "name": row[0].strip(),
                        "address": row[1].strip(),
                        "lat": float(row[2].strip()),
                        "lng": float(row[3].strip()),
                        "mass_times": row[4].strip(),
                    }
                    # Add last_updated if available
                    if len(row) > 5:
                        church["last_updated"] = row[5].strip()
                    churches.append(church)
                except (ValueError, IndexError) as e:
                    print(f"Error processing row {row}: {e}")
                    continue

        # Update cache
        with cache_lock:
            churches_cache = churches
            last_fetch_time = datetime.now()

        return churches
    except Exception as e:
        print(f"Error fetching data from Google Sheets: {e}")
        return []

# Fallback data in case Google Sheets fails
FALLBACK_CHURCHES = [
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
        "lat": 10.7851,
        "lng": 106.6898,
        "mass_times": "4:30, 6:00, 17:30, 19:00"
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
        
        # Try to get churches from Google Sheets
        churches = fetch_churches_from_sheets()
        
        # If Google Sheets fails, use fallback data
        if not churches:
            churches = FALLBACK_CHURCHES
        
        return jsonify({
            "success": True,
            "churches": churches
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/refresh-data', methods=['POST'])
def refresh_data():
    try:
        # Force refresh from Google Sheets
        churches = fetch_churches_from_sheets(force_refresh=True)
        return jsonify({
            "success": True,
            "message": "Data refreshed successfully",
            "churches": churches
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Initial data fetch
    fetch_churches_from_sheets()
    
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port, debug=False)
