# crediflux/managers/due_dates_manager.py
from typing import List, Dict

class DueDatesManager:
    @staticmethod
    def get_upcoming_due_dates(user_id: int, limit: int = 5) -> List[Dict]:
        return [
            {
                "description": "📌 Full due date tracking coming soon!",
                "days_left": "Soon",
                "group_name": "In development"
            }
        ]