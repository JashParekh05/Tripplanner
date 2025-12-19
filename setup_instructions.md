# 🚀 Quick Setup Instructions

## Step-by-Step Setup Guide

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you get errors, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Set Up Gmail App Password

**IMPORTANT**: You need a Gmail App Password (not your regular password)

1. Go to https://myaccount.google.com/
2. Click "Security" in the left sidebar
3. Enable "2-Step Verification" if not already enabled
4. After enabling 2FA, go back to Security
5. Click "2-Step Verification"
6. Scroll to bottom and click "App passwords"
7. Select "Mail" and "Other (Custom name)"
8. Name it "Flight Monitor"
9. Click "Generate"
10. **Copy the 16-character password** (no spaces)

### 3. Create Your Configuration File

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
# Required: Your Gmail settings
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=abcd-efgh-ijkl-mnop  # The 16-char app password from step 2
EMAIL_TO=where-to-send-alerts@email.com

# Your flight preferences
DEPARTURE_DATE=2025-03-20
RETURN_DATE=2025-03-29
MAX_PRICE=600
```

### 4. Test Your Setup

```bash
python run.py --test-email
```

You should receive a test email. If not, check:
- Email password is correct (16-character app password)
- Your internet connection
- Gmail settings

### 5. Run Your First Check

```bash
python run.py
```

This will:
- Search for flights
- Show results in terminal
- Send email if deals found

### 6. Start Continuous Monitoring

```bash
python run.py --continuous
```

Leave this running! It will check every 6 hours and send alerts.

## Optional: SerpAPI Setup (Recommended)

For better results, get a free SerpAPI key:

1. Sign up at https://serpapi.com
2. Get your API key (100 free searches/month)
3. Add to `.env`:
   ```env
   SERPAPI_KEY=your-key-here
   ```

## Optional: SMS Alerts (Twilio)

1. Sign up at https://www.twilio.com
2. Get a phone number and API credentials
3. Add to `.env`:
   ```env
   SMS_ENABLED=true
   TWILIO_ACCOUNT_SID=your-sid
   TWILIO_AUTH_TOKEN=your-token
   TWILIO_FROM_NUMBER=+1234567890
   TWILIO_TO_NUMBER=+1234567890
   ```

## Running on a Server

To keep monitoring 24/7:

### Option 1: Screen (Linux/Mac)

```bash
screen -S flight-monitor
python run.py --continuous
# Press Ctrl+A then D to detach
# Later: screen -r flight-monitor to reattach
```

### Option 2: Systemd Service (Linux)

Create `/etc/systemd/system/flight-monitor.service`:

```ini
[Unit]
Description=Flight Price Monitor
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Tripplanner
ExecStart=/usr/bin/python3 /path/to/Tripplanner/run.py --continuous
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable flight-monitor
sudo systemctl start flight-monitor
sudo systemctl status flight-monitor
```

### Option 3: Cron Job

Add to crontab (runs every 6 hours):

```bash
crontab -e
```

Add:
```
0 */6 * * * cd /path/to/Tripplanner && /usr/bin/python3 run.py
```

## Troubleshooting

### "No module named 'dotenv'"

```bash
pip install python-dotenv
```

### "Authentication failed" (Email)

- Make sure you're using App Password, not regular password
- Check 2FA is enabled
- Verify EMAIL_FROM matches the Gmail account

### "No flights found"

- Check your internet connection
- Verify dates are in the future
- Try increasing DATE_FLEXIBILITY
- Get a SerpAPI key for better results

### Database locked errors

```bash
rm data/flights.db  # Reset database
python run.py       # Will recreate
```

## Next Steps

1. ✅ Complete setup
2. ✅ Test email works
3. ✅ Run first check
4. ✅ Start continuous monitoring
5. 🎉 Book your cheap flight!

---

Need help? Check `logs/flight_monitor.log` for detailed error messages.
