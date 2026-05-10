# crediflux/managers/payment_manager.py
from utils.easypaisa_helper import EasypaisaHelper
from managers.settlement_manager import SettlementManager
from core.models import Settlement

class PaymentManager:
    @staticmethod
    def initiate(settlement: Settlement, receiver_phone: str) -> dict:
        EasypaisaHelper.copy_to_clipboard(receiver_phone)
        EasypaisaHelper.open_easypaisa()
        return {
            "receiver_phone": receiver_phone,
            "amount":         settlement.amount,
            "creditor_name":  settlement.creditor_name,
            "settlement":     settlement,
        }

    @staticmethod
    def confirm(settlement: Settlement, user_id: int) -> bool:
        return SettlementManager.confirm_paid(settlement, user_id)