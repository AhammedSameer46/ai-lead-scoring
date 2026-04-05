"""
Slack Notification Client
Sends alerts for high-priority leads
"""

import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Client for sending Slack notifications via Incoming Webhooks
    """
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_notification(self, message: Dict[str, Any]) -> bool:
        """
        Send a notification to Slack
        
        Args:
            message: Slack message payload (supports blocks)
            
        Returns:
            Success boolean
        """
        if not self.webhook_url or self.webhook_url == "your-slack-webhook-url":
            logger.warning("Slack webhook not configured, skipping notification")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info("Slack notification sent successfully")
                    return True
                else:
                    logger.error(f"Slack notification failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False
    
    async def send_hot_lead_alert(
        self,
        contact_name: str,
        score: int,
        email: str,
        reasoning: str,
        crm_url: str
    ) -> bool:
        """
        Convenience method for hot lead alerts
        
        Args:
            contact_name: Lead's name
            score: AI score
            email: Lead's email
            reasoning: AI reasoning
            crm_url: Link to CRM record
            
        Returns:
            Success boolean
        """
        message = {
            "text": f"🔥 Hot Lead Alert - {contact_name} scored {score}/100",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔥 Hot Lead: {contact_name}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Score:*\n{score}/100"},
                        {"type": "mrkdwn", "text": f"*Email:*\n{email}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*AI Reasoning:*\n{reasoning}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View in CRM"},
                            "url": crm_url,
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
        
        return await self.send_notification(message)
    
    async def send_error_alert(self, error_message: str, context: Dict[str, Any]) -> bool:
        """
        Send error alert to Slack
        
        Args:
            error_message: Error description
            context: Additional context (contact_id, etc.)
            
        Returns:
            Success boolean
        """
        message = {
            "text": f"⚠️ Lead Scoring Error",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⚠️ Lead Scoring Error"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error:*\n```{error_message}```"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Context:*\n```{context}```"
                    }
                }
            ]
        }
        
        return await self.send_notification(message)
