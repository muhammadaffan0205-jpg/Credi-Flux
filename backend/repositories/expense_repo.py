# backend/repositories/expense_repo.py
from core.db_connection import get_db
from core.models import Expense
from typing import List, Tuple, Optional

class ExpenseRepo:
    @staticmethod
    def add_expense_with_payers(group_id: int, description: str, total_amount: float,
                                payer_names: List[str], people: List) -> Tuple[bool, str]:
        conn, cur = get_db()
        try:
            name_map = {p.display_name.strip().lower(): p for p in people}
            norm_payers = list(dict.fromkeys(n.strip().lower() for n in payer_names if n.strip()))
            if not norm_payers or len(norm_payers) > 2:
                return False, "Select one or two payers."
            payer_people = [name_map[name] for name in norm_payers if name in name_map]
            if len(payer_people) != len(norm_payers):
                return False, "One or more payers not in group."
            non_payers = [p for p in people if p.person_id not in {x.person_id for x in payer_people}]
            if not non_payers:
                return False, "Need at least one non-payer."
            paid_each = round(total_amount / len(payer_people), 2)
            owes_each = round(total_amount / len(non_payers), 2)
            cur.execute("INSERT INTO manual_expenses (group_id, description, total_amount) VALUES (%s,%s,%s)",
                        (group_id, description, total_amount))
            expense_id = cur.lastrowid
            payer_ids = {p.person_id for p in payer_people}
            for person in people:
                is_payer = person.person_id in payer_ids
                cur.execute(
                    "INSERT INTO manual_expense_shares (expense_id, person_id, paid_amount, owed_amount) VALUES (%s,%s,%s,%s)",
                    (expense_id, person.person_id, paid_each if is_payer else 0, 0 if is_payer else owes_each)
                )
            conn.commit()
            return True, "Expense added and split successfully."
        except Exception as e:
            conn.rollback()
            return False, f"DB error: {e}"
        finally:
            cur.close()

    @staticmethod
    def add_bilateral_debt(
        group_id: int,
        description: str,
        debtor_name: str,
        creditor_name: str,
        amount: float,
        people: List,
    ) -> Tuple[bool, str]:
        """Record debt between two members only; other members unaffected."""
        conn, cur = get_db()
        try:
            name_map = {p.display_name.strip().lower(): p for p in people}
            dk = debtor_name.strip().lower()
            ck = creditor_name.strip().lower()
            if dk not in name_map or ck not in name_map:
                return False, "Both members must be in the group."
            if dk == ck:
                return False, "Debtor and creditor must be different."
            debtor_p = name_map[dk]
            creditor_p = name_map[ck]
            cur.execute(
                "INSERT INTO manual_expenses (group_id, description, total_amount) VALUES (%s,%s,%s)",
                (group_id, description, amount),
            )
            expense_id = cur.lastrowid
            for person in people:
                if person.person_id == debtor_p.person_id:
                    paid, owed = 0, amount
                elif person.person_id == creditor_p.person_id:
                    paid, owed = amount, 0
                else:
                    paid, owed = 0, 0
                cur.execute(
                    "INSERT INTO manual_expense_shares (expense_id, person_id, paid_amount, owed_amount) "
                    "VALUES (%s,%s,%s,%s)",
                    (expense_id, person.person_id, paid, owed),
                )
            conn.commit()
            return True, "Group debt recorded."
        except Exception as e:
            conn.rollback()
            return False, f"DB error: {e}"
        finally:
            cur.close()

    @staticmethod
    def get_net_balance(group_id: int) -> dict:
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT gp.display_name,
                          COALESCE(SUM(mes.paid_amount), 0) AS total_paid,
                          COALESCE(SUM(mes.owed_amount), 0) AS total_owed
                   FROM group_people gp
                   LEFT JOIN manual_expense_shares mes ON gp.person_id = mes.person_id
                   WHERE gp.group_id = %s
                   GROUP BY gp.person_id, gp.display_name""",
                (group_id,)
            )
            rows = cur.fetchall()
            net = {}
            for row in rows:
                net[row['display_name']] = float(row['total_paid']) - float(row['total_owed'])
            return net
        finally:
            cur.close()

    @staticmethod
    def get_balance_summary(group_id: int) -> List[Tuple[str, str, float]]:
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT gp.display_name,
                          COALESCE(SUM(mes.paid_amount), 0) AS total_paid,
                          COALESCE(SUM(mes.owed_amount), 0) AS total_owed
                   FROM group_people gp
                   LEFT JOIN manual_expense_shares mes ON gp.person_id = mes.person_id
                   WHERE gp.group_id = %s
                   GROUP BY gp.person_id, gp.display_name""",
                (group_id,)
            )
            rows = cur.fetchall()
        finally:
            cur.close()
        if not rows:
            return []
        creditors, debtors = [], []
        for row in rows:
            net = float(row["total_paid"]) - float(row["total_owed"])
            if net > 0.009:
                creditors.append([row["display_name"], net])
            elif net < -0.009:
                debtors.append([row["display_name"], -net])
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

    @staticmethod
    def get_group_expenses(group_id: int) -> List[Expense]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM manual_expenses WHERE group_id=%s ORDER BY created_at DESC", (group_id,))
            return [Expense(**r) for r in cur.fetchall()]
        finally:
            cur.close()