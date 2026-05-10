# crediflux/repositories/payment_confirmation_repo.py
from core.db_connection import get_db
from datetime import datetime
from typing import List, Dict, Optional

class PaymentConfirmationRepo:
    @staticmethod
    def create(debtor_id: int, creditor_id: int, amount: float, settlement_id: Optional[int] = None, direct_debt_id: Optional[int] = None) -> Optional[int]:
        conn, cur = get_db()
        try:
            cur.execute(
                """INSERT INTO payment_confirmations
                   (debtor_id, creditor_id, amount, settlement_id, direct_debt_id, status)
                   VALUES (%s, %s, %s, %s, %s, 'pending')""",
                (debtor_id, creditor_id, amount, settlement_id, direct_debt_id)
            )
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            return None
        finally:
            cur.close()

    @staticmethod
    def get_pending_for_creditor(creditor_id: int) -> List[Dict]:
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT pc.id, pc.debtor_id, pc.creditor_id, pc.amount,
                          pc.settlement_id, pc.direct_debt_id, pc.status, pc.created_at,
                          u.username as debtor_name
                   FROM payment_confirmations pc
                   JOIN users u ON pc.debtor_id = u.id
                   WHERE pc.creditor_id = %s AND pc.status = 'pending'
                   ORDER BY pc.created_at DESC""",
                (creditor_id,)
            )
            return cur.fetchall()
        finally:
            cur.close()

    @staticmethod
    def confirm(confirmation_id: int) -> bool:
        conn, cur = get_db()
        try:
            cur.execute(
                "UPDATE payment_confirmations SET status='confirmed' WHERE id=%s",
                (confirmation_id,)
            )
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            print(f"[ERROR] confirm DB error: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def get_by_id(confirmation_id: int) -> Optional[Dict]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM payment_confirmations WHERE id=%s", (confirmation_id,))
            return cur.fetchone()
        finally:
            cur.close()