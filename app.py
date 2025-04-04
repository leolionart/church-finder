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
app.debug = True  # Enable debug mode

# Constants
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
print(f"Loaded SPREADSHEET_ID: {SPREADSHEET_ID}")  # Debug print
RANGE_NAME = "'Churches'!A2:F"  # Changed from Sheet1 to Churches and added quotes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Cache variables
churches_cache = None
last_fetch_time = None
cache_lock = threading.Lock()

def get_google_sheets_service():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            'service-account.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        return service.spreadsheets()
    except Exception as e:
        print(f"Error creating Google Sheets service: {e}")
        return None

def fetch_churches_from_sheets(force_refresh=False):
    global churches_cache, last_fetch_time
    
    print(f"Fetching churches (force_refresh={force_refresh})")  # Debug print
    
    # Return cached data if available and not forcing refresh
    with cache_lock:
        if not force_refresh and churches_cache and last_fetch_time:
            print("Returning cached data")  # Debug print
            return churches_cache

    try:
        service = get_google_sheets_service()
        if not service:
            print("Failed to get Google Sheets service")  # Debug print
            return []

        print(f"Fetching data from sheet {SPREADSHEET_ID} range {RANGE_NAME}")  # Debug print
        sheet = service.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = sheet.get('values', [])
        print(f"Fetched {len(values)} rows from sheet")  # Debug print

        churches = []
        for i, row in enumerate(values):
            if len(row) >= 6:  # Ensure row has required fields
                try:
                    church = {
                        "name": row[0].strip(),
                        "address": row[1].strip(),
                        "mass_times": row[2].strip(),
                        "lat": float(row[4].strip()),  # Changed from index 2 to 4
                        "lng": float(row[5].strip()),  # Changed from index 3 to 5
                    }
                    # Add last_updated if available
                    if len(row) > 6:
                        church["last_updated"] = row[6].strip()
                    churches.append(church)
                except (ValueError, IndexError) as e:
                    print(f"Error processing row {i+2}: {row}")  # Debug print (i+2 because we start from A2)
                    print(f"Error details: {str(e)}")  # Debug print
                    continue

        # Update cache
        with cache_lock:
            churches_cache = churches
            last_fetch_time = datetime.now()
            print(f"Updated cache with {len(churches)} churches")  # Debug print

        return churches
    except Exception as e:
        print(f"Error fetching data from Google Sheets: {str(e)}")  # Debug print
        import traceback
        print(traceback.format_exc())  # Print full stack trace
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
            print("No churches fetched, using sample data")  # Debug print
            churches = SAMPLE_CHURCHES
        return jsonify({"success": True, "churches": churches})
    except Exception as e:
        print(f"Error in default_churches: {str(e)}")  # Debug print
        import traceback
        print(traceback.format_exc())  # Print full stack trace
        return jsonify({"success": True, "churches": SAMPLE_CHURCHES})

@app.route('/refresh-data', methods=['POST'])
def refresh_data():
    try:
        churches = fetch_churches_from_sheets(force_refresh=True)
        if not churches:
            error_msg = "Could not fetch data from Google Sheets"
            print(error_msg)  # Debug print
            return jsonify({"success": False, "error": error_msg})
        return jsonify({"success": True, "churches": churches})
    except Exception as e:
        print(f"Error in refresh_data: {str(e)}")  # Debug print
        import traceback
        print(traceback.format_exc())  # Print full stack trace
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))  # Changed default port to 5004
    app.run(host='0.0.0.0', port=port, debug=True)
