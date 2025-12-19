# Tripplanner Web Dashboard Guide

## Overview

The Tripplanner Web Dashboard provides a modern, user-friendly interface for monitoring flight deals, managing search configurations, and viewing system statistics. It includes integration with multiple flight data sources including SerpAPI, Skyscanner, and Kayak.

---

## Features

### 1. **Flight Deals Browser**
- View all flight deals in an organized grid layout
- Filter by maximum price
- Filter by data source (SerpAPI, Skyscanner, Kayak)
- Real-time deal updates
- Auto-refresh every 5 minutes
- See detailed information: price, dates, airline, stops, data source

### 2. **Manual Search**
- Trigger on-demand flight searches
- Specify custom origin, destination, and dates
- Results saved to database and viewable in deals tab

### 3. **Configuration Editor**
- Edit all search parameters via web interface
- Update destination airports
- Modify price thresholds
- Configure monitoring intervals
- Enable/disable multi-leg search
- View data source status (active/disabled)

### 4. **Statistics Dashboard**
- Total deals found
- Deals under budget
- Lowest price ever recorded
- Average flight price
- Total alerts sent
- Recent search activity

---

## Getting Started

### Installation

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment variables**:
Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
# Required for email notifications
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
EMAIL_TO=destination@email.com

# Optional: SerpAPI (Google Flights)
SERPAPI_KEY=your-serpapi-key

# Optional: Skyscanner (via RapidAPI)
SKYSCANNER_API_KEY=your-rapidapi-key

# Optional: Kayak (via RapidAPI)
KAYAK_API_KEY=your-rapidapi-key
```

### Starting the Dashboard

Run the web server:

```bash
python run_web.py
```

Or for development with auto-reload:

```bash
python run_web.py
# Or set WEB_DEBUG=true in .env
```

The dashboard will be available at:
- **Local**: http://localhost:5000
- **Network**: http://0.0.0.0:5000 (accessible from other devices on your network)

---

## API Integration Guide

### Supported Data Sources

#### 1. **SerpAPI (Google Flights)**
- **Setup**: Get API key from https://serpapi.com
- **Free Tier**: 100 searches/month
- **Configuration**: Add `SERPAPI_KEY` to `.env`
- **Features**: Most reliable, direct Google Flights data

#### 2. **Skyscanner API**
- **Setup**: Get RapidAPI key from https://rapidapi.com
- **Subscribe to**: Skyscanner API on RapidAPI marketplace
- **Configuration**: Add `SKYSCANNER_API_KEY` to `.env`
- **Features**: Wide coverage, competitive prices

#### 3. **Kayak API**
- **Setup**: Get RapidAPI key from https://rapidapi.com
- **Subscribe to**: Kayak API on RapidAPI marketplace (if available)
- **Configuration**: Add `KAYAK_API_KEY` to `.env`
- **Fallback**: If no API key, falls back to URL construction (scraping not implemented)

### How Data Sources Work Together

The system queries all configured data sources in parallel:

1. **SerpAPI** is queried first (if configured)
2. **Skyscanner** and **Kayak** are queried via `MultiSourceFlightSearcher`
3. Results are combined and deduplicated
4. Each flight is tagged with its source (`data_source` field)
5. All results are saved to the database

---

## API Endpoints

### Health Check
```
GET /api/health
```
Returns API status and timestamp.

### Get Deals
```
GET /api/deals?max_price=600&limit=50
```
Returns flight deals below the specified max price.

**Parameters**:
- `max_price` (optional): Maximum price filter (default: from config)
- `limit` (optional): Number of results (default: 50)

### Get Deal by ID
```
GET /api/deals/<id>
```
Returns specific deal details.

### Get Unnotified Deals
```
GET /api/deals/unnotified?max_price=600
```
Returns deals that haven't triggered notifications yet.

### Mark Deal as Notified
```
POST /api/deals/<id>/notify
Content-Type: application/json

{
  "alert_type": "manual"
}
```

### Get Price Trends
```
GET /api/price-trends?origin=ATL&destination=MAD&days=7
```
Returns price history for a route over the last N days.

### Get Configuration
```
GET /api/config
```
Returns current system configuration.

### Update Configuration
```
PUT /api/config
Content-Type: application/json

{
  "destination_airports": ["MAD", "BCN", "VLC"],
  "max_price": 600,
  "date_flexibility": 3,
  ...
}
```
Updates configuration (writes to .env file).

**Note**: Restart the monitoring service after updating configuration.

### Manual Search
```
POST /api/search/manual
Content-Type: application/json

