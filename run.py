#!/usr/bin/env python3
"""
Flight Price Monitor - Main Entry Point

Usage:
    python run.py                  # Run one-time check
    python run.py --continuous     # Run continuous monitoring
    python run.py --test-email     # Send test email
    python run.py --summary        # Show current deals
"""

import sys
import os
import argparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flight_monitor import FlightMonitor
from scheduler import FlightScheduler
from notifications import NotificationService
from config import Config


def run_one_time_check():
    """Run a single monitoring cycle"""
    print("\n🔍 Running one-time flight check...\n")
    monitor = FlightMonitor()
    monitor.run_monitoring_cycle()
    monitor.print_summary()


def run_continuous_monitoring():
    """Start continuous monitoring"""
    scheduler = FlightScheduler()
    scheduler.start_continuous_monitoring()


def send_test_email():
    """Send a test email to verify configuration"""
    print("\n📧 Sending test email...\n")

    email_config = {
        'enabled': Config.EMAIL_ENABLED,
        'from': Config.EMAIL_FROM,
        'to': Config.EMAIL_TO,
        'password': Config.EMAIL_PASSWORD,
        'smtp_server': Config.SMTP_SERVER,
        'smtp_port': Config.SMTP_PORT
    }

    sms_config = {
        'enabled': Config.SMS_ENABLED,
        'account_sid': Config.TWILIO_ACCOUNT_SID,
        'auth_token': Config.TWILIO_AUTH_TOKEN,
        'from_number': Config.TWILIO_FROM_NUMBER,
        'to_number': Config.TWILIO_TO_NUMBER
    } if Config.SMS_ENABLED else None

    notifier = NotificationService(email_config, sms_config)
    notifier.send_test_notification()

    print("✅ Test notification sent! Check your email/SMS.\n")


def show_summary():
    """Display current best deals"""
    monitor = FlightMonitor()
    monitor.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description='Flight Price Monitor - Find cheap flights to Europe',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Run one-time check
  python run.py --continuous       # Start continuous monitoring
  python run.py --test-email       # Test email configuration
  python run.py --summary          # Show current deals

Configuration:
  Edit the .env file to configure your settings
        """
    )

    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous monitoring (checks every N hours)'
    )

    parser.add_argument(
        '--test-email',
        action='store_true',
        help='Send a test email to verify configuration'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary of current deals'
    )

    args = parser.parse_args()

    try:
        # Ensure required directories exist
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)

        if args.test_email:
            send_test_email()
        elif args.summary:
            show_summary()
        elif args.continuous:
            run_continuous_monitoring()
        else:
            run_one_time_check()

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
