"""
AI Lead Scoring API - FastAPI Server
Receives GoHighLevel webhooks, scores leads with AI, updates CRM, sends Slack alerts
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import logging

from models import WebhookPayload, LeadScoreResponse, ScoringConfig
from lead_scorer import LeadScorer
from hubspot_client import HubSpotClient
from slack_notifier import SlackNotifier
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Lead Scoring API",
    description="Automated lead qualification and routing system",
    version="1.0.0"
)

# Initialize services
lead_scorer = LeadScorer(api_key=settings.GROQ_API_KEY)
hubspot_client = HubSpotClient(api_key=settings.HUBSPOT_API_KEY)
slack_notifier = SlackNotifier(webhook_url=settings.SLACK_WEBHOOK_URL)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Lead Scoring API",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/webhook/hubspot/contact", response_model=LeadScoreResponse)
async def handle_hubspot_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint for HubSpot new contact events
    
    Flow:
    1. Receive webhook payload
    2. Fetch contact details and engagement data from HubSpot
    3. Score lead with AI (Groq - Llama 3.3 70B)
    4. Route based on score (Hot/Warm/Cold)
    5. Update contact in HubSpot (properties, assignment)
    6. Send Slack notification for hot leads
    """
    try:
        # Parse webhook payload
        payload = await request.json()
        logger.info(f"Received webhook: {payload}")
        
        # HubSpot webhook format: payload is an array
        if isinstance(payload, list) and len(payload) > 0:
            event = payload[0]
            contact_id = event.get("objectId")
        else:
            contact_id = payload.get("objectId") or payload.get("vid") or payload.get("id")
        
        if not contact_id:
            raise HTTPException(status_code=400, detail="Missing contact ID in payload")
        
        # Fetch full contact details from HubSpot
        logger.info(f"Fetching contact details for ID: {contact_id}")
        contact_data = await hubspot_client.get_contact(contact_id)
        
        # Fetch engagement history
        logger.info(f"Fetching engagement data for contact: {contact_id}")
        engagement_data = await hubspot_client.get_contact_engagement(contact_id)
        
        # Prepare data for AI scoring
        scoring_input = {
            "contact": contact_data,
            "engagement": engagement_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Score the lead with AI
        logger.info(f"Scoring lead: {contact_id}")
        score_result = await lead_scorer.score_lead(scoring_input)
        
        # Determine routing tier
        tier = determine_tier(score_result["score"])
        logger.info(f"Lead {contact_id} scored {score_result['score']} - Tier: {tier}")
        
        # Update contact in HubSpot (properties, owner assignment)
        update_payload = build_hubspot_update(tier, score_result)
        await hubspot_client.update_contact(contact_id, update_payload)
        
        # Send Slack notification for hot leads (background task)
        if tier == "hot":
            background_tasks.add_task(
                send_hot_lead_alert,
                contact_data,
                score_result
            )
        
        return LeadScoreResponse(
            contact_id=contact_id,
            score=score_result["score"],
            tier=tier,
            reasoning=score_result.get("reasoning", ""),
            timestamp=datetime.utcnow().isoformat(),
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def determine_tier(score: int) -> str:
    """
    Determine lead tier based on AI score
    
    Hot: >= 80 (high intent, strong fit)
    Warm: 40-79 (moderate interest)
    Cold: < 40 (low engagement or poor fit)
    """
    if score >= 80:
        return "hot"
    elif score >= 40:
        return "warm"
    else:
        return "cold"


def build_hubspot_update(tier: str, score_result: dict) -> dict:
    """
    Build HubSpot contact update payload based on tier
    """
    tier_config = {
        "hot": {
            "assigned_to": settings.HOT_LEAD_OWNER_ID,
            "lifecycle_stage": "salesqualifiedlead",
            "lead_status": "OPEN"
        },
        "warm": {
            "assigned_to": settings.WARM_LEAD_OWNER_ID,
            "lifecycle_stage": "marketingqualifiedlead",
            "lead_status": "IN_PROGRESS"
        },
        "cold": {
            "assigned_to": settings.COLD_LEAD_OWNER_ID,
            "lifecycle_stage": "lead",
            "lead_status": "NEW"
        }
    }
    
    config = tier_config.get(tier, tier_config["cold"])
    
    return {
        "tier": tier,
        "assignedTo": config["assigned_to"],
        "customField": {
            "ai_lead_score": score_result["score"],
            "ai_score_reasoning": score_result.get("reasoning", "")[:500]  # Truncate for CRM
        }
    }


async def send_hot_lead_alert(contact_data: dict, score_result: dict):
    """Send Slack notification for hot leads"""
    try:
        message = {
            "text": f"🔥 *Hot Lead Alert* - Score: {score_result['score']}/100",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔥 Hot Lead: {contact_data.get('name', 'Unknown')}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Score:*\n{score_result['score']}/100"},
                        {"type": "mrkdwn", "text": f"*Email:*\n{contact_data.get('email', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Phone:*\n{contact_data.get('phone', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Company:*\n{contact_data.get('companyName', 'N/A')}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*AI Reasoning:*\n{score_result.get('reasoning', 'No reasoning provided')}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View in CRM"},
                            "url": f"https://app.hubspot.com/contacts/{settings.HUBSPOT_PORTAL_ID}/contact/{contact_data.get('id')}",
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
        
        await slack_notifier.send_notification(message)
        logger.info(f"Sent hot lead alert for contact {contact_data.get('id')}")
        
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")


@app.post("/test/score")
async def test_scoring(payload: dict):
    """Test endpoint for manual lead scoring"""
    try:
        score_result = await lead_scorer.score_lead(payload)
        tier = determine_tier(score_result["score"])
        
        return {
            "score": score_result["score"],
            "tier": tier,
            "reasoning": score_result.get("reasoning", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
