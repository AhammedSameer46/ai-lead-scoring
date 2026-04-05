"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class WebhookPayload(BaseModel):
    """GoHighLevel webhook payload"""
    contact_id: Optional[str] = Field(None, alias="id")
    event_type: Optional[str] = None
    location_id: Optional[str] = None
    timestamp: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ContactData(BaseModel):
    """Contact information from GHL"""
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    companyName: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = []
    customFields: Dict[str, Any] = {}
    dateAdded: Optional[str] = None


class EngagementData(BaseModel):
    """Engagement metrics for a contact"""
    email_opens: int = 0
    email_clicks: int = 0
    sms_replies: int = 0
    form_submissions: int = 0
    website_visits: int = 0
    call_duration_minutes: int = 0
    last_activity_date: Optional[str] = None
    days_since_first_contact: int = 0


class ScoringConfig(BaseModel):
    """Configuration for AI lead scoring"""
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 500
    
    # Scoring criteria weights
    engagement_weight: float = 0.4
    fit_weight: float = 0.35
    intent_weight: float = 0.25


class LeadScoreResult(BaseModel):
    """AI scoring result"""
    score: int = Field(..., ge=0, le=100, description="Lead score 0-100")
    reasoning: str = Field(..., description="AI explanation of the score")
    engagement_score: Optional[int] = None
    fit_score: Optional[int] = None
    intent_score: Optional[int] = None
    
    @validator('score')
    def validate_score(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Score must be between 0 and 100')
        return v


class LeadScoreResponse(BaseModel):
    """API response for lead scoring"""
    contact_id: str
    score: int
    tier: str  # hot, warm, cold
    reasoning: str
    timestamp: str
    success: bool = True
    error: Optional[str] = None


class GHLUpdatePayload(BaseModel):
    """Payload for updating GHL contact"""
    tags: List[str] = []
    assignedTo: Optional[str] = None
    customField: Dict[str, Any] = {}
    pipelineStage: Optional[str] = None


class SlackNotification(BaseModel):
    """Slack message structure"""
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None
    channel: Optional[str] = None
