# backend/utils/balance_utils.py
from typing import List, Set, Tuple
from managers.expense_manager import ExpenseManager
from managers.group_manager import GroupManager
from repositories.debt_repo import DebtRepo
from repositories.user_repo import UserRepo
from repositories.group_repo import GroupRepo
from core.models import User
from utils.min_cash_flow import run_min_cash_flow


def _connected_user_ids(user_id: int) -> Set[int]:
    """All user IDs linked via shared groups or any direct-debt path."""
    ids: Set[int] = {user_id}
    for group in GroupRepo.get_user_groups(user_id):
        for member_id in GroupRepo.get_member_user_ids(group.group_id):
            ids.add(member_id)

    changed = True
    while changed:
        changed = False
        if not ids:
            break
        for debt in DebtRepo.list_accepted_involving_user_ids(list(ids)):
            for uid in (debt['from_user_id'], debt['to_user_id']):
                if uid not in ids:
                    ids.add(uid)
                    changed = True
    return ids


def get_global_balance_summary(user: User) -> List[Tuple[str, str, float]]:
    """
    Optimized settlements across all groups the user is in plus every direct debt
    in the same connected network (e.g. P1→P2 and P2→P3 are optimized together).
  """
    expense_manager = ExpenseManager()
    group_manager = GroupManager()
    net_balance = {}

    for group in group_manager.get_user_groups(user.user_id):
        for debtor, creditor, amount in expense_manager.get_balance_summary(group.group_id):
            net_balance[debtor] = net_balance.get(debtor, 0.0) - amount
            net_balance[creditor] = net_balance.get(creditor, 0.0) + amount

    connected_ids = _connected_user_ids(user.user_id)
    for debt in DebtRepo.list_accepted_involving_user_ids(list(connected_ids)):
        from_user = UserRepo.get_by_id(debt['from_user_id'])
        to_user = UserRepo.get_by_id(debt['to_user_id'])
        if not from_user or not to_user:
            continue
        amount = float(debt['amount'])
        net_balance[from_user.username] = net_balance.get(from_user.username, 0.0) - amount
        net_balance[to_user.username] = net_balance.get(to_user.username, 0.0) + amount

    return run_min_cash_flow(net_balance)


def get_optimized_amount_owed(user: User, creditor_username: str) -> float:
    for debtor, creditor, amount in get_global_balance_summary(user):
        if debtor == user.username and creditor == creditor_username:
            return amount
    return 0.0


def get_optimized_amount_to_collect(user: User, debtor_username: str) -> float:
    for debtor, creditor, amount in get_global_balance_summary(user):
        if creditor == user.username and debtor == debtor_username:
            return amount
    return 0.0


def get_group_balance_summary(group_id: int) -> List[Tuple[str, str, float]]:
    """
    Optimized settlements for one group, including direct debts between members
    (same min-cash-flow as dashboard, scoped to group display names).
    """
    from repositories.expense_repo import ExpenseRepo
    from repositories.settlement_repo import SettlementRepo

    net_balance = dict(ExpenseRepo.get_net_balance(group_id))
    for s in SettlementRepo.get_for_group(group_id):
        if s.is_paid:
            net_balance[s.debtor_name] = net_balance.get(s.debtor_name, 0.0) + float(s.amount)
            net_balance[s.creditor_name] = net_balance.get(s.creditor_name, 0.0) - float(s.amount)

    user_id_to_label = {}
    for p in GroupRepo.get_people(group_id):
        if p.user_id:
            user_id_to_label[p.user_id] = p.display_name

    member_ids = list(user_id_to_label.keys())
    if member_ids:
        for debt in DebtRepo.list_accepted_involving_user_ids(member_ids):
            from_id = debt['from_user_id']
            to_id = debt['to_user_id']
            if from_id not in user_id_to_label or to_id not in user_id_to_label:
                continue
            amount = float(debt['amount'])
            from_label = user_id_to_label[from_id]
            to_label = user_id_to_label[to_id]
            net_balance[from_label] = net_balance.get(from_label, 0.0) - amount
            net_balance[to_label] = net_balance.get(to_label, 0.0) + amount

    return run_min_cash_flow(net_balance)
