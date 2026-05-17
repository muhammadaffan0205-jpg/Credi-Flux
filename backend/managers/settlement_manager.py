# backend/managers/settlement_manager.py
from repositories.settlement_repo import SettlementRepo
from repositories.transaction_repo import TransactionRepo
from core.models import Settlement

class SettlementManager:
    @staticmethod
    def get_for_group(group_id: int):
        return SettlementRepo.get_for_group(group_id)

    @staticmethod
    def get_pending_for_user(username: str):
        return SettlementRepo.get_for_user(username)

    @staticmethod
    def confirm_paid(settlement: Settlement, paying_user_id: int) -> bool:
        ok = SettlementRepo.mark_paid(settlement.settlement_id)
        if ok:
            TransactionRepo.save(paying_user_id, f"Paid via EasyPaisa to {settlement.creditor_name}",
                                 settlement.amount, settlement.creditor_name, settlement.group_id)
        return ok

    @staticmethod
    def mark_paid_by_id(settlement_id: int) -> bool:
        return SettlementRepo.mark_paid(settlement_id)