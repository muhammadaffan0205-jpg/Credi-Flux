# backend/utils/min_cash_flow.py
from typing import Dict, List, Tuple

def run_min_cash_flow(net_balance: Dict[str, float]) -> List[Tuple[str, str, float]]:
    """
    Greedy minimum-cash-flow on net balances.
    Positive net = creditor; negative net = debtor.
    Returns list of (debtor, creditor, amount) payments.
    """
    creditors = [[name, round(net, 2)] for name, net in net_balance.items() if net > 0.009]
    debtors = [[name, round(-net, 2)] for name, net in net_balance.items() if net < -0.009]
    creditors.sort(key=lambda x: -x[1])
    debtors.sort(key=lambda x: -x[1])

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
