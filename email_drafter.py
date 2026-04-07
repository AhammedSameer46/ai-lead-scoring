"""
Email Drafter for Personalized Outreach
Creates customized emails based on lead analysis
"""

import json
import logging
from typing import Dict, Any
from groq import AsyncGroq

logger = logging.getLogger(__name__)


class EmailDrafter:
    """
    Draft personalized outreach emails for potential clients
    """
    
    def __init__(self, api_key: str, company_name: str = "The One'z and Zero"):
        self.client = AsyncGroq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.company_name = company_name
    
    async def draft_outreach_email(
        self,
        lead_data: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Draft personalized outreach email
        
        Args:
            lead_data: Lead information (name, company, title, etc.)
            analysis: LinkedIn analysis results
            
        Returns:
            Dictionary with subject and body
        """
        try:
            prompt = self._build_email_prompt(lead_data, analysis)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                max_tokens=600,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"Drafted email for {lead_data.get('name', 'prospect')}")
            return result
            
        except Exception as e:
            logger.error(f"Error drafting email: {str(e)}")
            raise
    
    def _get_system_prompt(self) -> str:
        """System prompt for email drafting"""
        return f"""You are writing outreach emails for {self.company_name}, an automation agency.

Email Guidelines:
1. PERSONALIZED - Reference their specific pain point from the LinkedIn post
2. BRIEF - Max 150 words, 3-4 short paragraphs
3. VALUE-FIRST - Lead with the outcome/benefit, not features
4. CONVERSATIONAL - Professional but friendly, not salesy
5. SPECIFIC - Mention exact time/money savings
6. SOFT CTA - Suggest a quick chat, not a sales call

Structure:
- Para 1: Hook - reference their specific problem
- Para 2: Solution - how we solve it (with specific outcome)
- Para 3: Soft CTA - 5-min demo or quick chat

Tone:
- Helpful, not pushy
- Confident, not arrogant
- Human, not corporate

Services We Offer:
- CRM automation (HubSpot, GoHighLevel, Salesforce)
- Lead follow-up automation
- Email marketing automation
- Booking/scheduling automation
- Workflow automation (Zapier alternative)
- Custom integrations

Return JSON:
{{
  "subject": "short, personalized subject line (under 50 chars)",
  "body": "email body text",
  "tone": "friendly/professional/casual"
}}

CRITICAL: Do NOT sound like a generic AI email. Reference their actual problem."""

    def _build_email_prompt(
        self,
        lead_data: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """Build the email drafting prompt"""
        prompt = f"""Draft a personalized outreach email:

LEAD INFO:
Name: {lead_data.get('name', 'there')}
Title: {lead_data.get('title', 'Unknown')}
Company: {lead_data.get('company', 'their company')}
Industry: {analysis.get('industry', 'Unknown')}

THEIR PAIN POINTS:
{analysis.get('pain_points', 'Manual processes taking too much time')}

WHAT THEY NEED:
{analysis.get('automation_needs', 'Process automation')}

OUR RECOMMENDED SOLUTION:
{analysis.get('recommended_pitch', 'Workflow automation')}

Draft a personalized email that:
1. References their specific problem from their post
2. Shows how we solve it with specific outcomes (time/money saved)
3. Suggests a quick 5-min demo (not a sales call)

Return in JSON format with subject and body."""
        
        return prompt
    
    async def draft_follow_up(
        self,
        lead_name: str,
        previous_email: str,
        days_since: int
    ) -> Dict[str, str]:
        """
        Draft follow-up email
        
        Args:
            lead_name: Lead's name
            previous_email: Previous email sent
            days_since: Days since last email
            
        Returns:
            Follow-up email
        """
        try:
            prompt = f"""Draft a brief follow-up email:

TO: {lead_name}
DAYS SINCE LAST EMAIL: {days_since}
PREVIOUS EMAIL:
{previous_email}

Create a SHORT follow-up (max 50 words) that:
1. Acknowledges they're busy
2. Adds one new insight/value point
3. Makes it easy to respond

Return JSON with subject and body."""

            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                max_tokens=300,
                messages=[
                    {
                        "role": "system",
                        "content": f"You write brief, value-adding follow-up emails for {self.company_name}. Keep them under 50 words."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error drafting follow-up: {str(e)}")
            raise
    
    def format_email_for_gmail(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_name: str = "The One'z and Zero Team"
    ) -> Dict[str, Any]:
        """
        Format email for sending via Gmail API
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            from_name: Sender name
            
        Returns:
            Formatted email data
        """
        # Add signature
        signature = f"\n\nBest regards,\n{from_name}\n{self.company_name}\ntheonesnzeros@gmail.com"
        
        full_body = body + signature
        
        return {
            "to": to_email,
            "subject": subject,
            "body": full_body,
            "from_name": from_name
        }
