from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from ..models.project import Project
from ..schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: UUID, data: ProjectCreate) -> Project:
        project = Project(user_id=user_id, **data.model_dump())
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_user_projects(self, user_id: UUID) -> List[Project]:
        return self.db.query(Project).filter(
            Project.user_id == user_id,
            Project.deleted_at.is_(None)
        ).all()
