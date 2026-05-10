# crediflux/managers/debt_manager.py
from repositories.debt_repo import DebtRepo
from repositories.user_repo import UserRepo
from repositories.transaction_repo import TransactionRepo
from typing import Tuple, Optional, List, Dict

class DebtManager:
    @staticmethod
    def request_debt(from_user_id: int, to_phone: str, amount: float) -> Tuple[bool, str]:
        """Create a pending debt request (from_user_id owes amount to phone owner)."""
        user = UserRepo.get_by_phone(to_phone)
        if not user:
            return False, "User with this phone number not found."
        if user.user_id == from_user_id:
            return False, "You cannot send a request to yourself."
        if amount <= 0:
            return False, "Amount must be positive."
        req_id = DebtRepo.create_request(from_user_id, user.user_id, amount)
        if req_id:
            print(f"[DEBUG] Created debt request ID {req_id} from {from_user_id} to {user.user_id}")
            return True, f"Request sent to {user.username}."
        else:
            return False, "Could not send request."

    @staticmethod
    def get_pending_requests(user_id: int) -> List[Dict]:
        """Return list of pending debt requests for the user (where user is creditor)."""
        return DebtRepo.get_pending_for_user(user_id)

    @staticmethod
    def accept_request(request_id: int) -> bool:
        return DebtRepo.accept_request(request_id)

    @staticmethod
    def reject_request(request_id: int) -> bool:
        return DebtRepo.reject_request(request_id)

    @staticmethod
    def get_active_debts(user_id: int) -> List[Dict]:
        """Return all accepted debts involving this user (both as debtor and creditor)."""
        return DebtRepo.get_active_debts(user_id)

    @staticmethod
    def mark_direct_paid(debt_id: int, payer_user_id: int, creditor_name: str, amount: float, group_id: int = None) -> bool:
        """
        Mark a direct (peer‑to‑peer) debt as paid.
        Deletes the debt record and logs a transaction.
        """
        from repositories.debt_repo import DebtRepo
        from repositories.transaction_repo import TransactionRepo
        success = DebtRepo.mark_paid(debt_id)
        if success:
            TransactionRepo.save(payer_user_id, f"Paid via EasyPaisa to {creditor_name}", amount, creditor_name, group_id)
            return True
        return False