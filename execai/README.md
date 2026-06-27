# ExecAI - AI Executive Assistant for WhatsApp

## Status
**MVP Core Complete** - Ready for local testing.

## Features Implemented
- ✅ PostgreSQL Schema + Models
- ✅ FastAPI + WhatsApp Webhook
- ✅ LangChain Agent (GPT-4o-mini) with structured extraction
- ✅ Full Service Layer (Tasks, Projects, Events, Reviews)
- ✅ User onboarding skeleton
- ✅ Enhanced Prompts
- ✅ Alembic ready
- ✅ Local setup

## Local Setup
1. Copy `.env.example` → `.env` and fill keys
2. Setup Postgres DB: `createdb execai`
3. `psql -d execai -f schema.sql`
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --reload`
6. Use ngrok for WhatsApp webhook testing

## Next Steps
- Connect real WhatsApp Business API
- Add cron for daily/weekly check-ins
- Testing & tuning prompts
- Stripe integration for SaaS