"""LangChain Tools for ExecAI services."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, time
import logging
import pytz
from langchain_core.tools import tool
from pydantic import BaseModel

logger = logging.getLogger("execai.tools")

def get_user_timezone(user_id: UUID) -> pytz.timezone:
    """Retrieve database timezone preference or default to UTC."""
    from app.db.base import SessionLocal
    from app.models.user import User
    
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        tz_name = user.timezone if user and user.timezone else "UTC"
        try:
            return pytz.timezone(tz_name)
        except Exception:
            return pytz.utc

def format_datetime_with_tz(user_id: UUID, dt_str: Optional[str]) -> Optional[datetime]:
    """Parse datetime and localize it to the user's timezone preference."""
    if not dt_str:
        return None
    try:
        # Check standard ISO structure first
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        tz = get_user_timezone(user_id)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(tz)
        return dt
    except Exception as e:
        logger.warning(f"Failed to parse datetime: {dt_str}. Error: {e}")
        return None

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
async def google_auth_status_tool(user_id: UUID) -> str:
    """Check if the user has connected their Google Calendar."""
    from app.db.base import SessionLocal
    from app.models.user import User
    from app.utils.google_calendar import get_auth_url
    
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "User account not found."
        if user.google_calendar_connected:
            return "✅ Your Google Calendar account is connected successfully."
        else:
            auth_url = get_auth_url(user.whatsapp_phone)
            return (
                "❌ Your Google Calendar account is NOT connected.\n\n"
                f"Please authorize access by logging in here:\n{auth_url}"
            )

@tool
async def create_task_tool(user_id: UUID, title: str, description: Optional[str] = None, 
                         due_date: Optional[str] = None, priority: str = "medium") -> str:
    """Create a new task for the user."""
    from app.services.task_service import TaskService
    from app.schemas.task import TaskCreate
    from app.db.base import SessionLocal
    
    priority_map = {"low": 1, "medium": 3, "high": 5}
    prio_val = priority_map.get(priority.lower(), 3) if isinstance(priority, str) else priority

    parsed_due_date = format_datetime_with_tz(user_id, due_date)

    task_data = TaskCreate(
        title=title,
        description=description,
        due_date=parsed_due_date,
        priority=prio_val,
        status="pending"
    )
    
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
async def delete_task_tool(user_id: UUID, task_identifier: str) -> str:
    """Delete a task by title, ID, or match key. Use this for task removals."""
    from app.db.base import SessionLocal
    from app.models.task import Task
    import uuid
    
    with SessionLocal() as db:
        query = db.query(Task).filter(Task.user_id == user_id, Task.deleted_at.is_(None))
        
        # Check if UUID was provided
        try:
            target_uuid = uuid.UUID(task_identifier)
            task = query.filter(Task.id == target_uuid).first()
        except ValueError:
            # Match by case-insensitive name sub-match
            task = query.filter(Task.title.ilike(f"%{task_identifier}%")).first()
            
        if not task:
            # Look up the latest task if specified
            if "latest" in task_identifier.lower() or "last" in task_identifier.lower():
                task = query.order_by(Task.created_at.desc()).first()
                
        if task:
            task.deleted_at = datetime.utcnow()
            db.commit()
            return f"🗑️ Task '{task.title}' has been deleted successfully."
        return "Task not found."

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

