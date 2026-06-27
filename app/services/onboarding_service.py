"""Onboarding service for ExecAI."""

from typing import Dict, Any
from uuid import UUID
from app.services.user_service import UserService

class OnboardingService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def start_onboarding(self, user_id: UUID) -> str:
        """Send initial welcome and start onboarding."""
        return (
            "👋 Welcome to ExecAI! I'm your AI executive assistant on WhatsApp.\n\n"
            "I'll help you capture tasks, manage projects, and stay organized.\n\n"
            "First, what's your name?"
        )

    async def handle_onboarding_step(self, user_id: UUID, message: str, step: str) -> Dict:
        """Process onboarding responses."""
        # Logic to update user fields step by step
        if step == "name":
            # Update name, ask next question
            return {"next_step": "role", "response": "Great! What's your job title/role?"}
        # Add more steps...
        return {"next_step": None, "response": "Onboarding complete. How can I help today?"}
