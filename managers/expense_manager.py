# crediflux/managers/expense_manager.py
from repositories.expense_repo import ExpenseRepo
from repositories.group_repo import GroupRepo
from repositories.settlement_repo import SettlementRepo
from typing import List, Tuple

class ExpenseManager:
    @staticmethod
    def add(group_id: int, description: str, amount_str: str,
            payer_names: List[str]) -> Tuple[bool, str]:
        if not description.strip():
            return False, "Enter a description."
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, "Amount must be greater than zero."
        except ValueError:
            return False, "Amount must be a number."
        people = GroupRepo.get_people(group_id)
        if len(people) < 2:
            return False, "Add at least 2 members first."
        ok, msg = ExpenseRepo.add_expense_with_payers(
            group_id, description.strip(), amount, payer_names, people
        )
        if ok:
            raw = ExpenseRepo.get_balance_summary(group_id)
            SettlementRepo.save_settlements(group_id, raw)
        return ok, msg

    @staticmethod
    def get_balance_summary(group_id: int) -> List[Tuple[str, str, float]]:
        """Returns optimized settlement list excluding amounts already paid."""
        from repositories.settlement_repo import SettlementRepo
        # Get raw net balances from expense shares
        net = ExpenseRepo.get_net_balance(group_id)
        # Subtract amounts already paid via settlements
        settlements = SettlementRepo.get_for_group(group_id)
        paid_settlements = [s for s in settlements if s.is_paid]
        for s in paid_settlements:
            net[s.debtor_name] = net.get(s.debtor_name, 0) + s.amount   # reduce debt
            net[s.creditor_name] = net.get(s.creditor_name, 0) - s.amount
        # Build creditors and debtors lists
        creditors = [[name, bal] for name, bal in net.items() if bal > 0.009]
        debtors = [[name, -bal] for name, bal in net.items() if bal < -0.009]
        # Greedy min‑cash‑flow algorithm
        settlements = []
        i = j = 0
        while i < len(debtors) and j < len(creditors):
            debtor, debt = debtors[i]
            creditor, credit = creditors[j]
            pay = round(min(debt, credit), 2)
            if pay > 0:
                settlements.append((debtor, creditor, pay))
            debtors[i][1] = round(debt - pay, 2)
            creditors[j][1] = round(credit - pay, 2)
            if debtors[i][1] <= 0.009:
                i += 1
            if creditors[j][1] <= 0.009:
                j += 1
        return settlements
