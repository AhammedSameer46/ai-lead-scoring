"""
Gmail Sender for Automated Email Outreach
Sends personalized emails via Gmail SMTP
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GmailSender:
    """
    Send emails via Gmail SMTP
    """
    
    def __init__(self, email: str, app_password: str):
        self.email = email
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        to_name: Optional[str] = None
    ) -> bool:
        """
        Send email via Gmail
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body text
            to_name: Recipient name (optional)
            
        Returns:
            Success boolean
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"The One'z and Zero <{self.email}>"
            msg['To'] = to_email if not to_name else f"{to_name} <{to_email}>"
            msg['Subject'] = subject
            
            # Add body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Connect to Gmail SMTP
            logger.info(f"Connecting to Gmail SMTP...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Login
            server.login(self.email, self.app_password)
            logger.info(f"Logged in successfully")
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Gmail authentication failed: {str(e)}")
            logger.error("Check your Gmail app password in .env file")
            return False
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_template_email(
        self,
        to_email: str,
        to_name: str,
        template_data: Dict[str, Any]
    ) -> bool:
        """
        Send email using template data
        
        Args:
            to_email: Recipient email
            to_name: Recipient name
            template_data: Dictionary with 'subject' and 'body'
            
        Returns:
            Success boolean
        """
        subject = template_data.get('subject', 'Re: Automation Solutions')
        body = template_data.get('body', '')
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            to_name=to_name
        )
    
    def test_connection(self) -> bool:
        """
        Test Gmail connection and authentication
        
        Returns:
            Success boolean
        """
        try:
            logger.info("Testing Gmail connection...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.app_password)
            server.quit()
            
            logger.info("Gmail connection successful!")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("Gmail authentication failed - check app password")
            return False
            
        except Exception as e:
            logger.error(f"Gmail connection test failed: {str(e)}")
            return False
    
    def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email to verify setup
        
        Args:
            to_email: Email to send test to
            
        Returns:
            Success boolean
        """
        subject = "Test Email - Lead Finder System"
        body = """Hello!

This is a test email from your AI Lead Finder system.

If you're seeing this, email sending is working correctly!

Best regards,
The One'z and Zero Team
"""
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )


class EmailTracker:
    """
    Track sent emails (simple in-memory tracking)
    In production, you'd save this to a database or HubSpot
    """
    
    def __init__(self):
        self.sent_emails = []
    
    def log_sent_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        lead_data: Dict[str, Any]
    ):
        """
        Log that an email was sent
        
        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            lead_data: Lead information
        """
        from datetime import datetime
        
        record = {
            "to_email": to_email,
            "to_name": to_name,
            "subject": subject,
            "sent_at": datetime.now().isoformat(),
            "lead_score": lead_data.get("score"),
            "lead_tier": lead_data.get("tier")
        }
        
        self.sent_emails.append(record)
        logger.info(f"Logged sent email to {to_name} ({to_email})")
    
    def get_sent_count(self) -> int:
        """Get total number of emails sent"""
        return len(self.sent_emails)
    
    def has_sent_to(self, email: str) -> bool:
        """Check if we've already emailed this address"""
        return any(record['to_email'] == email for record in self.sent_emails)