{
  "origin": "ATL",
  "destination": "MAD",
  "departure_date": "2025-03-20",
  "return_date": "2025-03-29"
}
```
Triggers a manual flight search.

### Get Statistics
```
GET /api/stats
```
Returns system statistics (total deals, lowest price, alerts sent, etc.).

### Get Data Sources
```
GET /api/data-sources
```
Returns status of all configured data sources.

---

## Database Schema Updates

The database now includes a `data_source` field to track which API provided each flight:

```sql
CREATE TABLE flight_prices (
    id INTEGER PRIMARY KEY,
    origin TEXT,
    destination TEXT,
    departure_date TEXT,
    return_date TEXT,
    price REAL,
    currency TEXT,
    airline TEXT,
    stops INTEGER,
    flight_url TEXT,
    is_multi_leg BOOLEAN,
    leg_details TEXT,
    data_source TEXT DEFAULT 'serpapi',  -- NEW FIELD
    found_at TIMESTAMP,
    notified BOOLEAN
);
```

Possible values for `data_source`:
- `serpapi`
- `skyscanner`
- `kayak`

---

## Running in Production

### Using a Production WSGI Server

For production, use **Gunicorn** instead of Flask's development server:

1. **Install Gunicorn**:
```bash
pip install gunicorn
```

2. **Run with Gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 src.api:app
```

Parameters:
- `-w 4`: Use 4 worker processes
- `-b 0.0.0.0:5000`: Bind to all interfaces on port 5000

### Using Nginx as Reverse Proxy

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name tripplanner.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/Tripplanner/web;
    }
}
```

### Running as a Service

Create a systemd service file `/etc/systemd/system/tripplanner-web.service`:

```ini
[Unit]
Description=Tripplanner Web Dashboard
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/Tripplanner
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 src.api:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tripplanner-web
sudo systemctl start tripplanner-web
```

---

## Troubleshooting

### Dashboard not loading
- Check if Flask server is running: `python run_web.py`
- Check logs: `tail -f logs/web_server.log`
- Verify port 5000 is not in use: `lsof -i :5000`

### No deals showing up
- Check if monitoring service is running: `python run.py`
- Verify database exists: `ls data/flights.db`
- Check API keys are configured in `.env`

### API errors
- Check API key validity
- Verify API rate limits haven't been exceeded
- Check network connectivity
- Review logs for specific error messages

### Configuration changes not applying
- Restart the monitoring service after updating config
- Web server restart is not required for config changes

---

## Security Considerations

### API Keys
- **Never commit** `.env` file to git
- Use environment variables for sensitive data
- Rotate API keys periodically

### Network Access
- By default, server binds to `0.0.0.0` (all interfaces)
- For local-only access, set `WEB_HOST=127.0.0.1` in `.env`
- Use Nginx with SSL for production deployments
- Consider authentication middleware for public deployments

### CORS
- CORS is enabled for development
- Restrict CORS origins in production
- Edit `src/api.py` to configure allowed origins

---

## Development

### File Structure
```
Tripplanner/
├── src/
│   ├── api.py                 # Flask API backend
│   ├── api_integrations.py    # Skyscanner & Kayak clients
│   ├── flight_scraper.py      # Main scraper with multi-source support
│   ├── database.py            # Database with data_source field
│   └── ...
├── web/
│   ├── index.html            # Dashboard UI
│   ├── style.css             # Styling
│   └── app.js                # Frontend JavaScript
├── run_web.py                # Web server entry point
└── requirements.txt          # Python dependencies
```

### Adding New Data Sources

To add a new flight data source:

1. Create a new API client class in `src/api_integrations.py`:
```python
class NewSourceAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def search_flights(self, origin, destination, ...):
        # Implement search logic
        return flights  # List of flight dicts with data_source='newsource'
```

2. Add to `MultiSourceFlightSearcher`:
```python
if newsource_key:
    self.sources.append(('newsource', NewSourceAPI(newsource_key)))
```

3. Update `.env.example` with new API key field

4. Update `src/api.py` data sources endpoint

---

## Support & Contributing

- **Issues**: Report at https://github.com/your-repo/issues
- **Documentation**: See `README.md` and `CLAUDE.md`
- **License**: See LICENSE file

---

## Changelog

### Version 2.0.0 (Current)
- Added web dashboard with modern UI
- Integrated Skyscanner API
- Integrated Kayak API
- Added REST API endpoints
- Multi-source flight data aggregation
- Real-time statistics
- Manual search capability
- Web-based configuration editor

### Version 1.0.0
- Initial release with SerpAPI integration
- Email/SMS notifications
- SQLite database
- Command-line monitoring

---

**Last Updated**: 2025-12-19
**Version**: 2.0.0
