# backend/managers/debt_manager.py
from repositories.debt_repo import DebtRepo
from repositories.user_repo import UserRepo
from repositories.transaction_repo import TransactionRepo
from typing import List, Dict, Tuple

class DebtManager:
    @staticmethod
    def create_debt_request(requester_id: int, counterparty_phone: str, amount: float, direction: str) -> Tuple[bool, str]:
        """
        Create a pending debt for the counterparty (phone entered) to accept.
        from_user_id = debtor, to_user_id = creditor.
        direction 'owe'  -> requester owes counterparty.
        direction 'owed' -> counterparty owes requester.
        """
        counterparty = UserRepo.get_by_phone(counterparty_phone)
        if not counterparty:
            return False, "User not found. They must register on CrediFlux first."
        if UserRepo.phones_match(requester_id, counterparty_phone):
            return False, "Enter the other person's phone number, not your own."
        if amount <= 0:
            return False, "Amount must be positive."

        if direction == 'owe':
            debtor_id, creditor_id = requester_id, counterparty.user_id
        elif direction == 'owed':
            debtor_id, creditor_id = counterparty.user_id, requester_id
        else:
            return False, "Invalid direction."

        req_id = DebtRepo.create_request(
            debtor_id=debtor_id,
            creditor_id=creditor_id,
            pending_for_user_id=counterparty.user_id,
            requested_by_user_id=requester_id,
            amount=amount,
        )
        if req_id:
            return True, f"Request sent to {counterparty.username}. They must accept it when they log in."
        return False, "Could not send request."

    @staticmethod
    def get_pending_requests(user_id: int) -> List[Dict]:
        return DebtRepo.get_pending_for_user(user_id)

    @staticmethod
    def accept_request(request_id: int, user_id: int) -> bool:
        req = DebtRepo.get_by_id(request_id)
        if not req or req.get('status') != 'pending':
            return False
        pending_for = req.get('pending_for_user_id')
        if pending_for is not None and pending_for != user_id:
            return False
        if pending_for is None and req.get('to_user_id') != user_id:
            return False
        return DebtRepo.accept_request(request_id)

    @staticmethod
    def reject_request(request_id: int, user_id: int) -> bool:
        req = DebtRepo.get_by_id(request_id)
        if not req or req.get('status') != 'pending':
            return False
        pending_for = req.get('pending_for_user_id')
        if pending_for is not None and pending_for != user_id:
            return False
        return DebtRepo.reject_request(request_id)

    @staticmethod
    def get_active_debts(user_id: int) -> List[Dict]:
        return DebtRepo.get_active_debts(user_id)

    @staticmethod
    def settle_global_optimized_payment(payer_user_id: int, creditor_user_id: int, payment_amount: float) -> bool:
        """
        Apply an optimized payment edge (debtor -> creditor).
        Handles direct edges and chain reduction (e.g. P1 pays P3 clears P2->P3 and P1->P2).
        """
        from repositories.settlement_repo import SettlementRepo
        from utils.balance_utils import get_global_balance_summary

        payer = UserRepo.get_by_id(payer_user_id)
        creditor = UserRepo.get_by_id(creditor_user_id)
        if not payer or not creditor:
            return False

        expected = 0.0
        for debtor, cred, amt in get_global_balance_summary(payer):
            if debtor == payer.username and cred == creditor.username:
                expected = amt
                break
        if expected <= 0 or abs(expected - payment_amount) > 0.02:
            return False

        remaining = round(payment_amount, 2)

        for debt in DebtRepo.list_accepted_owed_by(payer_user_id):
            if debt['to_user_id'] != creditor_user_id:
                continue
            pay = min(remaining, float(debt['amount']))
            if pay > 0 and DebtRepo.reduce_or_clear(debt['id'], pay):
                remaining = round(remaining - pay, 2)

        while remaining > 0.009:
            incoming = [
                d for d in DebtRepo.list_accepted_owed_to(creditor_user_id)
                if d['from_user_id'] != payer_user_id
            ]
            if not incoming:
                break
            debt_in = incoming[0]
            pay = min(remaining, float(debt_in['amount']))
            if pay <= 0:
                break
            if not DebtRepo.reduce_or_clear(debt_in['id'], pay):
                break
            mid_id = debt_in['from_user_id']
            for debt_out in DebtRepo.list_accepted_owed_by(payer_user_id):
                if debt_out['to_user_id'] == mid_id:
                    DebtRepo.reduce_or_clear(debt_out['id'], pay)
                    break
            remaining = round(remaining - pay, 2)

        for s in SettlementRepo.get_for_user(payer.username):
            if s.creditor_name != creditor.username or s.is_paid:
                continue
            pay = min(remaining, float(s.amount))
            if pay > 0 and SettlementRepo.reduce_or_mark_paid(s.settlement_id, pay):
                remaining = round(remaining - pay, 2)

        while remaining > 0.009:
            incoming_s = [
                s for s in SettlementRepo.get_owed_to_user(creditor.username)
                if not s.is_paid and s.debtor_name != payer.username
            ]
            if not incoming_s:
                break
            st = incoming_s[0]
            pay = min(remaining, float(st.amount))
            if pay <= 0:
                break
            if not SettlementRepo.reduce_or_mark_paid(st.settlement_id, pay):
                break
            for s_out in SettlementRepo.get_for_user(payer.username):
                if s_out.creditor_name == st.debtor_name and not s_out.is_paid:
                    SettlementRepo.reduce_or_mark_paid(s_out.settlement_id, pay)
                    break
            remaining = round(remaining - pay, 2)

        TransactionRepo.save(
            payer_user_id,
            f"Optimized payment via EasyPaisa to {creditor.username}",
            payment_amount,
            creditor.username,
        )
        return abs(remaining) < 0.02

    @staticmethod
    def settle_net_with_peer(payer_user_id: int, peer_user_id: int, payment_amount: float) -> bool:
        return DebtManager.settle_global_optimized_payment(payer_user_id, peer_user_id, payment_amount)

    @staticmethod
    def mark_direct_paid(debt_id: int, payer_user_id: int, creditor_name: str, amount: float, group_id=None) -> bool:
        success = DebtRepo.mark_paid(debt_id)
        if success:
            TransactionRepo.save(payer_user_id, f"Paid via EasyPaisa to {creditor_name}", amount, creditor_name, group_id)
            return True
        return False
