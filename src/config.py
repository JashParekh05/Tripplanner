"""
Configuration management for Flight Price Monitor
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # Email Settings
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'true').lower() == 'true'
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_TO = os.getenv('EMAIL_TO', '')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

    # SMS Settings
    SMS_ENABLED = os.getenv('SMS_ENABLED', 'false').lower() == 'true'
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '')
    TWILIO_TO_NUMBER = os.getenv('TWILIO_TO_NUMBER', '')

    # API Keys
    SERPAPI_KEY = os.getenv('SERPAPI_KEY', '')

    # Flight Search Parameters
    ORIGIN_AIRPORT = os.getenv('ORIGIN_AIRPORT', 'ATL')
    DESTINATION_AIRPORTS = os.getenv('DESTINATION_AIRPORTS', 'MAD,BCN,VLC,SVQ,AGP').split(',')
    DEPARTURE_DATE = os.getenv('DEPARTURE_DATE', '2025-03-20')
    RETURN_DATE = os.getenv('RETURN_DATE', '2025-03-29')
    DATE_FLEXIBILITY = int(os.getenv('DATE_FLEXIBILITY', '3'))
    MAX_PRICE = int(os.getenv('MAX_PRICE', '600'))
    CURRENCY = os.getenv('CURRENCY', 'USD')

    # Alternative hubs for multi-leg searches
    EU_HUB_AIRPORTS = os.getenv('EU_HUB_AIRPORTS', 'LHR,CDG,AMS,FRA,FCO').split(',')

    # Monitoring Settings
    CHECK_INTERVAL_HOURS = int(os.getenv('CHECK_INTERVAL_HOURS', '6'))
    ENABLE_MULTI_LEG_SEARCH = os.getenv('ENABLE_MULTI_LEG_SEARCH', 'true').lower() == 'true'
    PRICE_DROP_THRESHOLD = int(os.getenv('PRICE_DROP_THRESHOLD', '50'))

    # Database
    DATABASE_PATH = os.path.join('data', 'flights.db')

    # Logging
    LOG_FILE = os.path.join('logs', 'flight_monitor.log')

    @staticmethod
    def get_date_range(base_date: str, flexibility: int) -> List[str]:
        """Generate list of dates within flexibility range"""
        base = datetime.strptime(base_date, '%Y-%m-%d')
        dates = []
        for i in range(-flexibility, flexibility + 1):
            date = base + timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))
        return dates

    @staticmethod
    def validate_config() -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        if Config.EMAIL_ENABLED:
            if not Config.EMAIL_FROM:
                errors.append("EMAIL_FROM is required when EMAIL_ENABLED=true")
            if not Config.EMAIL_PASSWORD:
                errors.append("EMAIL_PASSWORD is required when EMAIL_ENABLED=true")
            if not Config.EMAIL_TO:
                errors.append("EMAIL_TO is required when EMAIL_ENABLED=true")

        if Config.SMS_ENABLED:
            if not Config.TWILIO_ACCOUNT_SID:
                errors.append("TWILIO_ACCOUNT_SID is required when SMS_ENABLED=true")
            if not Config.TWILIO_AUTH_TOKEN:
                errors.append("TWILIO_AUTH_TOKEN is required when SMS_ENABLED=true")

        if not Config.EMAIL_ENABLED and not Config.SMS_ENABLED:
            errors.append("At least one notification method (EMAIL or SMS) must be enabled")

        return errors
