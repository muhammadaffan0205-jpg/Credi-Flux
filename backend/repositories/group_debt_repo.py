# backend/repositories/group_debt_repo.py
from core.db_connection import get_db
from datetime import datetime
from typing import List, Dict, Optional

class GroupDebtRepo:
    @staticmethod
    def create_request(
        group_id: int,
        debtor_user_id: int,
        creditor_user_id: int,
        pending_for_user_id: int,
        requested_by_user_id: int,
        amount: float,
    ) -> Optional[int]:
        conn, cur = get_db()
        try:
            cur.execute(
                """INSERT INTO group_debt_requests
                   (group_id, debtor_user_id, creditor_user_id, pending_for_user_id,
                    requested_by_user_id, amount, status)
                   VALUES (%s, %s, %s, %s, %s, %s, 'pending')""",
                (group_id, debtor_user_id, creditor_user_id, pending_for_user_id,
                 requested_by_user_id, amount),
            )
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            return None
        finally:
            cur.close()

    @staticmethod
    def get_by_id(request_id: int) -> Optional[Dict]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM group_debt_requests WHERE id=%s", (request_id,))
            return cur.fetchone()
        finally:
            cur.close()

    @staticmethod
    def get_pending_for_user(user_id: int) -> List[Dict]:
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT gdr.*, g.group_name,
                          debtor.username AS debtor_username,
                          creditor.username AS creditor_username,
                          requester.username AS requested_by_username
                   FROM group_debt_requests gdr
                   JOIN groupss g ON gdr.group_id = g.group_id
                   JOIN users debtor ON gdr.debtor_user_id = debtor.id
                   JOIN users creditor ON gdr.creditor_user_id = creditor.id
                   JOIN users requester ON gdr.requested_by_user_id = requester.id
                   WHERE gdr.status = 'pending' AND gdr.pending_for_user_id = %s
                   ORDER BY gdr.created_at DESC""",
                (user_id,),
            )
            return cur.fetchall()
        finally:
            cur.close()

    @staticmethod
    def accept_request(request_id: int) -> bool:
        conn, cur = get_db()
        try:
            cur.execute(
                "UPDATE group_debt_requests SET status='accepted', accepted_at=%s WHERE id=%s",
                (datetime.now(), request_id),
            )
            conn.commit()
            return cur.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()
