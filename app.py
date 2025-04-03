from flask import Flask, render_template, request, jsonify
from scraper import ChurchScraper
import os
from dotenv import load_dotenv
import atexit

load_dotenv()

app = Flask(__name__)
scraper = ChurchScraper()

# Initialize Google Sheets importer and auto updater
sheets_importer = None
auto_updater = None
try:
    from sheets_importer import GoogleSheetsImporter
    from auto_updater import ChurchDataUpdater
    sheets_importer = GoogleSheetsImporter()
    auto_updater = ChurchDataUpdater()
    auto_updater.start()
    # Register the shutdown function to stop the scheduler when the app stops
    atexit.register(lambda: auto_updater.stop() if auto_updater else None)
except Exception as e:
    print("Google Sheets integration is not available:", str(e))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        time_slot = data.get('time_slot')
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        
        churches = scraper.search_churches(time_slot, lat, lng)
        return jsonify({'success': True, 'churches': churches})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/default-churches', methods=['POST'])
def default_churches():
    try:
        data = request.get_json()
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        
        # Get all churches within 5km radius
        churches = scraper.get_nearby_churches(lat, lng, radius_km=5)
        return jsonify({'success': True, 'churches': churches})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/update-database', methods=['POST'])
def update_database():
    try:
        new_churches = scraper.update_database()
        return jsonify({
            'success': True,
            'message': f'Added {new_churches} new churches to the database'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/import-from-sheets', methods=['POST'])
def import_from_sheets():
    if not sheets_importer or not auto_updater:
        return jsonify({
            'success': False,
            'error': 'Google Sheets integration is not available'
        }), 503
        
    try:
        # Trigger an immediate update
        auto_updater.update_data()
        return jsonify({
            'success': True,
            'message': 'Successfully triggered data update from Google Sheets'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/update-status', methods=['GET'])
def update_status():
    if not auto_updater:
        return jsonify({
            'success': False,
            'error': 'Auto updater is not available'
        }), 503
    
    try:
        # Get the next run time of the update job
        job = auto_updater.scheduler.get_job('update_church_data')
        next_run = job.next_run_time.astimezone(auto_updater.vietnam_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'next_update': next_run
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port)
