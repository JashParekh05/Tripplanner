#!/usr/bin/env python3
"""
Debug script to test Gmail SMTP connection
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get credentials
email_from = os.getenv('EMAIL_FROM')
email_password = os.getenv('EMAIL_PASSWORD')
email_to = os.getenv('EMAIL_TO')
smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', 587))

print("=" * 60)
print("Gmail SMTP Connection Test")
print("=" * 60)
print(f"\nEmail From: {email_from}")
print(f"Email To: {email_to}")
print(f"SMTP Server: {smtp_server}")
print(f"SMTP Port: {smtp_port}")
print(f"Password Length: {len(email_password) if email_password else 0} characters")
print(f"Password (first 4 chars): {email_password[:4] if email_password else 'None'}...")
print(f"Password (last 4 chars): ...{email_password[-4:] if email_password else 'None'}")
print(f"Password has spaces: {' ' in email_password if email_password else 'N/A'}")
print("\n" + "=" * 60)

# Test SMTP connection
try:
    print("\n🔌 Connecting to SMTP server...")
    server = smtplib.SMTP(smtp_server, smtp_port)

    print("✅ Connected to SMTP server")

    print("\n🔐 Starting TLS...")
    server.starttls()
    print("✅ TLS started")

    print(f"\n🔑 Attempting login with:")
    print(f"   Username: {email_from}")
    print(f"   Password: {'*' * len(email_password)}")

    server.login(email_from, email_password)
    print("✅ Login successful!")

    # Send test email
    print("\n📧 Sending test email...")
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = "✅ Tripplanner Email Test - SUCCESS"

    body = """
    🎉 Congratulations!

    Your Gmail SMTP configuration is working correctly!

    You can now use the Tripplanner flight monitoring system.

    Next steps:
    - Run: python3 run.py (one-time check)
    - Run: python3 run.py --continuous (continuous monitoring)
    - Run: python3 run_web.py (web dashboard)
    """

    msg.attach(MIMEText(body, 'plain'))

    server.send_message(msg)
    print("✅ Test email sent successfully!")

    server.quit()
    print("\n✅ All tests passed! Your email configuration is working.\n")

except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication failed: {e}")
    print("\nTroubleshooting steps:")
    print("1. Verify you're using an App Password, not your regular Gmail password")
    print("2. Go to https://myaccount.google.com/apppasswords")
    print("3. Generate a NEW App Password")
    print("4. Update your .env file with the new password (no spaces)")
    print("5. Try this test again")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"\nError type: {type(e).__name__}")

print("\n" + "=" * 60)
