"""
HubSpot API Client (Free CRM)
Documentation: https://developers.hubspot.com/docs/api/overview
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class HubSpotClient:
    """
    Client for interacting with HubSpot CRM API
    
    Free tier includes:
    - Contact management
    - Custom properties
    - Webhooks
    - API access
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """
        Fetch contact details by ID
        
        Args:
            contact_id: HubSpot contact ID (vid)
            
        Returns:
            Contact data dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                # Fetch contact with all properties
                response = await client.get(
                    f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                    headers=self.headers,
                    params={
                        "properties": [
                            "email", "firstname", "lastname", "company", 
                            "phone", "hs_lead_status", "lifecyclestage",
                            "jobtitle", "city", "state", "country",
                            "website", "hs_analytics_source",
                            "createdate", "lastmodifieddate"
                        ]
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Format for our system
                properties = data.get("properties", {})
                contact_data = {
                    "id": data.get("id"),
                    "name": f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
                    "email": properties.get("email"),
                    "phone": properties.get("phone"),
                    "companyName": properties.get("company"),
                    "source": properties.get("hs_analytics_source", "Unknown"),
                    "title": properties.get("jobtitle"),
                    "location": f"{properties.get('city', '')}, {properties.get('state', '')}".strip(", "),
                    "lifecycle_stage": properties.get("lifecyclestage"),
                    "lead_status": properties.get("hs_lead_status"),
                    "tags": [],  # HubSpot doesn't use tags, uses properties
                    "customFields": properties,
                    "dateAdded": properties.get("createdate")
                }
                
                logger.info(f"Fetched HubSpot contact {contact_id}")
                return contact_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching contact {contact_id}: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error fetching contact {contact_id}: {str(e)}")
            raise
    
    async def get_contact_engagement(self, contact_id: str) -> Dict[str, Any]:
        """
        Fetch engagement metrics for a contact
        
        HubSpot tracks:
        - Email engagement (opens, clicks)
        - Meeting scheduled/completed
        - Form submissions
        - Page views
        - Call activity
        
        Args:
            contact_id: HubSpot contact ID
            
        Returns:
            Engagement metrics dictionary
        """
        try:
            engagement_data = {
                "email_opens": 0,
                "email_clicks": 0,
                "meetings_scheduled": 0,
                "form_submissions": 0,
                "website_visits": 0,
                "call_duration_minutes": 0,
                "last_activity_date": None,
                "days_since_first_contact": 0
            }
            
            async with httpx.AsyncClient() as client:
                # Get engagements associated with contact
                response = await client.get(
                    f"{self.base_url}/crm/v3/objects/contacts/{contact_id}/associations/engagements",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    associations = response.json()
                    
                    # Count engagement types
                    for assoc in associations.get("results", []):
                        engagement_type = assoc.get("type", "").lower()
                        
                        if "email" in engagement_type:
                            engagement_data["email_opens"] += 1
                        elif "meeting" in engagement_type:
                            engagement_data["meetings_scheduled"] += 1
                        elif "call" in engagement_type:
                            engagement_data["call_duration_minutes"] += 5  # Estimate
                
                # Get contact properties for additional engagement data
                contact_response = await client.get(
                    f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                    headers=self.headers,
                    params={
                        "properties": [
                            "num_conversion_events",
                            "hs_email_open", 
                            "hs_email_click",
                            "num_contacted_notes",
                            "notes_last_updated",
                            "createdate"
                        ]
                    },
                    timeout=30.0
                )
                
                if contact_response.status_code == 200:
                    props = contact_response.json().get("properties", {})
                    
                    # Update with actual metrics
                    if props.get("hs_email_open"):
                        engagement_data["email_opens"] = int(props.get("hs_email_open", 0))
                    if props.get("hs_email_click"):
                        engagement_data["email_clicks"] = int(props.get("hs_email_click", 0))
                    if props.get("num_conversion_events"):
                        engagement_data["form_submissions"] = int(props.get("num_conversion_events", 0))
                    
                    # Calculate days since creation
                    if props.get("createdate"):
                        create_date = datetime.fromisoformat(props["createdate"].replace("Z", "+00:00"))
                        days_diff = (datetime.now(create_date.tzinfo) - create_date).days
                        engagement_data["days_since_first_contact"] = days_diff
                    
                    engagement_data["last_activity_date"] = props.get("notes_last_updated")
            
            logger.info(f"Fetched engagement data for HubSpot contact {contact_id}")
            return engagement_data
            
        except Exception as e:
            logger.error(f"Error fetching engagement for {contact_id}: {str(e)}")
            # Return empty engagement rather than failing
            return {
                "email_opens": 0,
                "email_clicks": 0,
                "meetings_scheduled": 0,
                "form_submissions": 0,
                "website_visits": 0,
                "call_duration_minutes": 0,
                "last_activity_date": None,
                "days_since_first_contact": 0
            }
    
    async def update_contact(
        self,
        contact_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update contact properties in HubSpot
        
        Args:
            contact_id: HubSpot contact ID
            update_data: Dictionary with update fields
            
        Returns:
            Updated contact data
        """
        try:
            # Build properties payload
            properties = {}
            
            # Map our fields to HubSpot properties
            if "customField" in update_data:
                custom = update_data["customField"]
                if "ai_lead_score" in custom:
                    properties["ai_lead_score"] = str(custom["ai_lead_score"])
                if "ai_score_reasoning" in custom:
                    properties["ai_score_reasoning"] = custom["ai_score_reasoning"]
            
            # Set lead status based on tier
            if "tier" in update_data:
                tier = update_data["tier"]
                if tier == "hot":
                    properties["hs_lead_status"] = "OPEN"
                    properties["lifecyclestage"] = "salesqualifiedlead"
                elif tier == "warm":
                    properties["hs_lead_status"] = "IN_PROGRESS"
                    properties["lifecyclestage"] = "marketingqualifiedlead"
                else:
                    properties["hs_lead_status"] = "NEW"
                    properties["lifecyclestage"] = "lead"
            
            # Update contact owner (assignment)
            if "assignedTo" in update_data:
                properties["hubspot_owner_id"] = update_data["assignedTo"]
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                    headers=self.headers,
                    json={"properties": properties},
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Updated HubSpot contact {contact_id}")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating contact {contact_id}: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {str(e)}")
            raise
    
    async def create_note(
        self,
        contact_id: str,
        note_text: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Add a note to contact (for audit trail)
        
        Args:
            contact_id: HubSpot contact ID
            note_text: Note content
            user_id: Optional owner ID
            
        Returns:
            Success boolean
        """
        try:
            note_body = {
                "properties": {
                    "hs_note_body": note_text,
                    "hs_timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            if user_id:
                note_body["properties"]["hubspot_owner_id"] = user_id
            
            async with httpx.AsyncClient() as client:
                # Create the note
                note_response = await client.post(
                    f"{self.base_url}/crm/v3/objects/notes",
                    headers=self.headers,
                    json=note_body,
                    timeout=30.0
                )
                note_response.raise_for_status()
                note_id = note_response.json()["id"]
                
                # Associate note with contact
                assoc_response = await client.put(
                    f"{self.base_url}/crm/v3/objects/notes/{note_id}/associations/contacts/{contact_id}/note_to_contact",
                    headers=self.headers,
                    timeout=30.0
                )
                assoc_response.raise_for_status()
                
                logger.info(f"Created note for HubSpot contact {contact_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating note for {contact_id}: {str(e)}")
            return False
    
    async def get_owner_id_by_email(self, email: str) -> Optional[str]:
        """
        Get HubSpot owner ID by email
        
        Args:
            email: Owner's email address
            
        Returns:
            Owner ID or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/crm/v3/owners",
                    headers=self.headers,
                    params={"email": email},
                    timeout=30.0
                )
                response.raise_for_status()
                
                results = response.json().get("results", [])
                if results:
                    return results[0]["id"]
                return None
                
        except Exception as e:
            logger.error(f"Error getting owner by email {email}: {str(e)}")
            return None
