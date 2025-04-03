import requests
from bs4 import BeautifulSoup
import geocoder
import json
import os
import re
from datetime import datetime

class ChurchScraper:
    def __init__(self):
        self.base_url = 'https://giothanhle.net'
        self.churches_data_file = 'churches_data.json'
        
    def get_church_links(self):
        """Get all church links from the main page"""
        response = requests.get(f"{self.base_url}/gio-le")
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()  # Use set to avoid duplicates
        
        # Find all church links in the page
        for link in soup.find_all('a', href=True):
            href = link['href']
            if self.base_url not in href:
                href = self.base_url + href if href.startswith('/') else self.base_url + '/' + href
            if '/gio-le/nha-tho-' in href or '/gio-le/giao-xu-' in href:
                links.add(href)
                
        return list(links)

    def parse_mass_times(self, text):
        """Extract mass times from text"""
        # Common patterns for mass times
        time_patterns = [
            r'(\d{1,2}[:.]\d{2})(?:\s*(?:AM|PM|am|pm))?',  # matches "6:00", "6.00", with optional AM/PM
            r'(\d{1,2})\s*(?:giờ|g|h)(?:\s*\d{2})?',  # matches "6 giờ", "6g", "6h", "6g30"
            r'(\d{1,2})(?:[:.])?(\d{2})',  # matches "600", "6:00", "6.00"
        ]
        
        times = []
        text = text.lower()
        
        # Common time indicators in Vietnamese
        time_indicators = ['giờ lễ', 'thánh lễ', 'chúa nhật', 'ngày thường', 'thứ']
        
        # Find paragraphs that might contain mass times
        paragraphs = text.split('\n')
        for paragraph in paragraphs:
            if any(indicator in paragraph.lower() for indicator in time_indicators):
                # Process each time pattern
                for pattern in time_patterns:
                    matches = re.finditer(pattern, paragraph)
                    for match in matches:
                        if len(match.groups()) == 1:
                            time_str = match.group(1)
                            if ':' not in time_str and '.' not in time_str:
                                time_str += ':00'
                        else:
                            # Handle format like "630" -> "6:30"
                            hours = match.group(1)
                            minutes = match.group(2) if len(match.groups()) > 1 else '00'
                            time_str = f"{hours}:{minutes}"
                            
                        time_str = time_str.replace('.', ':')
                        # Ensure proper format (HH:MM)
                        if ':' in time_str:
                            h, m = time_str.split(':')
                            if len(h) == 1:
                                time_str = f"0{h}:{m}"
                            if len(m) == 1:
                                time_str = f"{h}:0{m}"
                        times.append(time_str)
                
        return sorted(list(set(times)))  # Remove duplicates and sort

    def get_church_details(self, url):
        """Get details for a specific church"""
        try:
            response = requests.get(url)
            response.encoding = 'utf-8'  # Ensure proper encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get church name from breadcrumb or title
            title = None
            breadcrumb = soup.find('span', class_='breadcrumb_last')
            if breadcrumb:
                title = breadcrumb.text.strip()
            if not title:
                title = soup.find('h1', class_='entry-title')
                if title:
                    title = title.text.strip()
            
            if not title:
                return None
                
            church_name = title
            if 'nhà thờ' not in church_name.lower() and 'giáo xứ' not in church_name.lower():
                church_name = 'Nhà thờ ' + church_name
                
            # Get content
            content = soup.find('div', class_='entry-content')
            if not content:
                return None
                
            content_text = content.get_text('\n')
            
            # Extract mass times
            mass_times = self.parse_mass_times(content_text)
            if not mass_times:
                return None  # Skip if no mass times found
            
            # Extract address
            address_patterns = [
                r'Địa chỉ:([^\.]*)',
                r'Địa điểm:([^\.]*)',
                r'Tọa lạc:([^\.]*)',
                r'tại([^\.]*)',
                r'toạ lạc tại([^\.]*)'
            ]
            
            address = None
            for pattern in address_patterns:
                match = re.search(pattern, content_text, re.IGNORECASE)
                if match:
                    address = match.group(1).strip()
                    break
                    
            if not address:
                # Try to find any text that looks like an address
                address_keywords = ['đường', 'phường', 'quận', 'thành phố', 'tỉnh', 'ấp', 'xã', 'huyện']
                paragraphs = content_text.split('\n')
                for p in paragraphs:
                    if any(keyword in p.lower() for keyword in address_keywords):
                        address = p.strip()
                        break
            
            if not address:
                # Use church name as fallback
                address = church_name
                
            # Get coordinates using geocoder
            location = geocoder.google(f"{church_name}, {address}, Vietnam")
            if location.ok:
                lat, lng = location.latlng
            else:
                lat, lng = None, None
                
            return {
                'name': church_name,
                'address': address,
                'mass_times': mass_times,
                'url': url,
                'lat': lat,
                'lng': lng
            }
            
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return None

    def save_churches_data(self, churches):
        """Save churches data to JSON file"""
        with open(self.churches_data_file, 'w', encoding='utf-8') as f:
            json.dump(churches, f, ensure_ascii=False, indent=2)

    def load_churches_data(self):
        """Load churches data from JSON file"""
        if os.path.exists(self.churches_data_file):
            with open(self.churches_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def update_database(self):
        """Update the churches database"""
        print("Starting database update...")
        # Load existing data
        existing_churches = self.load_churches_data()
        existing_urls = {church['url'] for church in existing_churches}
        
        # Get all church links
        print("Fetching church links...")
        links = self.get_church_links()
        print(f"Found {len(links)} church links")
        
        # Process new churches
        new_churches = []
        for i, link in enumerate(links, 1):
            if link not in existing_urls:
                print(f"Processing church {i}/{len(links)}: {link}")
                church_data = self.get_church_details(link)
                if church_data:
                    new_churches.append(church_data)
                    print(f"Added: {church_data['name']}")
                    
        # Combine existing and new data
        all_churches = existing_churches + new_churches
        
        # Save updated data
        if new_churches:
            self.save_churches_data(all_churches)
        
        return len(new_churches)

    def search_churches(self, time_slot, lat, lng, radius_km=5):
        """Search for churches with mass times near the given time and location"""
        churches = self.load_churches_data()
        target_time = datetime.strptime(time_slot, '%H:%M').time()
        
        matching_churches = []
        for church in churches:
            if not church['lat'] or not church['lng']:
                continue
                
            # Calculate distance
            distance = geocoder.distance(
                (lat, lng),
                (church['lat'], church['lng']),
                units='kilometers'
            )
            
            if distance > radius_km:
                continue
                
            # Check mass times within 1 hour range
            for mass_time in church['mass_times']:
                try:
                    church_time = datetime.strptime(mass_time, '%H:%M').time()
                    time_diff = abs(
                        (church_time.hour * 60 + church_time.minute) -
                        (target_time.hour * 60 + target_time.minute)
                    )
                    
                    # If mass time is within 1 hour of target time
                    if time_diff <= 60:
                        church_copy = church.copy()
                        church_copy['distance'] = round(distance, 1)
                        matching_churches.append(church_copy)
                        break
                except ValueError:
                    continue
                    
        # Sort by distance
        matching_churches.sort(key=lambda x: x['distance'])
        return matching_churches
