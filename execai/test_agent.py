import asyncio
from app.agents.core_agent import ExecAIAgent
from app.services.user_service import UserService
from app.db.session import get_db
from app.db.base import init_db

async def test_agent():
    init_db()
    db = next(get_db())
    # Create test user
    user_service = UserService(db)
    user = user_service.get_or_create_by_phone("+1234567890")
    
    agent = ExecAIAgent()
    response = await agent.process_message(
        message="Schedule a meeting with team tomorrow at 2pm about Q3 planning",
        user_context={"user_id": str(user.id), "name": user.name, "role": user.role},
        user_id=user.id
    )
    print("Agent Response:", response)

if __name__ == "__main__":
    asyncio.run(test_agent())