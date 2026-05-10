# crediflux/utils/balance_utils.py
from typing import List, Tuple
from managers.expense_manager import ExpenseManager
from managers.debt_manager import DebtManager
from managers.group_manager import GroupManager
from repositories.user_repo import UserRepo   # <-- THIS WAS MISSING
from core.models import User


def get_global_balance_summary(user: User) -> List[Tuple[str, str, float]]:
    """
    Returns optimized settlements based on all groups the user is in
    plus all active direct debts (accepted requests).
    """
    group_manager = GroupManager()
    expense_manager = ExpenseManager()
    debt_manager = DebtManager()

    # 1. Group debts
    groups = group_manager.get_user_groups(user.user_id)
    net_balance = {}   # username -> net (positive = creditor, negative = debtor)

    for group in groups:
        settlements = expense_manager.get_balance_summary(group.group_id)
        for debtor, creditor, amount in settlements:
            net_balance[debtor] = net_balance.get(debtor, 0.0) - amount
            net_balance[creditor] = net_balance.get(creditor, 0.0) + amount

    # 2. Direct debts (accepted)
    direct_debts = debt_manager.get_active_debts(user.user_id)
    for debt in direct_debts:
        from_user = UserRepo.get_by_id(debt['from_user_id'])
        to_user = UserRepo.get_by_id(debt['to_user_id'])
        if not from_user or not to_user:
            continue
        from_name = from_user.username
        to_name = to_user.username
        amount = float(debt['amount'])
        net_balance[from_name] = net_balance.get(from_name, 0.0) - amount
        net_balance[to_name] = net_balance.get(to_name, 0.0) + amount

    # 3. Build creditors and debtors lists
    creditors = [[name, net] for name, net in net_balance.items() if net > 0.009]
    debtors = [[name, -net] for name, net in net_balance.items() if net < -0.009]

    # 4. Greedy min‑cash‑flow algorithm
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
        if debtors[i][1] <= 0.009: i += 1
        if creditors[j][1] <= 0.009: j += 1
    return settlements