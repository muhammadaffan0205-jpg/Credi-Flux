# crediflux/repositories/debt_repo.py
from core.db_connection import get_db
from typing import List, Dict, Optional
from datetime import datetime

class DebtRepo:
    @staticmethod
    def create_request(from_user_id: int, to_user_id: int, amount: float) -> Optional[int]:
        conn, cur = get_db()
        try:
            cur.execute(
                "INSERT INTO user_debts (from_user_id, to_user_id, amount, status) VALUES (%s,%s,%s,'pending')",
                (from_user_id, to_user_id, amount)
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
                          u.username as from_username, u.phone as from_phone
                   FROM user_debts d
                   JOIN users u ON d.from_user_id = u.id
                   WHERE d.to_user_id = %s AND d.status = 'pending'""",
                (user_id,)
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
        """Delete the direct debt row instead of updating status."""
        conn, cur = get_db()
        try:
            cur.execute("DELETE FROM user_debts WHERE id=%s AND status='accepted'", (debt_id,))
            conn.commit()
            rows = cur.rowcount
            print(f"[DEBUG] DebtRepo.mark_paid (DELETE): debt_id={debt_id}, rows deleted={rows}")
            return rows > 0
        except Exception as e:
            print(f"[ERROR] mark_paid DB error: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()