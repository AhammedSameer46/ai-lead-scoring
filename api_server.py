"""
API endpoint to receive LinkedIn posts from browser extension
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import asyncio

from linkedin_analyzer import LinkedInAnalyzer
from email_drafter import EmailDrafter
from telegram_notifier import TelegramNotifier
from hubspot_client import HubSpotClient
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LinkedIn Lead Capture API")

# Enable CORS so browser can send requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LinkedInPostCapture(BaseModel):
    """Model for captured LinkedIn post data"""
    post_content: str
    author_name: Optional[str] = None
    author_title: Optional[str] = None
    author_company: Optional[str] = None
    linkedin_url: Optional[str] = None


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "LinkedIn Lead Capture API",
        "endpoints": {
            "capture": "/api/capture-post",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check for Render"""
    return {"status": "healthy"}


@app.post("/api/capture-post")
async def capture_linkedin_post(post_data: LinkedInPostCapture):
    """
    Receive LinkedIn post from browser extension
    Analyze it and send alerts
    """
    try:
        logger.info(f"Received post capture from browser")
        
        # Initialize services
        analyzer = LinkedInAnalyzer(api_key=settings.GROQ_API_KEY)
        drafter = EmailDrafter(
            api_key=settings.GROQ_API_KEY,
            company_name=settings.COMPANY_NAME
        )
        telegram = TelegramNotifier(
            bot_token=settings.TELEGRAM_BOT_TOKEN,
            chat_id=settings.TELEGRAM_CHAT_ID
        )
        
        # Analyze the post
        logger.info("Analyzing LinkedIn post...")
        analysis = await analyzer.analyze_post(
            post_content=post_data.post_content,
            author_name=post_data.author_name,
            author_title=post_data.author_title,
            author_company=post_data.author_company
        )
        
        score = analysis.get("score", 0)
        tier = analysis.get("tier", "cold")
        
        logger.info(f"Analysis complete - Score: {score}/100, Tier: {tier}")
        
        # Build lead data
        from datetime import datetime
        lead_data = {
            "name": post_data.author_name or "Prospect",
            "company": post_data.author_company,
            "title": post_data.author_title,
            "industry": analysis.get("industry"),
            "pain_points": analysis.get("pain_points"),
            "linkedin_url": post_data.linkedin_url,
            "post_url": post_data.linkedin_url,
            "score": score,
            "tier": tier,
            "automation_needs": analysis.get("automation_needs"),
            "urgency": analysis.get("urgency"),
            "date_found": datetime.now().isoformat()
        }
        
        # Send Telegram alert
        logger.info("Sending Telegram notification...")
        await telegram.send_lead_alert(
            lead_data=lead_data,
            score=score,
            reasoning=analysis.get("reasoning", "")
        )
        
        # For HOT and WARM leads, draft email
        if score >= 40:
            logger.info("Drafting personalized email...")
            email_draft = await drafter.draft_outreach_email(
                lead_data=lead_data,
                analysis=analysis
            )
            
            # Send email draft to Telegram
            await telegram.send_email_draft(
                lead_name=post_data.author_name or "the prospect",
                email_subject=email_draft.get("subject", ""),
                email_body=email_draft.get("body", ""),
                lead_url=post_data.linkedin_url
            )
            
            logger.info("Email draft sent to Telegram")
        
        return {
            "success": True,
            "score": score,
            "tier": tier,
            "message": f"Lead analyzed! Score: {score}/100 ({tier.upper()}). Check Telegram for details."
        }
        
    except Exception as e:
        logger.error(f"Error processing post: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
