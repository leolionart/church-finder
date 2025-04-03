import os
import json
import threading
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, jsonify, request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Constants
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME = 'Sheet1!A2:F'  # Assuming headers are in row 1
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Cache variables
churches_cache = None
last_fetch_time = None
cache_lock = threading.Lock()

def get_google_sheets_service():
    try:
        # Check if we have JSON credentials in environment variable
        creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if creds_json:
            creds_info = json.loads(creds_json)
        else:
            # Fallback to service-account.json file
            creds_path = 'service-account.json'
            if not os.path.exists(creds_path):
                print("No credentials found")
                return None
            with open(creds_path) as f:
                creds_info = json.load(f)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        return service.spreadsheets()
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

        sheet = service.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = sheet.get('values', [])

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

# Sample data for fallback
SAMPLE_CHURCHES = [
    {
        "name": "Nhà thờ Đức Bà",
        "address": "01 Công xã Paris, Bến Nghé, Quận 1, Thành phố Hồ Chí Minh",
        "lat": 10.7797,
        "lng": 106.6990,
        "mass_times": "5:30, 17:30",
        "last_updated": "2025-04-03"
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/default-churches', methods=['POST'])
def default_churches():
    try:
        churches = fetch_churches_from_sheets()
        if not churches:
            churches = SAMPLE_CHURCHES
        return jsonify({"success": True, "churches": churches})
    except Exception as e:
        print(f"Error in default_churches: {e}")
        return jsonify({"success": True, "churches": SAMPLE_CHURCHES})

@app.route('/refresh-data', methods=['POST'])
def refresh_data():
    try:
        churches = fetch_churches_from_sheets(force_refresh=True)
        if not churches:
            return jsonify({"success": False, "error": "Could not fetch data from Google Sheets"})
        return jsonify({"success": True, "churches": churches})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
