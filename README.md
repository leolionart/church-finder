# Church Finder

A web application to help users find nearby churches in Vietnam and view their mass schedules.

## Features

- Interactive map interface
- Real-time location tracking
- Mass schedule filtering
- Responsive design for mobile devices
- Live data updates from Google Sheets
- Distance-based sorting
- Accurate geolocation

## Tech Stack

- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Map: Leaflet.js
- Data Source: Google Sheets API
- Deployment: Render.com

## Prerequisites

- Python 3.8+
- Google Cloud Platform account with Sheets API enabled
- Service account credentials

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/church-finder.git
cd church-finder
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with:
```
SPREADSHEET_ID=your_spreadsheet_id
```

5. Set up Google Sheets API:
- Create a project in Google Cloud Console
- Enable Google Sheets API
- Create a service account and download credentials
- Save the credentials as `service-account.json` in the project root
- Share your Google Sheet with the service account email

6. Run the application:
```bash
python app.py
```

## Google Sheet Structure

The application expects your Google Sheet to have the following columns:
1. Name - Church name
2. Address - Full address
3. Latitude - Decimal degrees (e.g., 10.7797)
4. Longitude - Decimal degrees (e.g., 106.6990)
5. Mass Times - Comma-separated times (e.g., "5:30, 17:30")
6. Last Updated - Date of last update

## Deployment

The application is configured for deployment on Render.com:

1. Create a new Web Service
2. Connect your repository
3. Set environment variables:
   - `SPREADSHEET_ID`
   - Add the contents of `service-account.json` as `GOOGLE_APPLICATION_CREDENTIALS_JSON`
4. Deploy!

## Development

To run the application in development mode:
```bash
export FLASK_ENV=development
export FLASK_APP=app.py
flask run
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

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
