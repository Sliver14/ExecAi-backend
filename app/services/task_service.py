from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from ..models.task import Task
from ..schemas.task import TaskCreate, TaskUpdate

class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: UUID, data: TaskCreate) -> Task:
        task = Task(user_id=user_id, **data.model_dump())
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task_id: UUID, data: TaskUpdate) -> Optional[Task]:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task:
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(task, key, value)
            self.db.commit()
            self.db.refresh(task)
        return task

    def complete(self, task_id: UUID) -> Optional[Task]:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(task)
        return task

    def get_user_tasks(self, user_id: UUID, status: str = None) -> List[Task]:
        query = self.db.query(Task).filter(Task.user_id == user_id, Task.deleted_at.is_(None))
        if status:
            query = query.filter(Task.status == status)
        return query.all()
