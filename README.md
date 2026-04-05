# AI Lead Scoring System (100% FREE - Groq + HubSpot)

Automated lead qualification workflow that analyzes new CRM contacts, calculates engagement-based scores using **Groq's Llama 3.3 70B** (free AI), and automatically routes leads in **HubSpot CRM** (free tier) with Slack notifications.

## Why This Stack?

- **Groq AI**: FREE, fast, no credit card needed
- **HubSpot CRM**: FREE tier with full API access
- **Total cost**: $0/month (perfect for learning, testing, small business)

## Features

- **Webhook Integration**: Receives new contact events from HubSpot
- **AI-Powered Scoring**: Uses Groq's Llama 3.3 70B (FREE!)
- **Automatic Routing**: Segments leads into Hot (≥80), Warm (40-79), and Cold (<40) tiers
- **CRM Updates**: Automatically updates contact properties and assigns owners in HubSpot
- **Slack Alerts**: Real-time notifications for high-priority hot leads
- **Async Architecture**: Non-blocking operations for high throughput
- **100% Free Stack**: No subscription costs - Groq + HubSpot free tiers

## Architecture

```
Webhook Trigger → Fetch Contact Data → AI Scoring (Groq Llama 3.3) → Determine Tier → Update CRM → Slack Alert (if hot)
```

### Scoring Logic

The AI evaluates three dimensions:

1. **Engagement (40%)**: Email opens/clicks, website visits, form submissions, response rate
2. **Fit (35%)**: Company size, industry, role, budget indicators, geographic match
3. **Intent (25%)**: Demo requests, pricing inquiries, urgency signals, problem severity

**Tier Assignment:**
- **Hot (≥80)**: High intent + strong fit → Top sales rep + Slack alert
- **Warm (40-79)**: Moderate interest → Secondary rep
- **Cold (<40)**: Low engagement/poor fit → Nurture pipeline

## Setup

### Prerequisites

- Python 3.11+
- Groq API key (FREE - no credit card)
- HubSpot account (FREE tier)
- Slack workspace with webhook access (optional)

### Installation

1. **Clone and navigate to the project:**
```bash
cd ai-lead-scoring
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your actual API keys and configuration
```

Required variables:
- `GROQ_API_KEY`: Your Groq API key (FREE!)
- `HUBSPOT_API_KEY`: Your HubSpot private app token (FREE!)
- `HUBSPOT_PORTAL_ID`: Your HubSpot account ID
- `SLACK_WEBHOOK_URL`: Slack incoming webhook URL (optional)
- `HOT_LEAD_OWNER_ID`: HubSpot user ID for hot lead assignment
- `WARM_LEAD_OWNER_ID`: HubSpot user ID for warm lead assignment
- `COLD_LEAD_OWNER_ID`: HubSpot user ID for cold lead assignment

### Getting API Keys

**Groq (FREE & Fast):**
1. Go to https://console.groq.com
2. Sign up with Google/GitHub
3. Create new API key
4. Copy to `.env` as `GROQ_API_KEY`
5. No credit card required!

**HubSpot (FREE CRM):**
1. Create free account at https://www.hubspot.com/products/get-started
2. Go to Settings → Integrations → Private Apps
3. Create app with contact read/write scopes
4. Copy token to `.env` as `HUBSPOT_API_KEY`
5. Get Portal ID from URL
6. **See HUBSPOT_SETUP.md for detailed guide**

**Slack:**
1. Go to https://api.slack.com/apps
2. Create new app → Incoming Webhooks
3. Activate and add webhook to channel
4. Copy webhook URL to `.env` as `SLACK_WEBHOOK_URL`

**GHL User IDs:**
1. In GHL, go to Settings > Team
2. Click on each user and copy their ID from the URL
3. Set as `HOT_LEAD_OWNER_ID`, `WARM_LEAD_OWNER_ID`, `COLD_LEAD_OWNER_ID`

## Running the Server

### Development Mode

```bash
python main.py
```

Server runs at `http://localhost:8000`

API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### `POST /webhook/ghl/contact`

Main webhook endpoint for GoHighLevel contact events.

