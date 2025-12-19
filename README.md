# ✈️ Flight Price Monitor

Automated flight price monitoring system that searches for cheap flights from Atlanta (ATL) to Spain and sends email/SMS alerts when deals are found.

## 🎯 Features

- **Smart Flight Search**: Searches multiple destinations (Madrid, Barcelona, Valencia, Seville, Malaga)
- **Flexible Dates**: Searches within ±3 days of your target dates
- **Multi-leg Optimization**: Finds cheaper routes via European hubs (London, Paris, Amsterdam, etc.)
- **Price Tracking**: Stores price history and detects price drops
- **Instant Alerts**: Email and SMS notifications for great deals
- **Continuous Monitoring**: Runs on schedule to catch deals as they appear
- **Deal Detection**: Identifies new lows and significant price drops

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- Gmail account (for email alerts)
- Optional: Twilio account (for SMS alerts)
- Optional: SerpAPI key (for reliable Google Flights data)

### 2. Installation

```bash
# Clone or download the repository
cd Tripplanner

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Email Configuration (Required)
EMAIL_ENABLED=true
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
EMAIL_TO=destination@email.com

# Flight Search Parameters
ORIGIN_AIRPORT=ATL
DESTINATION_AIRPORTS=MAD,BCN,VLC,SVQ,AGP
DEPARTURE_DATE=2025-03-20
RETURN_DATE=2025-03-29
DATE_FLEXIBILITY=3
MAX_PRICE=600

# Monitoring Settings
CHECK_INTERVAL_HOURS=6
ENABLE_MULTI_LEG_SEARCH=true
```

#### Gmail Setup

To use Gmail for email alerts:

1. Go to your Google Account settings
2. Enable 2-factor authentication
3. Generate an "App Password" for this application
4. Use the app password in `EMAIL_PASSWORD`

**Never use your actual Gmail password!**

### 4. Run the Monitor

```bash
# One-time check
python run.py

# Continuous monitoring (checks every 6 hours)
python run.py --continuous

# Test email configuration
python run.py --test-email

# Show current deals
python run.py --summary
```

## 📋 Usage Examples

### Basic Usage

```bash
# Run a single check
python run.py
```

This will:
1. Search for flights matching your criteria
2. Save results to database
3. Send email alerts for deals under $600
4. Display a summary of best deals

### Continuous Monitoring

```bash
# Start the monitor
python run.py --continuous
```

This will:
- Run an immediate check
- Schedule checks every N hours (configured in .env)
- Send alerts when new deals appear
- Keep running until you press Ctrl+C

### Check Configuration

```bash
# Test your email setup
python run.py --test-email
```

Sends a test email to verify your configuration is correct.

## 🛠️ Advanced Configuration

### Multiple Destinations

Search multiple Spanish cities:

```env
DESTINATION_AIRPORTS=MAD,BCN,VLC,SVQ,AGP,BIO
```

### Date Flexibility

Adjust how flexible your dates are:

```env
DATE_FLEXIBILITY=5  # Search ±5 days from target
```

### Multi-leg Searches

Find cheaper combinations via European hubs:

```env
ENABLE_MULTI_LEG_SEARCH=true
EU_HUB_AIRPORTS=LHR,CDG,AMS,FRA,FCO,DUB
```

For example, ATL → London → Madrid might be cheaper than ATL → Madrid direct.

### SMS Alerts (Optional)

Add Twilio for SMS notifications:

```env
SMS_ENABLED=true
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+1234567890
```

### SerpAPI (Recommended)

For more reliable flight data, get a free SerpAPI key:

1. Sign up at https://serpapi.com
2. Get your API key (100 free searches/month)
3. Add to .env:

```env
SERPAPI_KEY=your-serpapi-key
```

## 📊 How It Works

1. **Data Collection**
   - Uses SerpAPI to fetch Google Flights data
   - Falls back to direct scraping if needed
   - Searches multiple destinations and date combinations

