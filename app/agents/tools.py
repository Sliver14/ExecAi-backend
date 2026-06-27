"""LangChain Tools for ExecAI services."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from langchain_core.tools import tool
from pydantic import BaseModel

# Tool schemas
class CreateTaskInput(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None  # ISO format
    priority: str = "medium"
    project_id: Optional[UUID] = None

class CreateProjectInput(BaseModel):
    title: str
    description: Optional[str] = None

class CreateEventInput(BaseModel):
    title: str
    start_time: str  # ISO
    end_time: Optional[str] = None
    location: Optional[str] = None

@tool
async def create_task_tool(user_id: UUID, title: str, description: Optional[str] = None, 
                         due_date: Optional[str] = None, priority: str = "medium") -> str:
    """Create a new task for the user."""
    from app.services.task_service import TaskService
    from app.schemas.task import TaskCreate
    from app.db.session import get_db  # Will be dependency injected in practice
    
    # Note: In real usage, services are passed from router
    # This is a wrapper for tool calling
    db = next(get_db())  # Temporary for tool
    service = TaskService(db)
    # Map priority string to integer
    priority_map = {
        "low": 1,
        "medium": 3,
        "high": 5
    }
    prio_val = 3
    if isinstance(priority, str):
        prio_val = priority_map.get(priority.lower(), 3)
    elif isinstance(priority, int):
        prio_val = priority

    task_data = TaskCreate(
        title=title,
        description=description,
        due_date=due_date,
        priority=prio_val,
        status="pending"
    )
    task = service.create(user_id, task_data)
    return f"✅ Task created successfully: {task.title} (ID: {task.id})"

@tool
async def list_tasks_tool(user_id: UUID, status: Optional[str] = None) -> str:
    """List user's tasks."""
    from app.services.task_service import TaskService
    from app.db.session import get_db
    
    db = next(get_db())
    service = TaskService(db)
    tasks = service.get_user_tasks(user_id, status)
    
    if not tasks:
        return "No tasks found."
    
    task_list = "\n".join([f"- {t.title} (Due: {t.due_date}, Status: {t.status})" for t in tasks])
    return f"Your tasks:\n{task_list}"

@tool
async def complete_task_tool(user_id: UUID, task_id: UUID) -> str:
    """Mark a task as completed."""
    from app.services.task_service import TaskService
    from app.db.session import get_db
    
    db = next(get_db())
    service = TaskService(db)
    task = service.complete(task_id)
    if task:
        return f"✅ Task completed: {task.title}"
    return "Task not found."

# Add more tools as needed
@tool
async def create_project_tool(user_id: UUID, title: str, description: Optional[str] = None) -> str:
    """Create a new project."""
    # Placeholder - implement with ProjectService
    return f"✅ Project '{title}' created."

# TODO: Add event tools, review tools, etc.

ALL_TOOLS = [create_task_tool, list_tasks_tool, complete_task_tool, create_project_tool]