**Request:**
```json
{
  "contact_id": "abc123",
  "event_type": "contact.created",
  "location_id": "loc_xyz"
}
```

**Response:**
```json
{
  "contact_id": "abc123",
  "score": 85,
  "tier": "hot",
  "reasoning": "Strong engagement with 5 email opens and 2 form submissions. Decision-maker title at enterprise company. Recent demo request indicates high intent.",
  "timestamp": "2026-04-01T10:30:00Z",
  "success": true
}
```

### `POST /test/score`

Test endpoint for manual scoring.

**Request:**
```json
{
  "contact": {
    "name": "John Doe",
    "email": "john@example.com",
    "companyName": "Acme Corp",
    "source": "Website Form"
  },
  "engagement": {
    "email_opens": 5,
    "email_clicks": 2,
    "website_visits": 8,
    "form_submissions": 1
  }
}
```

### `GET /`

Health check endpoint.

## GoHighLevel Webhook Setup

1. Log into GoHighLevel
2. Go to Settings > Integrations > Webhooks
3. Create new webhook:
   - **Event**: Contact Created
   - **URL**: `https://your-domain.com/webhook/ghl/contact`
   - **Method**: POST
4. Save and test

## Deployment

### Docker (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t ai-lead-scorer .
docker run -p 8000:8000 --env-file .env ai-lead-scorer
```

### Cloud Platforms

**Railway:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Deploy
railway login
railway init
railway up
```

**Render:**
1. Connect GitHub repo
2. Create new Web Service
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env`

**AWS Lambda + API Gateway:**
Use `mangum` adapter:
```bash
pip install mangum
```

Update `main.py`:
```python
from mangum import Mangum
handler = Mangum(app)
```

## Testing

Test with curl:
```bash
curl -X POST http://localhost:8000/test/score \
  -H "Content-Type: application/json" \
  -d '{
    "contact": {
      "name": "Test Lead",
      "email": "test@example.com",
      "companyName": "Test Corp"
    },
    "engagement": {
      "email_opens": 10,
      "website_visits": 5
    }
  }'
```

## Monitoring & Logging

Logs are written to stdout in structured format:
```
2026-04-01 10:30:00 - main - INFO - Received webhook: {...}
2026-04-01 10:30:01 - lead_scorer - INFO - Lead scored: 85/100
2026-04-01 10:30:02 - ghl_client - INFO - Updated contact abc123
```

For production, integrate with:
- **Sentry** for error tracking
- **Datadog** or **CloudWatch** for metrics
- **Papertrail** or **LogDNA** for log aggregation

## Customization

### Adjust Scoring Criteria

Edit `lead_scorer.py` → `_get_system_prompt()` to modify:
- Weight distribution (engagement/fit/intent)
- Tier thresholds (hot/warm/cold)
- Scoring factors

### Add Custom Engagement Metrics

Edit `ghl_client.py` → `get_contact_engagement()` to fetch:
- Call recordings
- Meeting attendance
- Proposal views
- Contract interactions

### Modify Routing Logic

Edit `main.py` → `build_ghl_update()` to customize:
- Tag naming conventions
- Pipeline stage assignments
- Custom field updates

## Troubleshooting

**Webhook not triggering:**
- Verify webhook URL is publicly accessible
- Check GHL webhook logs for errors
- Ensure contact events are enabled

**AI scoring errors:**
- Verify OpenAI API key is valid
- Check API quota/rate limits
- Review prompt format in logs

**GHL update failures:**
- Confirm API key has write permissions
- Verify user IDs exist in your account
- Check custom field names match your CRM

**Slack notifications not sending:**
- Test webhook URL directly
- Verify channel permissions
- Check webhook app is installed

## Future Enhancements

- [ ] Real-time engagement tracking via GHL events
- [ ] Historical scoring accuracy metrics
- [ ] A/B test different scoring prompts
- [ ] Multi-language support for international leads
- [ ] Integration with sales calendars for auto-booking
- [ ] Predictive lead scoring based on closed-won patterns

## License

MIT

## Support

For issues or questions, open a GitHub issue or contact your system administrator..
