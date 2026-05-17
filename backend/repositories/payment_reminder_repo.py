# backend/repositories/payment_reminder_repo.py
from core.db_connection import get_db
from datetime import datetime
from typing import List, Dict, Optional

class PaymentReminderRepo:
    @staticmethod
    def upsert_pending(
        creditor_id: int,
        debtor_id: int,
        amount: float,
        direct_debt_id=None,
        settlement_id=None,
    ) -> Optional[int]:
        conn, cur = get_db()
        try:
            cur.execute(
                """SELECT id FROM payment_reminders
                   WHERE creditor_id=%s AND debtor_id=%s AND status='pending'
                     AND ((direct_debt_id IS NULL AND %s IS NULL) OR direct_debt_id=%s)
                     AND ((settlement_id IS NULL AND %s IS NULL) OR settlement_id=%s)
                   LIMIT 1""",
                (creditor_id, debtor_id, direct_debt_id, direct_debt_id, settlement_id, settlement_id),
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    "UPDATE payment_reminders SET amount=%s, created_at=%s WHERE id=%s",
                    (amount, datetime.now(), row['id']),
                )
                conn.commit()
                return row['id']
            cur.execute(
                """INSERT INTO payment_reminders
                   (creditor_id, debtor_id, amount, direct_debt_id, settlement_id, status)
                   VALUES (%s, %s, %s, %s, %s, 'pending')""",
                (creditor_id, debtor_id, amount, direct_debt_id, settlement_id),
            )
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            return None
        finally:
            cur.close()

    @staticmethod
    def get_pending_for_debtor(debtor_id: int) -> List[Dict]:
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT pr.id, pr.creditor_id, pr.debtor_id, pr.amount,
                          pr.direct_debt_id, pr.settlement_id, pr.status, pr.created_at,
                          c.username AS creditor_username, c.phone, c.easypaisa_num
                   FROM payment_reminders pr
                   JOIN users c ON pr.creditor_id = c.id
                   WHERE pr.debtor_id = %s AND pr.status = 'pending'
                   ORDER BY pr.created_at DESC""",
                (debtor_id,),
            )
            return cur.fetchall()
        finally:
            cur.close()

    @staticmethod
    def dismiss_for_payment(debtor_id: int, creditor_id: int, direct_debt_id=None, settlement_id=None) -> bool:
        conn, cur = get_db()
        try:
            cur.execute(
                """UPDATE payment_reminders SET status='dismissed'
                   WHERE debtor_id=%s AND creditor_id=%s AND status='pending'
                     AND ((direct_debt_id IS NULL AND %s IS NULL) OR direct_debt_id=%s)
                     AND ((settlement_id IS NULL AND %s IS NULL) OR settlement_id=%s)""",
                (debtor_id, creditor_id, direct_debt_id, direct_debt_id, settlement_id, settlement_id),
            )
            conn.commit()
            return cur.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def get_by_id(reminder_id: int) -> Optional[Dict]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM payment_reminders WHERE id=%s", (reminder_id,))
            return cur.fetchone()
        finally:
            cur.close()
