"""
Telegram Notifier for Lead Alerts
Sends real-time notifications when hot leads are found
"""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Send lead alerts via Telegram bot
    """
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_lead_alert(
        self,
        lead_data: Dict[str, Any],
        score: int,
        reasoning: str
    ) -> bool:
        """
        Send hot lead alert to Telegram
        
        Args:
            lead_data: Lead information
            score: AI score (0-100)
            reasoning: AI explanation
            
        Returns:
            Success boolean
        """
        try:
            # Determine tier emoji
            if score >= 80:
                emoji = "🔥"
                tier = "HOT"
            elif score >= 40:
                emoji = "⚡"
                tier = "WARM"
            else:
                emoji = "❄️"
                tier = "COLD"
            
            # Build message
            message = f"{emoji} *{tier} LEAD ALERT*\n\n"
            message += f"*Score:* {score}/100\n\n"
            
            if lead_data.get("name"):
                message += f"*Name:* {lead_data['name']}\n"
            if lead_data.get("company"):
                message += f"*Company:* {lead_data['company']}\n"
            if lead_data.get("title"):
                message += f"*Title:* {lead_data['title']}\n"
            if lead_data.get("industry"):
                message += f"*Industry:* {lead_data['industry']}\n"
            
            message += f"\n*AI Analysis:*\n{reasoning}\n"
            
            if lead_data.get("pain_points"):
                message += f"\n*Pain Points:*\n{lead_data['pain_points']}\n"
            
            if lead_data.get("linkedin_url"):
                message += f"\n[View LinkedIn Profile]({lead_data['linkedin_url']})"
            
            if lead_data.get("post_url"):
                message += f"\n[View Post]({lead_data['post_url']})"
            
            # Send message
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": False
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Sent Telegram alert for {tier} lead")
                    return True
                else:
                    logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {str(e)}")
            return False
    
    async def send_email_draft(
        self,
        lead_name: str,
        email_subject: str,
        email_body: str,
        lead_url: Optional[str] = None
    ) -> bool:
        """
        Send drafted email for approval
        
        Args:
            lead_name: Lead's name
            email_subject: Drafted subject line
            email_body: Drafted email content
            lead_url: LinkedIn URL
            
        Returns:
            Success boolean
        """
        try:
            message = f"📧 *EMAIL DRAFT READY*\n\n"
            message += f"*To:* {lead_name}\n"
            message += f"*Subject:* {email_subject}\n\n"
            message += f"*Draft:*\n```\n{email_body}\n```\n\n"
            
            if lead_url:
                message += f"[View Lead Profile]({lead_url})\n\n"
            
            message += "Reply with:\n"
            message += "✅ *SEND* - I'll ask for the email address\n"
            message += "❌ *SKIP* - to skip this lead"
            
            # Send message with draft
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "Markdown"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    # Store draft in a simple file for bot to retrieve
                    # In production, use a database
                    import json
                    draft_data = {
                        "lead_name": lead_name,
                        "subject": email_subject,
                        "body": email_body,
                        "url": lead_url
                    }
                    
                    # Save to temp file
                    try:
                        with open('/tmp/last_email_draft.json', 'w') as f:
                            json.dump(draft_data, f)
                    except Exception as e:
                        logger.error(f"Could not save draft: {e}")
                    
                    return True
                else:
                    logger.error(f"Telegram API error: {response.status_code}")
                    return False
                
        except Exception as e:
            logger.error(f"Error sending email draft: {str(e)}")
            return False
    
    async def send_message(self, text: str) -> bool:
        """
        Send simple text message
        
        Args:
            text: Message text
            
        Returns:
            Success boolean
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    },
                    timeout=10.0
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    async def send_error_alert(self, error_message: str, context: Dict[str, Any]) -> bool:
        """
        Send error notification
        
        Args:
            error_message: Error description
            context: Additional context
            
        Returns:
            Success boolean
        """
        try:
            message = f"⚠️ *ERROR ALERT*\n\n"
            message += f"*Error:* {error_message}\n\n"
            message += f"*Context:* ```{context}```"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "Markdown"
                    },
                    timeout=10.0
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error sending error alert: {str(e)}")
            return False
        