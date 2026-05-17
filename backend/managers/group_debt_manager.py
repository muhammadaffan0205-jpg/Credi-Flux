# backend/managers/group_debt_manager.py
from repositories.group_debt_repo import GroupDebtRepo
from repositories.group_repo import GroupRepo
from repositories.user_repo import UserRepo
from repositories.expense_repo import ExpenseRepo
from repositories.settlement_repo import SettlementRepo
from typing import List, Dict, Tuple, Optional

class GroupDebtManager:
    @staticmethod
    def _display_name_in_group(group_id: int, user_id: int) -> Optional[str]:
        for p in GroupRepo.get_people(group_id):
            if p.user_id == user_id:
                return p.display_name
        user = UserRepo.get_by_id(user_id)
        return user.username if user else None

    @staticmethod
    def _user_in_group(group_id: int, user_id: int) -> bool:
        return any(p.user_id == user_id for p in GroupRepo.get_people(group_id))

    @staticmethod
    def create_request(
        group_id: int,
        requester_id: int,
        counterparty_user_id: int,
        amount: float,
        direction: str,
    ) -> Tuple[bool, str]:
        if not GroupDebtManager._user_in_group(group_id, requester_id):
            return False, "You are not in this group."
        if not GroupDebtManager._user_in_group(group_id, counterparty_user_id):
            return False, "That member is not in this group."
        if requester_id == counterparty_user_id:
            return False, "Select another member."
        if amount <= 0:
            return False, "Amount must be positive."
        counterparty = UserRepo.get_by_id(counterparty_user_id)
        if not counterparty:
            return False, "Member not found."

        if direction == 'owe':
            debtor_id, creditor_id = requester_id, counterparty_user_id
        elif direction == 'owed':
            debtor_id, creditor_id = counterparty_user_id, requester_id
        else:
            return False, "Invalid direction."

        rid = GroupDebtRepo.create_request(
            group_id, debtor_id, creditor_id, counterparty_user_id, requester_id, amount
        )
        if rid:
            return True, f"Request sent to {counterparty.username}. They must accept it on their dashboard."
        return False, "Could not send request."

    @staticmethod
    def get_pending_for_user(user_id: int) -> List[Dict]:
        return GroupDebtRepo.get_pending_for_user(user_id)

    @staticmethod
    def accept_request(request_id: int, user_id: int) -> Tuple[bool, str]:
        req = GroupDebtRepo.get_by_id(request_id)
        if not req or req.get('status') != 'pending':
            return False, "Request not found."
        if req['pending_for_user_id'] != user_id:
            return False, "You cannot accept this request."

        group_id = req['group_id']
        debtor_name = GroupDebtManager._display_name_in_group(group_id, req['debtor_user_id'])
        creditor_name = GroupDebtManager._display_name_in_group(group_id, req['creditor_user_id'])
        if not debtor_name or not creditor_name:
            return False, "Could not resolve group members."

        people = GroupRepo.get_people(group_id)
        desc = f"Debt: {debtor_name} owes {creditor_name}"
        ok, msg = ExpenseRepo.add_bilateral_debt(
            group_id, desc, debtor_name, creditor_name, float(req['amount']), people
        )
        if not ok:
            return False, msg

        raw = ExpenseRepo.get_balance_summary(group_id)
        SettlementRepo.save_settlements(group_id, raw)
        GroupDebtRepo.accept_request(request_id)
        return True, "Debt added to group. Balances updated."
