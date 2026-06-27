from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from typing import Dict, Any
from ..models.review import WeeklyReview
from ..models.task import Task
from ..models.project import Project

class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def generate_weekly_review(self, user_id: UUID) -> Dict[str, Any]:
        # This will be enhanced with AI later
        today = datetime.utcnow()
        week_start = today - timedelta(days=7)

        completed_tasks = self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.completed_at >= week_start
        ).all()

        active_projects = self.db.query(Project).filter(
            Project.user_id == user_id,
            Project.deleted_at.is_(None)
        ).all()

        total_tasks = self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.deleted_at.is_(None)
        ).count()

        review = WeeklyReview(
            user_id=user_id,
            week_start=week_start.date(),
            completed_tasks=len(completed_tasks),
            total_tasks=total_tasks,
            insights={"details": "AI-generated insights will go here."},
            reflection={},
            planned_priorities=[]
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        return {
            "review_id": str(review.id),
            "completed": len(completed_tasks),
            "active_projects": len(active_projects),
            "insights": review.insights
        }

