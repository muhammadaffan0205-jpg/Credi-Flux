# backend/repositories/transaction_repo.py
from core.db_connection import get_db
from core.models import Transaction
from typing import List, Optional

class TransactionRepo:
    @staticmethod
    def save(user_id: int, description: str, amount: float, paid_to: str, group_id: Optional[int] = None) -> bool:
        conn, cur = get_db()
        try:
            cur.execute(
                "INSERT INTO transactions (user_id, group_id, description, amount, paid_to) VALUES (%s,%s,%s,%s,%s)",
                (user_id, group_id, description, amount, paid_to)
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def get_for_user(user_id: int, limit: int = 100) -> List[Transaction]:
        _, cur = get_db()
        try:
            cur.execute(
                "SELECT * FROM transactions WHERE user_id=%s ORDER BY txn_date DESC LIMIT %s",
                (user_id, limit)
            )
            return [Transaction(**r) for r in cur.fetchall()]
        finally:
            cur.close()

    @staticmethod
    def get_totals(user_id: int):
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT
                     COALESCE(SUM(CASE WHEN s.debtor_name=(SELECT username FROM users WHERE id=%s) THEN s.amount ELSE 0 END),0) AS owed,
                     COALESCE(SUM(CASE WHEN s.creditor_name=(SELECT username FROM users WHERE id=%s) THEN s.amount ELSE 0 END),0) AS collect
                   FROM settlements s WHERE s.is_paid=0""",
                (user_id, user_id)
            )
            row = cur.fetchone()
            return float(row["owed"]), float(row["collect"])
        finally:
            cur.close()