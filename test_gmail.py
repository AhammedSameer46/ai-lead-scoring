"""
Test Gmail Email Sending
Quick script to verify Gmail setup is working
"""

import asyncio
from gmail_sender import GmailSender
from config import settings


def test_gmail():
    """Test Gmail connection and send test email"""
    
    print("\n" + "="*60)
    print("Testing Gmail Email Sending")
    print("="*60 + "\n")
    
    # Initialize Gmail sender
    gmail = GmailSender(
        email=settings.COMPANY_EMAIL,
        app_password=settings.GMAIL_APP_PASSWORD
    )
    
    # Test 1: Connection
    print("Test 1: Testing Gmail connection...")
    if gmail.test_connection():
        print("✅ Gmail connection successful!\n")
    else:
        print("❌ Gmail connection failed!")
        print("Check your GMAIL_APP_PASSWORD in .env file\n")
        return
    
    # Test 2: Send test email
    print("Test 2: Sending test email...")
    test_email = input("Enter your email to receive test: ").strip()
    
    if not test_email:
        print("No email provided, skipping test email")
        return
    
    print(f"Sending test email to {test_email}...")
    
    if gmail.send_test_email(test_email):
        print("✅ Test email sent successfully!")
        print(f"Check {test_email} inbox\n")
    else:
        print("❌ Failed to send test email\n")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    test_gmail()
