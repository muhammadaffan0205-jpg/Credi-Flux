# backend/managers/payment_reminder_manager.py
from repositories.payment_reminder_repo import PaymentReminderRepo
from repositories.debt_repo import DebtRepo
from repositories.settlement_repo import SettlementRepo
from repositories.user_repo import UserRepo
from typing import Tuple, Optional

class PaymentReminderManager:
    @staticmethod
    def send_reminder(creditor_id: int, debtor_username: str, amount: float,
                      direct_debt_id=None, settlement_id=None, net_payment: bool = False) -> Tuple[bool, str]:
        debtor = UserRepo.get_by_username(debtor_username)
        if not debtor:
            return False, "Debtor not found."
        if debtor.user_id == creditor_id:
            return False, "Invalid debtor."

        did = sid = None
        if net_payment:
            pass
        elif direct_debt_id is not None:
            debt = DebtRepo.get_by_id(int(direct_debt_id))
            if not debt or debt.get('status') != 'accepted':
                return False, "Invalid direct debt."
            if debt['from_user_id'] != debtor.user_id or debt['to_user_id'] != creditor_id:
                return False, "Debt does not match."
            if abs(float(debt['amount']) - amount) > 0.02:
                return False, "Amount does not match debt."
            did = int(direct_debt_id)
        elif settlement_id is not None:
            st = SettlementRepo.get_by_id(int(settlement_id))
            creditor = UserRepo.get_by_id(creditor_id)
            if not st or st.is_paid or not creditor:
                return False, "Invalid settlement."
            if st.debtor_name != debtor.username or st.creditor_name != creditor.username:
                return False, "Settlement does not match."
            if abs(float(st.amount) - amount) > 0.02:
                return False, "Amount does not match settlement."
            sid = int(settlement_id)
        else:
            return False, "directDebtId, settlementId, or netPayment required."

        rid = PaymentReminderRepo.upsert_pending(creditor_id, debtor.user_id, amount, did, sid)
        if rid:
            return True, f"Payment request sent to {debtor.username}."
        return False, "Could not send reminder."

    @staticmethod
    def get_due_alerts_for_debtor(debtor_id: int):
        rows = PaymentReminderRepo.get_pending_for_debtor(debtor_id)
        alerts = []
        for r in rows:
            creditor = UserRepo.get_by_id(r['creditor_id'])
            pay_num = creditor.pay_number if creditor else ''
            is_net = not r.get('direct_debt_id') and not r.get('settlement_id')
            alerts.append({
                'id': r['id'],
                'creditorUsername': r['creditor_username'],
                'amount': float(r['amount']),
                'directDebtId': r.get('direct_debt_id'),
                'settlementId': r.get('settlement_id'),
                'netPayment': is_net,
                'creditorPayNumber': pay_num,
                'message': f"{r['creditor_username']} requested their Rs. {float(r['amount'])} — double-click to pay",
            })
        return alerts

    @staticmethod
    def dismiss_after_payment(debtor_id: int, creditor_id: int, direct_debt_id=None, settlement_id=None):
        PaymentReminderRepo.dismiss_for_payment(debtor_id, creditor_id, direct_debt_id, settlement_id)