@tool
async def create_event_tool(user_id: UUID, title: str, start_time: str, end_time: Optional[str] = None, 
                           recurrence_pattern: Optional[str] = None, location: Optional[str] = None,
                           description: Optional[str] = None) -> str:
    """
    Create a calendar event. If the user's Google Calendar is connected, 
    it syncs automatically, with support for RRULE list (recurrence_pattern).
    """
    from app.db.base import SessionLocal
    from app.models.user import User
    from app.models.event import Event
    from app.utils.google_calendar import create_google_calendar_event, get_auth_url
    
    parsed_start = format_datetime_with_tz(user_id, start_time)
    if not parsed_start:
        return "Error: Start time format invalid."
        
    if end_time:
        parsed_end = format_datetime_with_tz(user_id, end_time)
    else:
        # Default duration: 1 hour
        parsed_end = parsed_start + pytz.timezone("UTC").localize(datetime.min - datetime.min) # generic timedelta
        import datetime as dt_module
        parsed_end = parsed_start + dt_module.timedelta(hours=1)
        
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "User not found."
            
        gcal_event_id = None
        
        # RRULE recurrence parser
        rrule_list = None
        if recurrence_pattern:
            # Map shortcuts to standard Google Calendar RRULE strings
            pat = recurrence_pattern.upper()
            if "DAILY" in pat:
                rrule_list = ["RRULE:FREQ=DAILY"]
            elif "WEEKLY" in pat:
                rrule_list = ["RRULE:FREQ=WEEKLY"]
            elif "MONTHLY" in pat:
                rrule_list = ["RRULE:FREQ=MONTHLY"]
            elif "YEARLY" in pat:
                rrule_list = ["RRULE:FREQ=YEARLY"]
            elif "WEEKDAY" in pat:
                rrule_list = ["RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"]
            else:
                rrule_list = [f"RRULE:{recurrence_pattern}"]

        if user.google_calendar_connected:
            gcal_payload = {
                "summary": title,
                "description": description,
                "location": location,
                "start": {"dateTime": parsed_start.isoformat(), "timeZone": user.timezone},
                "end": {"dateTime": parsed_end.isoformat(), "timeZone": user.timezone},
            }
            if rrule_list:
                gcal_payload["recurrence"] = rrule_list
                
            gcal_event_id = await create_google_calendar_event(user, gcal_payload)
            if not gcal_event_id:
                logger.error("Failed to sync event with Google Calendar.")
        else:
            auth_url = get_auth_url(user.whatsapp_phone)
            return (
                "⚠️ Your Google Calendar is not connected. I cannot schedule calendar events "
                f"until you link your Google account here:\n{auth_url}"
            )
            
        # Write to local DB event table
        local_event = Event(
            user_id=user_id,
            title=title,
            start_time=parsed_start,
            end_time=parsed_end,
            location=location,
            description=description,
            google_calendar_event_id=gcal_event_id,
        )
        db.add(local_event)
        db.commit()
        
        recurrence_msg = f" (recurring: {recurrence_pattern})" if recurrence_pattern else ""
        return f"📅 Event '{title}' scheduled successfully{recurrence_msg}."

@tool
async def delete_event_tool(user_id: UUID, event_identifier: str) -> str:
    """Delete a calendar event by title, ID, or matching string."""
    from app.db.base import SessionLocal
    from app.models.user import User
    from app.models.event import Event
    from app.utils.google_calendar import delete_google_calendar_event
    import uuid
    
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "User not found."
            
        query = db.query(Event).filter(Event.user_id == user_id, Event.deleted_at.is_(None))
        
        try:
            target_uuid = uuid.UUID(event_identifier)
            event = query.filter(Event.id == target_uuid).first()
        except ValueError:
            event = query.filter(Event.title.ilike(f"%{event_identifier}%")).first()
            
        if not event:
            if "latest" in event_identifier.lower() or "last" in event_identifier.lower():
                event = query.order_by(Event.created_at.desc()).first()
                
        if event:
            if event.google_calendar_event_id:
                await delete_google_calendar_event(user, event.google_calendar_event_id)
            event.deleted_at = datetime.utcnow()
            db.commit()
            return f"🗑️ Event '{event.title}' has been deleted successfully."
        return "Event not found."

ALL_TOOLS = [
    create_task_tool, 
    list_tasks_tool, 
    complete_task_tool, 
    delete_task_tool,
    create_project_tool,
    create_event_tool,
    delete_event_tool,
    google_auth_status_tool
]