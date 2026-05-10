# crediflux/managers/settlement_manager.py
from repositories.settlement_repo import SettlementRepo
from repositories.transaction_repo import TransactionRepo
from core.models import Settlement
from typing import List

class SettlementManager:
    @staticmethod
    def get_for_group(group_id: int) -> List[Settlement]:
        return SettlementRepo.get_for_group(group_id)

    @staticmethod
    def get_pending_for_user(username: str) -> List[Settlement]:
        return SettlementRepo.get_for_user(username)

    @staticmethod
    def confirm_paid(settlement: Settlement, paying_user_id: int) -> bool:
        ok = SettlementRepo.mark_paid(settlement.settlement_id)
        if ok:
            TransactionRepo.save(
                user_id     = paying_user_id,
                description = f"Paid via EasyPaisa to {settlement.creditor_name}",
                amount      = settlement.amount,
                paid_to     = settlement.creditor_name,
                group_id    = settlement.group_id,
            )
        return ok

    @staticmethod
    def mark_paid_by_id(settlement_id: int) -> bool:
        return SettlementRepo.mark_paid(settlement_id)