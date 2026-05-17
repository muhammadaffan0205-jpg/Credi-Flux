# backend/repositories/debt_repo.py
from core.db_connection import get_db
from datetime import datetime
from typing import List, Dict, Optional

class DebtRepo:
    @staticmethod
    def get_by_id(debt_id: int) -> Optional[Dict]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM user_debts WHERE id=%s", (debt_id,))
            return cur.fetchone()
        finally:
            cur.close()

    @staticmethod
    def list_accepted_owed_to(creditor_user_id: int) -> List[Dict]:
        """Accepted direct debts where this user is the creditor (to_user)."""
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT id, from_user_id, to_user_id, amount, status
                   FROM user_debts
                   WHERE to_user_id = %s AND status = 'accepted'""",
                (creditor_user_id,),
            )
            return cur.fetchall()
        finally:
            cur.close()

    @staticmethod
    def list_accepted_owed_by(debtor_user_id: int) -> List[Dict]:
        """Accepted direct debts where this user is the debtor (from_user)."""
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT id, from_user_id, to_user_id, amount, status
                   FROM user_debts
                   WHERE from_user_id = %s AND status = 'accepted'""",
                (debtor_user_id,),
            )
            return cur.fetchall()
        finally:
            cur.close()

    @staticmethod
    def create_request(
        debtor_id: int,
        creditor_id: int,
        pending_for_user_id: int,
        requested_by_user_id: int,
        amount: float,
    ) -> Optional[int]:
        conn, cur = get_db()
        try:
            cur.execute(
                """INSERT INTO user_debts
                   (from_user_id, to_user_id, pending_for_user_id, requested_by_user_id, amount, status)
                   VALUES (%s, %s, %s, %s, %s, 'pending')""",
                (debtor_id, creditor_id, pending_for_user_id, requested_by_user_id, amount),
            )
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            return None
        finally:
            cur.close()

    @staticmethod
    def get_pending_for_user(user_id: int) -> List[Dict]:
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT d.id, d.from_user_id, d.to_user_id, d.amount, d.status, d.created_at,
                          d.pending_for_user_id, d.requested_by_user_id,
                          debtor.username AS debtor_username,
                          creditor.username AS creditor_username,
                          requester.username AS requested_by_username
                   FROM user_debts d
                   JOIN users debtor ON d.from_user_id = debtor.id
                   JOIN users creditor ON d.to_user_id = creditor.id
                   LEFT JOIN users requester ON d.requested_by_user_id = requester.id
                   WHERE d.status = 'pending'
                     AND (d.pending_for_user_id = %s
                          OR (d.pending_for_user_id IS NULL AND d.to_user_id = %s))
                   ORDER BY d.created_at DESC""",
                (user_id, user_id),
            )
            return cur.fetchall()
        finally:
            cur.close()

    @staticmethod
    def accept_request(request_id: int) -> bool:
        conn, cur = get_db()
        try:
            cur.execute(
                "UPDATE user_debts SET status='accepted', accepted_at=%s WHERE id=%s",
                (datetime.now(), request_id)
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def reject_request(request_id: int) -> bool:
        conn, cur = get_db()
        try:
            cur.execute("UPDATE user_debts SET status='rejected' WHERE id=%s", (request_id,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def list_accepted_involving_user_ids(user_ids: List[int]) -> List[Dict]:
        if not user_ids:
            return []
        _, cur = get_db()
        try:
            placeholders = ','.join(['%s'] * len(user_ids))
            cur.execute(
                f"""SELECT id, from_user_id, to_user_id, amount, status
                    FROM user_debts
                    WHERE status = 'accepted'
                      AND (from_user_id IN ({placeholders}) OR to_user_id IN ({placeholders}))""",
                tuple(user_ids) + tuple(user_ids),
            )
            return cur.fetchall()
        finally:
            cur.close()

    @staticmethod
    def reduce_or_clear(debt_id: int, payment: float) -> bool:
        debt = DebtRepo.get_by_id(debt_id)
        if not debt or debt.get('status') != 'accepted':
            return False
        amount = float(debt['amount'])
        if payment >= amount - 0.009:
            return DebtRepo.mark_paid(debt_id)
        conn, cur = get_db()
        try:
            cur.execute(
                "UPDATE user_debts SET amount = %s WHERE id = %s AND status = 'accepted'",
                (round(amount - payment, 2), debt_id),
            )
            conn.commit()
            return cur.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def list_accepted_between(user_id: int, other_user_id: int) -> List[Dict]:
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT id, from_user_id, to_user_id, amount, status
                   FROM user_debts
                   WHERE status = 'accepted'
                     AND ((from_user_id = %s AND to_user_id = %s)
                          OR (from_user_id = %s AND to_user_id = %s))""",
                (user_id, other_user_id, other_user_id, user_id),
            )
            return cur.fetchall()
        finally:
            cur.close()

    @staticmethod
    def get_active_debts(user_id: int) -> List[Dict]:
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT id, from_user_id, to_user_id, amount, status, created_at, accepted_at
                   FROM user_debts
                   WHERE (from_user_id = %s OR to_user_id = %s) AND status = 'accepted'""",
                (user_id, user_id)
            )
            return cur.fetchall()
        finally:
            cur.close()

    @staticmethod
    def mark_paid(debt_id: int) -> bool:
        conn, cur = get_db()
        try:
            cur.execute("DELETE FROM user_debts WHERE id=%s AND status='accepted'", (debt_id,))
            conn.commit()
            return cur.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()