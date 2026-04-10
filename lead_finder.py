"""
LinkedIn Lead Finder - Main Script
Analyzes LinkedIn posts and sends alerts for potential clients
"""

import asyncio
import sys
import logging
from datetime import datetime

from linkedin_analyzer import LinkedInAnalyzer
from email_drafter import EmailDrafter
from telegram_notifier import TelegramNotifier
from hubspot_client import HubSpotClient
from gmail_sender import GmailSender
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def analyze_linkedin_post(
    post_content: str,
    author_name: str = None,
    author_title: str = None,
    author_company: str = None,
    linkedin_url: str = None
):
    """
    Analyze a LinkedIn post for potential leads
    
    Args:
        post_content: The text content of the post
        author_name: Post author's name
        author_title: Author's job title
        author_company: Author's company
        linkedin_url: LinkedIn profile or post URL
    """
    try:
        # Initialize clients
        analyzer = LinkedInAnalyzer(api_key=settings.GROQ_API_KEY)
        drafter = EmailDrafter(
            api_key=settings.GROQ_API_KEY,
            company_name=settings.COMPANY_NAME
        )
        telegram = TelegramNotifier(
            bot_token=settings.TELEGRAM_BOT_TOKEN,
            chat_id=settings.TELEGRAM_CHAT_ID
        )
        hubspot = HubSpotClient(api_key=settings.HUBSPOT_API_KEY)
        
        # Step 1: Analyze the post
        logger.info("Analyzing LinkedIn post...")
        analysis = await analyzer.analyze_post(
            post_content=post_content,
            author_name=author_name,
            author_title=author_title,
            author_company=author_company
        )
        
        score = analysis.get("score", 0)
        tier = analysis.get("tier", "cold")
        
        logger.info(f"Analysis complete - Score: {score}/100, Tier: {tier}")
        
        # Step 2: Build lead data
        lead_data = {
            "name": author_name or "Prospect",
            "company": author_company,
            "title": author_title,
            "industry": analysis.get("industry"),
            "pain_points": analysis.get("pain_points"),
            "linkedin_url": linkedin_url,
            "post_url": linkedin_url,
            "score": score,
            "tier": tier,
            "automation_needs": analysis.get("automation_needs"),
            "urgency": analysis.get("urgency"),
            "date_found": datetime.utcnow().isoformat()
        }
        
        # Step 3: Send Telegram alert (for all leads, but emphasized for hot ones)
        logger.info("Sending Telegram notification...")
        await telegram.send_lead_alert(
            lead_data=lead_data,
            score=score,
            reasoning=analysis.get("reasoning", "")
        )
        
        # Step 4: For HOT and WARM leads, draft email
        if score >= 40:  # Hot or Warm
            logger.info("Drafting personalized email...")
            email_draft = await drafter.draft_outreach_email(
                lead_data=lead_data,
                analysis=analysis
            )
            
            # Send email draft to Telegram for approval
            await telegram.send_email_draft(
                lead_name=author_name or "the prospect",
                email_subject=email_draft.get("subject", ""),
                email_body=email_draft.get("body", ""),
                lead_url=linkedin_url
            )
            
            logger.info("Email draft sent to Telegram for review")
            
            # Ask user if they want to send the email now
            print("\n" + "="*60)
            print("EMAIL DRAFT READY")
            print("="*60)
            print(f"To: {author_name or 'Prospect'}")
            print(f"Subject: {email_draft.get('subject', '')}")
            print(f"\nBody:\n{email_draft.get('body', '')}")
            print("="*60)
            
            send_now = input("\nSend this email now? (yes/no): ").strip().lower()
            
            if send_now in ['yes', 'y']:
                # Get prospect email
                prospect_email = input("Enter prospect's email address: ").strip()
                
                if prospect_email:
                    logger.info(f"Sending email to {prospect_email}...")
                    
                    # Initialize Gmail sender
                    gmail = GmailSender(
                        email=settings.COMPANY_EMAIL,
                        app_password=settings.GMAIL_APP_PASSWORD
                    )
                    
                    # Send email
                    success = gmail.send_email(
                        to_email=prospect_email,
                        subject=email_draft.get('subject', ''),
                        body=email_draft.get('body', ''),
                        to_name=author_name
                    )
                    
                    if success:
                        print(f"\n✅ Email sent successfully to {prospect_email}!")
                        
                        # Notify via Telegram
                        await telegram.send_message(
                            f"✅ Email sent to {author_name or 'prospect'} ({prospect_email})\n"
                            f"Subject: {email_draft.get('subject', '')}"
                        )
                        
                        logger.info(f"Email sent successfully to {prospect_email}")
                    else:
                        print(f"\n❌ Failed to send email to {prospect_email}")
                        logger.error(f"Failed to send email to {prospect_email}")
                else:
                    print("\nNo email address provided - skipping send")
            else:
                print("\nEmail draft saved for later. Check Telegram for details.")
        
        # Step 5: Save to HubSpot (if contact info available)
        # For now, we'll save it with the LinkedIn URL as identifier
        logger.info("Lead analysis complete!")
        
        # Print summary
        print("\n" + "="*60)
        print(f"LEAD ANALYSIS COMPLETE")
        print("="*60)
        print(f"Score: {score}/100")
        print(f"Tier: {tier.upper()}")
        print(f"Industry: {analysis.get('industry')}")
        print(f"Pain Points: {analysis.get('pain_points')}")
        print(f"Recommended Pitch: {analysis.get('recommended_pitch')}")
        print("="*60)
        print("\nNotifications sent to Telegram!")
        print("="*60 + "\n")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing post: {str(e)}", exc_info=True)
        
        # Send error to Telegram
        try:
            telegram = TelegramNotifier(
                bot_token=settings.TELEGRAM_BOT_TOKEN,
                chat_id=settings.TELEGRAM_CHAT_ID
            )
            await telegram.send_error_alert(
                error_message=str(e),
                context={"post_preview": post_content[:200]}
            )
        except:
            pass
        
        raise


async def main():
    """Main entry point"""
    
    print("\n" + "="*60)
    print("LinkedIn Lead Finder - The One'z and Zero")
    print("="*60 + "\n")
    
    # Example usage - you can modify this
    if len(sys.argv) > 1:
        # Post content passed as command line argument
        post_content = sys.argv[1]
        author_name = sys.argv[2] if len(sys.argv) > 2 else None
        author_title = sys.argv[3] if len(sys.argv) > 3 else None
        author_company = sys.argv[4] if len(sys.argv) > 4 else None
        linkedin_url = sys.argv[5] if len(sys.argv) > 5 else None
    else:
        # Interactive mode
        print("Enter LinkedIn post details:\n")
        post_content = input("Post content (paste the full text): ")
        author_name = input("Author name (optional): ") or None
        author_title = input("Author title (optional): ") or None
        author_company = input("Author company (optional): ") or None
        linkedin_url = input("LinkedIn URL (optional): ") or None
        print()
    
    if not post_content:
        print("Error: Post content is required!")
        return
    
    await analyze_linkedin_post(
        post_content=post_content,
        author_name=author_name,
        author_title=author_title,
        author_company=author_company,
        linkedin_url=linkedin_url
    )


if __name__ == "__main__":
    asyncio.run(main())

    