2. **Price Analysis**
   - Stores all prices in SQLite database
   - Tracks price history over time
   - Detects price drops and new lows

3. **Deal Detection**
   - Compares prices against your MAX_PRICE threshold
   - Identifies significant price drops (>$50)
   - Flags new lowest prices for each route

4. **Notifications**
   - Sends formatted email with deal details
   - Optional SMS for urgent alerts
   - Prevents duplicate notifications

5. **Scheduling**
   - Runs checks every N hours (configurable)
   - Cleans up old data automatically
   - Maintains price history for trend analysis

## 📁 Project Structure

```
Tripplanner/
├── src/
│   ├── config.py           # Configuration management
│   ├── database.py         # Database operations
│   ├── flight_scraper.py   # Flight data collection
│   ├── flight_monitor.py   # Main monitoring logic
│   ├── notifications.py    # Email/SMS alerts
│   └── scheduler.py        # Scheduling system
├── data/
│   └── flights.db          # SQLite database (auto-created)
├── logs/
│   └── flight_monitor.log  # Application logs
├── .env                    # Your configuration (create from .env.example)
├── .env.example           # Configuration template
├── requirements.txt       # Python dependencies
├── run.py                 # Main entry point
├── README.md             # This file
└── CLAUDE.md             # AI assistant guide
```

## 🎯 Your Specific Use Case

Based on your requirements:

- **Origin**: Atlanta (ATL)
- **Destinations**: Spain (preferring Madrid - friend there)
- **Dates**: March 20-29, 2025 (flexible)
- **Budget**: $500-600
- **Goal**: Cheapest way to Europe during spring break

The system is configured to:
1. Search Madrid as primary destination
2. Check other Spanish cities (Barcelona, Valencia, etc.)
3. Look for multi-leg options via European hubs
4. Alert when prices drop below $600
5. Track price trends to catch the best deals

## 💡 Tips for Finding the Best Deals

1. **Run Continuous Monitoring**: Prices change frequently
   ```bash
   python run.py --continuous
   ```

2. **Be Flexible**: The more flexible your dates, the better deals you'll find

3. **Consider Multi-leg**: Sometimes ATL → London → Madrid is cheaper than direct

4. **Book Quickly**: When you get an alert for a great deal, book fast!

5. **Alternative Airports**: Consider flying into Barcelona or Valencia if cheaper

6. **Budget Airlines**: Once in Europe, use Ryanair/EasyJet for cheap intra-Europe flights

## 🐛 Troubleshooting

### Email Not Sending

1. Check Gmail App Password is correct
2. Verify 2FA is enabled on your Google account
3. Test with: `python run.py --test-email`

### No Flights Found

1. Check if SerpAPI key is valid (or get one free)
2. Verify dates are in future
3. Try broader date flexibility
4. Check internet connection

### Database Errors

```bash
# Reset database
rm data/flights.db
python run.py  # Will recreate database
```

## 🔒 Security Notes

- Never commit your `.env` file to git
- Use Gmail App Passwords, not your actual password
- Keep API keys private
- The `.gitignore` file protects sensitive files

## 📈 Future Enhancements

Potential improvements:

- [ ] Web dashboard for viewing deals
- [ ] More data sources (Skyscanner, Kayak API)
- [ ] Price prediction using historical data
- [ ] Mobile app integration
- [ ] Slack/Discord notifications
- [ ] Calendar integration
- [ ] Booking automation

## 🤝 Contributing

This is a personal project, but improvements are welcome!

## 📄 License

MIT License - Use freely for personal use

## 🆘 Support

For issues or questions:
1. Check the logs in `logs/flight_monitor.log`
2. Verify configuration in `.env`
3. Test with `python run.py --test-email`

## 🎉 Enjoy Your Trip!

When you find that perfect deal, book it and enjoy your spring break in Spain! 🇪🇸

---

**Last Updated**: 2025-12-19
**Version**: 1.0.0
