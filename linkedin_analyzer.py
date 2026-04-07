"""
LinkedIn Post/Profile Analyzer
Extracts information from LinkedIn content and scores potential leads
"""

import json
import logging
from typing import Dict, Any, Optional
from groq import AsyncGroq

logger = logging.getLogger(__name__)


class LinkedInAnalyzer:
    """
    Analyze LinkedIn posts and profiles to identify potential clients
    """
    
    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    async def analyze_post(
        self,
        post_content: str,
        author_name: Optional[str] = None,
        author_title: Optional[str] = None,
        author_company: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a LinkedIn post for automation needs
        
        Args:
            post_content: The text content of the post
            author_name: Post author's name
            author_title: Post author's job title
            author_company: Post author's company
            
        Returns:
            Analysis results with score and reasoning
        """
        try:
            prompt = self._build_analysis_prompt(
                post_content,
                author_name,
                author_title,
                author_company
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                max_tokens=800,
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
            
            logger.info(f"Analyzed LinkedIn post - Score: {result.get('score', 0)}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing post: {str(e)}")
            raise
    
    def _get_system_prompt(self) -> str:
        """System prompt for LinkedIn post analysis"""
        return """You are an expert at identifying potential clients for an automation agency called "The One'z and Zero".

The agency specializes in:
- CRM automation and integration
- Lead generation automation
- Email marketing automation
- Workflow automation (Zapier, Make.com alternatives)
- Real estate automation (lead follow-up, scheduling, nurturing)
- E-commerce automation (inventory, orders, customer service)
- Coach/consultant automation (booking, client onboarding, content)

Analyze LinkedIn posts to identify people who:
1. Express pain points about manual/repetitive tasks
2. Mention spending too much time on administrative work
3. Ask for automation recommendations
4. Discuss workflow inefficiencies
5. Are in target industries (real estate, coaching, e-commerce, agencies)

Scoring (0-100):
- 80-100: HOT - Clear automation need, buying signals, budget indicators, decision maker
- 40-79: WARM - Has pain points but no urgency or unclear budget
- 0-39: COLD - Just discussing, no clear need, or not decision maker

Return JSON:
{
  "score": 0-100,
  "tier": "hot/warm/cold",
  "reasoning": "Why this score",
  "pain_points": "Specific problems mentioned",
  "automation_needs": "What they need automated",
  "industry": "Their industry",
  "urgency": "low/medium/high",
  "budget_signals": "Any budget mentions or indicators",
  "decision_maker": true/false,
  "recommended_pitch": "What service to pitch them"
}

Be critical. Most posts are NOT good leads. Only score 80+ if there's clear buying intent."""

    def _build_analysis_prompt(
        self,
        post_content: str,
        author_name: Optional[str],
        author_title: Optional[str],
        author_company: Optional[str]
    ) -> str:
        """Build the analysis prompt"""
        prompt = "Analyze this LinkedIn post for automation service opportunities:\n\n"
        
        if author_name:
            prompt += f"AUTHOR: {author_name}\n"
        if author_title:
            prompt += f"TITLE: {author_title}\n"
        if author_company:
            prompt += f"COMPANY: {author_company}\n"
        
        prompt += f"\nPOST CONTENT:\n{post_content}\n\n"
        prompt += "Analyze this and return your assessment in JSON format."
        
        return prompt
    
    async def extract_contact_info(self, text: str) -> Dict[str, Any]:
        """
        Extract potential contact information from text
        
        Args:
            text: Text to analyze
            
        Returns:
            Extracted contact info
        """
        try:
            prompt = f"""Extract contact information from this text:

{text}

Return JSON with:
{{
  "email": "email if found or null",
  "phone": "phone if found or null",
  "website": "website if found or null",
  "linkedin_url": "linkedin profile url if found or null"
}}"""

            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                max_tokens=200,
                messages=[
                    {
                        "role": "system",
                        "content": "You extract contact information from text. Return only valid information found, use null for missing fields."
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
            logger.error(f"Error extracting contact info: {str(e)}")
            return {}
    
    async def categorize_industry(self, company_description: str, title: str) -> str:
        """
        Categorize the prospect's industry
        
        Args:
            company_description: Company description
            title: Job title
            
        Returns:
            Industry category
        """
        try:
            prompt = f"""Categorize this prospect's industry:

Company: {company_description}
Title: {title}

Choose ONE category:
- Real Estate
- Coaching/Consulting
- E-commerce
- Agency (Marketing/Creative)
- SaaS
- Healthcare
- Professional Services
- Other

Return only the category name."""

            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            industry = response.choices[0].message.content.strip()
            return industry
            
        except Exception as e:
            logger.error(f"Error categorizing industry: {str(e)}")
            return "Other"
