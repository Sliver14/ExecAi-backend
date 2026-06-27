# ExecAI - AI Executive Assistant for WhatsApp

## Project Status (MVP)
- ✅ PostgreSQL Schema + SQLAlchemy Models
- ✅ FastAPI + WhatsApp Webhook
- ✅ LangChain Agent with GPT-4o-mini
- ✅ Full Service Layer (User, Task, Project, Event, Review)
- ✅ Onboarding skeleton
- ✅ Enhanced prompts
- 🔄 Next: Full tool calling, cron jobs for reminders/reviews, tests, real WhatsApp API config

## Local Setup
1. `cd execai`
2. `python -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` → `.env` and fill keys
5. Setup Postgres DB and run `psql -d execai -f schema.sql`
6. `uvicorn app.main:app --reload --port 8000`

For webhook testing use ngrok.

## Architecture
- **WhatsApp** → FastAPI Webhook → User Context → LangChain Agent → Services → DB + Response
# ExecAi-backend
