# backend/managers/transaction_manager.py
from repositories.transaction_repo import TransactionRepo
from core.models import Transaction

class TransactionManager:
    @staticmethod
    def get_history(user_id: int, limit: int = 100):
        return TransactionRepo.get_for_user(user_id, limit)

    @staticmethod
    def get_totals(user_id: int):
        return TransactionRepo.get_totals(user_id)