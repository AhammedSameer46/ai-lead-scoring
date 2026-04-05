"""
Test suite for AI Lead Scoring API
"""

import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"


@pytest.mark.asyncio
async def test_manual_scoring():
    """Test manual lead scoring endpoint"""
    payload = {
        "contact": {
            "name": "John Doe",
            "email": "john@example.com",
            "companyName": "Acme Corp",
            "source": "Website Form",
            "tags": ["Enterprise", "Inbound"]
        },
        "engagement": {
            "email_opens": 10,
            "email_clicks": 5,
            "website_visits": 15,
            "form_submissions": 2,
            "call_duration_minutes": 30
        }
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/test/score", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "score" in data
        assert "tier" in data
        assert "reasoning" in data
        assert 0 <= data["score"] <= 100
        assert data["tier"] in ["hot", "warm", "cold"]


# Sample webhook payloads for testing

SAMPLE_GHL_WEBHOOK = {
    "contact_id": "test-contact-123",
    "event_type": "contact.created",
    "location_id": "test-location-456",
    "timestamp": "2026-04-01T10:30:00Z",
    "data": {
        "id": "test-contact-123",
        "name": "Jane Smith",
        "email": "jane@startup.com",
        "phone": "+1234567890",
        "companyName": "Tech Startup Inc",
        "source": "LinkedIn Ad",
        "tags": ["Startup", "B2B SaaS"],
        "customFields": {
            "company_size": "50-100",
            "industry": "Technology",
            "budget": "$50k+"
        }
    }
}

SAMPLE_HIGH_ENGAGEMENT_CONTACT = {
    "contact": {
        "id": "contact-789",
        "name": "Mike Johnson",
        "email": "mike@enterprise.com",
        "phone": "+9876543210",
        "companyName": "Enterprise Solutions LLC",
        "source": "Referral",
        "tags": ["Enterprise", "Decision Maker"],
        "dateAdded": "2026-03-15T08:00:00Z"
    },
    "engagement": {
        "email_opens": 15,
        "email_clicks": 8,
        "sms_replies": 3,
        "form_submissions": 3,
        "website_visits": 25,
        "call_duration_minutes": 45,
        "last_activity_date": "2026-04-01T09:00:00Z",
        "days_since_first_contact": 17
    }
}

SAMPLE_LOW_ENGAGEMENT_CONTACT = {
    "contact": {
        "id": "contact-999",
        "name": "Bob Williams",
        "email": "bob@example.com",
        "phone": None,
        "companyName": None,
        "source": "Cold List",
        "tags": [],
        "dateAdded": "2026-02-01T12:00:00Z"
    },
    "engagement": {
        "email_opens": 1,
        "email_clicks": 0,
        "sms_replies": 0,
        "form_submissions": 0,
        "website_visits": 0,
        "call_duration_minutes": 0,
        "last_activity_date": "2026-02-05T10:00:00Z",
        "days_since_first_contact": 60
    }
}


if __name__ == "__main__":
    """Run tests with: pytest test_api.py -v"""
    pytest.main([__file__, "-v"])
