"""
AI Lead Scoring Engine using Groq (Free & Fast)
"""

import json
import logging
from typing import Dict, Any
from groq import AsyncGroq
from models import LeadScoreResult, ScoringConfig

logger = logging.getLogger(__name__)


class LeadScorer:
    """
    AI-powered lead scoring using Groq (Llama 3.3 70B)
    
    Evaluates leads based on:
    - Engagement: Email opens, clicks, website visits, responses
    - Fit: Company size, industry, role, budget indicators
    - Intent: Urgency signals, specific questions, demo requests
    """
    
    def __init__(self, api_key: str, config: ScoringConfig = None):
        self.client = AsyncGroq(api_key=api_key)
        self.config = config or ScoringConfig()
        # Update default model to Groq's best model
        if self.config.model == "gpt-4o":
            self.config.model = "llama-3.3-70b-versatile"
        
    async def score_lead(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a lead using AI analysis
        
        Args:
            data: Dictionary containing contact and engagement data
            
        Returns:
            Dictionary with score, tier, and reasoning
        """
        try:
            # Build prompt with structured data
            prompt = self._build_scoring_prompt(data)
            
            # Call GPT-4 for scoring
            response = await self.client.chat.completions.create(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
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
            
            # Parse AI response
            result = json.loads(response.choices[0].message.content)
            
            # Validate and structure result
            score_result = {
                "score": int(result.get("score", 0)),
                "reasoning": result.get("reasoning", ""),
                "engagement_score": result.get("engagement_score"),
                "fit_score": result.get("fit_score"),
                "intent_score": result.get("intent_score")
            }
            
            logger.info(f"Lead scored: {score_result['score']}/100")
            return score_result
            
        except Exception as e:
            logger.error(f"Error scoring lead: {str(e)}", exc_info=True)
            raise
    
    def _get_system_prompt(self) -> str:
        """System prompt defining the AI's role and scoring criteria"""
        return """You are an expert sales lead qualification AI. Your job is to analyze lead data and assign a score from 0-100.

Scoring Criteria:

1. ENGAGEMENT (40% weight):
   - Email opens and clicks
   - Website visits and page views
   - Form submissions
   - Response rate to outreach
   - Recent activity (recency matters)
   
2. FIT (35% weight):
   - Company size and industry
   - Job title and decision-making authority
   - Budget indicators
   - Use case alignment with our product
   - Geographic location
   
3. INTENT (25% weight):
   - Explicit buying signals (demo requests, pricing inquiries)
   - Urgency indicators (timeline mentioned, competitive evaluation)
   - Problem severity (pain points expressed)
   - Research depth (multiple touchpoints, specific questions)

Score Ranges:
- 80-100: HOT - High intent, strong fit, active engagement. Sales-ready.
- 40-79: WARM - Moderate interest or partial fit. Needs nurturing.
- 0-39: COLD - Low engagement, poor fit, or insufficient data.

Return a JSON object with:
{
  "score": <0-100>,
  "reasoning": "<2-3 sentence explanation>",
  "engagement_score": <0-100>,
  "fit_score": <0-100>,
  "intent_score": <0-100>
}

Be critical. Most leads are not hot. Only score 80+ if there's clear buying intent AND strong fit."""

    def _build_scoring_prompt(self, data: Dict[str, Any]) -> str:
        """Build the user prompt with lead data"""
        contact = data.get("contact", {})
        engagement = data.get("engagement", {})
        
        prompt = f"""Analyze this lead and provide a score:

CONTACT INFORMATION:
- Name: {contact.get('name', 'Unknown')}
- Email: {contact.get('email', 'N/A')}
- Phone: {contact.get('phone', 'N/A')}
- Company: {contact.get('companyName', 'N/A')}
- Source: {contact.get('source', 'Unknown')}
- Tags: {', '.join(contact.get('tags', []))}
- Date Added: {contact.get('dateAdded', 'Unknown')}

ENGAGEMENT METRICS:
- Email Opens: {engagement.get('email_opens', 0)}
- Email Clicks: {engagement.get('email_clicks', 0)}
- SMS Replies: {engagement.get('sms_replies', 0)}
- Form Submissions: {engagement.get('form_submissions', 0)}
- Website Visits: {engagement.get('website_visits', 0)}
- Call Duration: {engagement.get('call_duration_minutes', 0)} minutes
- Last Activity: {engagement.get('last_activity_date', 'Unknown')}
- Days Since First Contact: {engagement.get('days_since_first_contact', 0)}

CUSTOM FIELDS:
{json.dumps(contact.get('customFields', {}), indent=2)}

Analyze this data and return your scoring assessment in JSON format."""
        
        return prompt
    
    async def batch_score_leads(self, leads: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Score multiple leads in parallel
        
        Args:
            leads: List of lead data dictionaries
            
        Returns:
            List of score results
        """
        import asyncio
        
        tasks = [self.score_lead(lead) for lead in leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to score lead {i}: {str(result)}")
            else:
                valid_results.append(result)
        
        return valid_results
