import asyncio
from app.agents.core_agent import ExecAIAgent
from app.services.user_service import UserService
from app.db.base import SessionLocal, init_db

async def test_agent():
    init_db()
    with SessionLocal() as db:
        # Create test user
        user_service = UserService(db)
        user = user_service.get_or_create_by_phone("+1234567890")
        
        # Explicitly configure user timezone for validation
        from app.schemas.user import UserUpdate
        user_service.update(user.id, UserUpdate(timezone="America/New_York"))
        
        user_id = user.id
        user_name = user.name
        user_role = user.role
        user_tz = "America/New_York"
    
    agent = ExecAIAgent()
    
    # 1. Test Task Deletion Intent Routing
    response = await agent.process_message(
        message="Delete my gym inspection task",
        user_context={"user_id": str(user_id), "name": user_name, "role": user_role, "timezone": user_tz},
        user_id=user_id
    )
    print("Delete Task Agent Response:", response)
    
    # 2. Test Greeting Logic Continuity
    response_greet = await agent.process_message(
        message="Hello again",
        user_context={"user_id": str(user_id), "name": user_name, "role": user_role, "timezone": user_tz},
        user_id=user_id
    )
    print("Greetings Continuity Response:", response_greet)

if __name__ == "__main__":
    asyncio.run(test_agent())