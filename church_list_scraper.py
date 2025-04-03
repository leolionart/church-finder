import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChurchListScraper:
    def __init__(self):
        self.base_url = "https://giothanhle.net"
        self.church_list_url = f"{self.base_url}/danh-sach-nha-tho/"
        self.geolocator = Nominatim(user_agent="church_finder")
        
        # Setup Google Sheets API
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_file(
            'service-account.json', scopes=SCOPES)
        self.sheets_service = build('sheets', 'v4', credentials=creds)
        self.spreadsheet_id = "1aAEJCJKnPBmN-oOOSiwtEL6jAyBr1M1o1uj-pFj1taY"

    def get_church_links(self):
        """Get all church links from the church list page."""
        try:
            response = requests.get(self.church_list_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/gio-le/nha-tho-' in href or '/gio-le/giao-xu-' in href:
                    if href not in links:  # Avoid duplicates
                        links.append(href)
            
            return links
        except Exception as e:
            logger.error(f"Error getting church links: {str(e)}")
            return []

    def get_church_details(self, url):
        """Get details for a specific church."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get church name from title
            title = soup.find('h1', class_='entry-title')
            if not title:
                return None
            church_name = title.text.strip()
            
            # Get content
            content = soup.find('div', class_='entry-content')
            if not content:
                return None
            
            content_text = content.get_text()
            
            # Extract address and mass times
            address = None
            mass_times = []
            
            lines = content_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Look for address
                if any(keyword in line.lower() for keyword in ['địa chỉ:', 'địa chỉ', 'tọa lạc tại']):
                    address = line.split(':', 1)[-1].strip()
                
                # Look for mass times
                if any(keyword in line.lower() for keyword in ['giờ lễ:', 'giờ lễ', 'thứ', 'chúa nhật']):
                    mass_times.append(line.strip())
            
            if not address or not mass_times:
                return None
                
            # Get coordinates
            try:
                location = self.geolocator.geocode(address)
                if location:
                    lat, lng = location.latitude, location.longitude
                else:
                    lat, lng = None, None
            except GeocoderTimedOut:
                lat, lng = None, None
                
            return {
                'name': church_name,
                'address': address,
                'mass_times': ' | '.join(mass_times),
                'url': url,
                'lat': lat,
                'lng': lng
            }
        except Exception as e:
            logger.error(f"Error getting church details from {url}: {str(e)}")
            return None

    def update_sheet(self, churches):
        """Update Google Sheet with church data."""
        try:
            # Prepare the data
            values = [
                ['Tên nhà thờ', 'Địa chỉ', 'Giờ lễ', 'URL', 'Latitude', 'Longitude']
            ]
            
            for church in churches:
                values.append([
                    church['name'],
                    church['address'],
                    church['mass_times'],
                    church['url'],
                    church['lat'] if church['lat'] else '',
                    church['lng'] if church['lng'] else ''
                ])
            
            # Clear existing data
            self.sheets_service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range='A1:F'
            ).execute()
            
            # Update with new data
            body = {
                'values': values
            }
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range='A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return len(values) - 1  # Subtract header row
        except Exception as e:
            logger.error(f"Error updating sheet: {str(e)}")
            return 0

    def run(self):
        """Run the scraper and update the sheet."""
        logger.info("Starting church list scraper...")
        
        # Get all church links
        links = self.get_church_links()
        logger.info(f"Found {len(links)} church links")
        
        # Get details for each church
        churches = []
        for link in links:
            logger.info(f"Processing {link}")
            church = self.get_church_details(link)
            if church:
                churches.append(church)
            time.sleep(1)  # Be nice to the server
        
        logger.info(f"Successfully scraped {len(churches)} churches")
        
        # Update sheet
        updated_count = self.update_sheet(churches)
        logger.info(f"Updated sheet with {updated_count} churches")
        
        return updated_count

if __name__ == '__main__':
    scraper = ChurchListScraper()
    scraper.run()
