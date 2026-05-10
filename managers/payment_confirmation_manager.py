# crediflux/managers/payment_confirmation_manager.py
from repositories.payment_confirmation_repo import PaymentConfirmationRepo
from managers.settlement_manager import SettlementManager
from managers.debt_manager import DebtManager
from repositories.user_repo import UserRepo
from typing import List, Dict, Optional

class PaymentConfirmationManager:
    @staticmethod
    def request_payment(debtor_id: int, creditor_id: int, amount: float,
                        settlement_id: Optional[int] = None,
                        direct_debt_id: Optional[int] = None) -> Optional[int]:
        return PaymentConfirmationRepo.create(debtor_id, creditor_id, amount, settlement_id, direct_debt_id)

    @staticmethod
    def get_pending_for_user(user_id: int) -> List[Dict]:
        return PaymentConfirmationRepo.get_pending_for_creditor(user_id)

    @staticmethod
    def confirm_payment(confirmation_id: int, creditor_id: int) -> bool:
        req = PaymentConfirmationRepo.get_by_id(confirmation_id)
        if not req:
            print("[ERROR] No request found for id", confirmation_id)
            return False
        if req['creditor_id'] != creditor_id:
            print(f"[ERROR] Creditor mismatch: request creditor {req['creditor_id']} vs {creditor_id}")
            return False
        if req['status'] != 'pending':
            print(f"[ERROR] Request status is {req['status']}, not pending")
            return False

        success = False
        print(f"[DEBUG] Confirming payment: settlement_id={req['settlement_id']}, direct_debt_id={req['direct_debt_id']}")
        if req['settlement_id']:
            # Group settlement
            success = SettlementManager.mark_paid_by_id(req['settlement_id'])
            print(f"[DEBUG] mark_paid_by_id result: {success}")
        elif req['direct_debt_id']:
            # Direct debt
            creditor = UserRepo.get_by_id(req['creditor_id'])
            if not creditor:
                print("[ERROR] Creditor not found for direct debt")
                return False
            success = DebtManager.mark_direct_paid(
                debt_id=req['direct_debt_id'],
                payer_user_id=req['debtor_id'],
                creditor_name=creditor.username,
                amount=float(req['amount']),
                group_id=None
            )
            print(f"[DEBUG] mark_direct_paid result: {success}")
        else:
            print("[ERROR] No settlement_id nor direct_debt_id in request")
            return False

        if success:
            return PaymentConfirmationRepo.confirm(confirmation_id)
        return False