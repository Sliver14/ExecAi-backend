# ExecAI Production Readiness Audit Prompt

You are a Senior Python Backend Engineer, Senior DevOps Engineer, Senior
Security Engineer, and Senior QA Engineer.

Your task is to perform a COMPLETE production readiness audit and
refactor of this FastAPI + LangChain + WhatsApp Cloud API + OpenAI +
PostgreSQL (Neon) project.

Do NOT focus on one issue.

Instead, inspect the ENTIRE project like you are preparing it for a real
SaaS launch where hundreds of users will simultaneously interact with
the WhatsApp AI assistant.

## Project Goals

The application is an AI Executive Assistant that: - receives WhatsApp
messages - stores users in PostgreSQL (Neon) - manages projects -
manages tasks - manages events - uses OpenAI GPT - uses LangChain Tool
Calling - replies through WhatsApp Cloud API - is deployed on Railway

Target qualities: - production ready - scalable - reliable - secure -
maintainable

## Audit Scope

Inspect and improve:

1.  FastAPI Architecture

-   app/main.py
-   routers
-   middleware
-   lifespan
-   startup/shutdown
-   health/readiness endpoints
-   exception handling
-   logging

2.  WhatsApp Integration

-   webhook verification
-   GET/POST webhook
-   payload parsing
-   Cloud API compatibility
-   Graph API requests
-   retries
-   async HTTP
-   signature validation
-   duplicate webhook handling
-   unsupported message handling

3.  OpenAI Integration

-   connection reuse
-   retries
-   timeout handling
-   model lifecycle
-   error recovery

4.  LangChain

-   deprecated imports
-   tool calling
-   AgentExecutor
-   prompts
-   MessagesPlaceholder
-   compatibility

5.  Database

-   SQLAlchemy
-   Neon PostgreSQL
-   pooling
-   transactions
-   relationships
-   indexes
-   session lifecycle

6.  Alembic

-   migrations
-   imports
-   PostgreSQL compatibility
-   DATABASE_URL

7.  Railway

-   startup
-   Docker/Nixpacks
-   health checks
-   migrations
-   environment variables

8.  Environment Variables Verify all required variables exist and fail
    fast if missing.

9.  Logging Replace print() with structured logging.

10. Security Audit secrets, validation, webhook signature verification,
    prompt injection mitigation.

11. Performance Review database access, async usage, HTTP clients,
    caching opportunities.

12. AI Agent Audit complete execution flow, memory, tools, conversation
    handling.

13. Services Audit TaskService, ProjectService, EventService and others.

14. Error Handling No silent failures. Log exceptions with stack traces.

15. WhatsApp Client Replace any mock implementation with a production
    implementation using httpx.AsyncClient.

16. Code Quality Remove dead code, duplicate code, unused imports and
    legacy patterns.

17. Scalability Prepare for hundreds of concurrent WhatsApp users.

18. Testing Generate unit, integration, webhook and database tests.

19. Documentation Update README, deployment guide, Railway setup, Neon
    setup, Meta setup.

20. End-to-End Validation Simulate: WhatsApp User → Meta Webhook →
    FastAPI → User Lookup → Database → AI Agent → Tool Calling →
    Database → OpenAI → WhatsApp Cloud API → User receives reply

## Deliverables

For every issue provide: - Severity (Critical/High/Medium/Low) - File -
Root cause - Updated code - Reason for change - Production impact -
Security impact - Performance impact

Finally provide: - Production Readiness Score (0--100%) - Remaining
blockers - Launch checklist - Railway checklist - Neon checklist -
WhatsApp Cloud API checklist - Monitoring & alerting checklist -
Recommended future improvements

Do not stop until the entire codebase has been reviewed and all
production-critical issues have been fixed or documented.
