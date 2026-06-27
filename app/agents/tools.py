"""LangChain Tools for ExecAI services."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging
from langchain_core.tools import tool
from pydantic import BaseModel

logger = logging.getLogger("execai.tools")

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
    from app.db.base import SessionLocal
    
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

    # Handle datetime conversion safely if present
    parsed_due_date = None
    if due_date:
        try:
            parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        except Exception:
            logger.warning(f"Could not parse due_date: {due_date}. Leaving as None.")

    task_data = TaskCreate(
        title=title,
        description=description,
        due_date=parsed_due_date,
        priority=prio_val,
        status="pending"
    )
    
    # Secure session lifecycle using context manager to avoid leaks
    with SessionLocal() as db:
        service = TaskService(db)
        try:
            task = service.create(user_id, task_data)
            return f"✅ Task created successfully: {task.title} (ID: {task.id})"
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return f"Error creating task: {str(e)}"

@tool
async def list_tasks_tool(user_id: UUID, status: Optional[str] = None) -> str:
    """List user's tasks."""
    from app.services.task_service import TaskService
    from app.db.base import SessionLocal
    
    with SessionLocal() as db:
        service = TaskService(db)
        try:
            tasks = service.get_user_tasks(user_id, status)
            if not tasks:
                return "No tasks found."
            
            task_list = "\n".join([f"- {t.title} (Due: {t.due_date}, Status: {t.status})" for t in tasks])
            return f"Your tasks:\n{task_list}"
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return f"Error listing tasks: {str(e)}"

@tool
async def complete_task_tool(user_id: UUID, task_id: UUID) -> str:
    """Mark a task as completed."""
    from app.services.task_service import TaskService
    from app.db.base import SessionLocal
    
    with SessionLocal() as db:
        service = TaskService(db)
        try:
            task = service.complete(task_id)
            if task:
                return f"✅ Task completed: {task.title}"
            return "Task not found."
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return f"Error completing task: {str(e)}"

@tool
async def create_project_tool(user_id: UUID, title: str, description: Optional[str] = None) -> str:
    """Create a new project for the user."""
    from app.services.project_service import ProjectService
    from app.schemas.project import ProjectCreate
    from app.db.base import SessionLocal
    
    project_data = ProjectCreate(
        title=title,
        description=description,
        status="active",
        progress=0
    )
    
    with SessionLocal() as db:
        service = ProjectService(db)
        try:
            project = service.create(user_id, project_data)
            return f"✅ Project '{project.title}' created successfully (ID: {project.id})."
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return f"Error creating project: {str(e)}"

ALL_TOOLS = [create_task_tool, list_tasks_tool, complete_task_tool, create_project_tool]