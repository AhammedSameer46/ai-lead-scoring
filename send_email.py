"""
Send Email to Captured Lead
Simple script to send emails after you've captured a lead via Chrome extension
"""

import asyncio
import sys
from gmail_sender import GmailSender
from email_drafter import EmailDrafter
from telegram_notifier import TelegramNotifier
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_lead_email():
    """
    Send email to a lead you've already captured
    """
    
    print("\n" + "="*60)
    print("Send Email to Captured Lead - The One'z and Zero")
    print("="*60 + "\n")
    
    # Get lead details
    print("Enter lead details:\n")
    lead_name = input("Lead name: ").strip()
    lead_email = input("Lead email: ").strip()
    lead_company = input("Company (optional): ").strip() or None
    lead_title = input("Title (optional): ").strip() or None
    pain_points = input("Their pain points: ").strip()
    
    if not lead_name or not lead_email:
        print("\n❌ Lead name and email are required!")
        return
    
    print(f"\n📧 Drafting email for {lead_name}...")
    
    # Initialize services
    drafter = EmailDrafter(
        api_key=settings.GROQ_API_KEY,
        company_name=settings.COMPANY_NAME
    )
    
    gmail = GmailSender(
        email=settings.COMPANY_EMAIL,
        app_password=settings.GMAIL_APP_PASSWORD
    )
    
    telegram = TelegramNotifier(
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        chat_id=settings.TELEGRAM_CHAT_ID
    )
    
    # Prepare lead data
    lead_data = {
        "name": lead_name,
        "company": lead_company,
        "title": lead_title,
        "pain_points": pain_points
    }
    
    analysis = {
        "industry": "Business",
        "pain_points": pain_points,
        "automation_needs": "Process automation",
        "recommended_pitch": "Workflow automation to reduce manual work"
    }
    
    # Draft email
    try:
        email_draft = await drafter.draft_outreach_email(
            lead_data=lead_data,
            analysis=analysis
        )
        
        subject = email_draft.get('subject', 'Re: Automation Solutions')
        body = email_draft.get('body', '')
        
        print("\n" + "="*60)
        print("EMAIL DRAFT")
        print("="*60)
        print(f"To: {lead_name} <{lead_email}>")
        print(f"Subject: {subject}\n")
        print(body)
        print("="*60 + "\n")
        
        # Ask for confirmation
        confirm = input("Send this email? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            logger.info(f"Sending email to {lead_email}...")
            
            success = gmail.send_email(
                to_email=lead_email,
                subject=subject,
                body=body,
                to_name=lead_name
            )
            
            if success:
                print(f"\n✅ Email sent successfully to {lead_email}!")
                
                # Notify via Telegram
                await telegram.send_message(
                    f"✅ Email sent to {lead_name} ({lead_email})\n"
                    f"Subject: {subject}"
                )
                
            else:
                print(f"\n❌ Failed to send email to {lead_email}")
        else:
            print("\n❌ Email not sent")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(send_lead_email())
