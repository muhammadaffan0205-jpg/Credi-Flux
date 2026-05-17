# backend/managers/payment_confirmation_manager.py
from repositories.payment_confirmation_repo import PaymentConfirmationRepo
from managers.settlement_manager import SettlementManager
from managers.debt_manager import DebtManager
from repositories.user_repo import UserRepo

class PaymentConfirmationManager:
    @staticmethod
    def request_payment(debtor_id, creditor_id, amount, settlement_id=None, direct_debt_id=None):
        return PaymentConfirmationRepo.create(debtor_id, creditor_id, amount, settlement_id, direct_debt_id)

    @staticmethod
    def get_pending_for_user(user_id):
        return PaymentConfirmationRepo.get_pending_for_creditor(user_id)

    @staticmethod
    def confirm_payment(confirmation_id, creditor_id):
        req = PaymentConfirmationRepo.get_by_id(confirmation_id)
        if not req or req['creditor_id'] != creditor_id or req['status'] != 'pending':
            return False
        success = False
        if req['settlement_id']:
            success = SettlementManager.mark_paid_by_id(req['settlement_id'])
        elif req['direct_debt_id']:
            creditor = UserRepo.get_by_id(req['creditor_id'])
            if creditor:
                success = DebtManager.mark_direct_paid(req['direct_debt_id'], req['debtor_id'],
                                                       creditor.username, float(req['amount']), None)
        elif req['direct_debt_id'] is None and req['settlement_id'] is None:
            success = DebtManager.settle_global_optimized_payment(
                req['debtor_id'], req['creditor_id'], float(req['amount'])
            )
        if success:
            return PaymentConfirmationRepo.confirm(confirmation_id)
        return False