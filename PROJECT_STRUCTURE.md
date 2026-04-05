# Project Structure

```
ai-lead-scoring/
│
├── main.py                 # FastAPI application & webhook endpoints
├── config.py              # Environment configuration
├── models.py              # Pydantic data models
├── lead_scorer.py         # AI scoring engine (GPT-4)
├── ghl_client.py          # GoHighLevel API client
├── slack_notifier.py      # Slack notification service
│
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
│
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Docker Compose configuration
├── setup.sh              # Quick start script
│
├── test_api.py           # API tests & sample payloads
└── README.md             # Full documentation
```

## File Descriptions

### Core Application Files

- **main.py**: FastAPI server with two main endpoints:
  - `POST /webhook/ghl/contact`: Main webhook receiver
  - `POST /test/score`: Manual testing endpoint
  - Handles full workflow: receive → fetch → score → route → notify

- **lead_scorer.py**: AI scoring engine
  - Uses GPT-4 to evaluate leads on 3 dimensions
  - Structured JSON output for consistent parsing
  - Batch scoring support for high volume

- **ghl_client.py**: GoHighLevel integration
  - Fetch contact details and engagement data
  - Update contacts (tags, assignment, custom fields)
  - Add notes for audit trail

- **slack_notifier.py**: Slack integration
  - Rich block-based messages for hot leads
  - Error alerting capabilities
  - Async notification delivery

### Configuration & Models

- **config.py**: Centralized settings management
  - Loads from environment variables
  - Type-safe configuration with Pydantic
  - Defaults for local development

- **models.py**: Data validation schemas
  - Request/response models
  - Type safety and validation
  - API documentation auto-generation

### Deployment Files

- **Dockerfile**: Production container image
  - Python 3.11 slim base
  - Multi-stage build for smaller size
  - Health check included

- **docker-compose.yml**: Local development setup
  - Auto-reload on code changes
  - Volume mounting for live editing
  - Environment variable injection

### Testing & Documentation

- **test_api.py**: Test suite with pytest
  - Sample webhook payloads
  - High/low engagement scenarios
  - Health check validation

- **README.md**: Complete documentation
  - Setup instructions
  - API reference
  - Deployment guides
  - Troubleshooting tips

## Key Design Decisions

1. **Async Architecture**: All I/O operations use async/await for non-blocking performance
2. **Modular Services**: Each integration (GHL, OpenAI, Slack) is isolated in its own client
3. **Type Safety**: Pydantic models throughout for validation and auto-docs
4. **Error Handling**: Try/catch blocks with logging, graceful degradation
5. **Configurability**: All business logic (tier thresholds, routing) easily adjustable
