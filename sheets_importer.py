import os
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from geopy.geocoders import Nominatim
import json

class GoogleSheetsImporter:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="church_finder")
        self.service = self._get_sheets_service()
        self.churches_file = 'churches.json'

    def _get_sheets_service(self):
        """Initialize Google Sheets API service."""
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        
        # Try to load credentials from service account file
        try:
            credentials = service_account.Credentials.from_service_account_file(
                'service-account.json', scopes=SCOPES)
        except FileNotFoundError:
            raise Exception("service-account.json file not found. Please ensure you have the correct Google Sheets API credentials.")
        
        return build('sheets', 'v4', credentials=credentials)

    def _get_coordinates(self, address):
        """Get latitude and longitude from address using geocoding."""
        try:
            location = self.geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            return None, None
        except:
            return None, None

    def _parse_mass_times(self, mass_times_str):
        """Parse mass times string into a list."""
        if not mass_times_str:
            return []
        return [time.strip() for time in mass_times_str.split(',')]

    def _load_existing_churches(self):
        """Load existing churches from JSON file."""
        try:
            with open(self.churches_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_churches(self, churches):
        """Save churches to JSON file."""
        with open(self.churches_file, 'w', encoding='utf-8') as f:
            json.dump(churches, f, ensure_ascii=False, indent=2)

    def import_from_sheet(self, spreadsheet_id, range_name):
        """Import church data from Google Sheet."""
        try:
            # Get data from sheet
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            values = result.get('values', [])

            if not values:
                return 0

            # Load existing churches
            existing_churches = self._load_existing_churches()
            existing_names = {church['name'] for church in existing_churches}
            imported_count = 0

            # Process each row
            for row in values:
                if len(row) < 3:  # Need at least name, address, and mass times
                    continue

                name = row[0].strip()
                if name in existing_names:
                    continue

                address = row[1].strip()
                mass_times = self._parse_mass_times(row[2])
                
                # Get coordinates
                lat, lng = None, None
                if len(row) >= 5:  # If lat/lng provided in sheet
                    try:
                        lat = float(row[3])
                        lng = float(row[4])
                    except (ValueError, IndexError):
                        pass

                if lat is None or lng is None:
                    lat, lng = self._get_coordinates(address)

                if lat is None or lng is None:
                    continue  # Skip if we can't get coordinates

                # Create church entry
                church = {
                    'name': name,
                    'address': address,
                    'mass_times': mass_times,
                    'lat': lat,
                    'lng': lng,
                    'url': row[5] if len(row) > 5 else None
                }

                existing_churches.append(church)
                existing_names.add(name)
                imported_count += 1

            # Save updated churches
            self._save_churches(existing_churches)
            return imported_count

        except Exception as e:
            print(f"Error importing from sheet: {str(e)}")
            raise
