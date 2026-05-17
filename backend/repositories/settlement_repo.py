# backend/repositories/settlement_repo.py
from core.db_connection import get_db
from core.models import Settlement
from typing import List, Optional
from datetime import datetime

class SettlementRepo:
    @staticmethod
    def get_by_id(settlement_id: int) -> Optional[Settlement]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM settlements WHERE settlement_id=%s", (settlement_id,))
            row = cur.fetchone()
            return SettlementRepo._row(row) if row else None
        finally:
            cur.close()

    @staticmethod
    def save_settlements(group_id: int, settlements: List[tuple]) -> bool:
        conn, cur = get_db()
        try:
            cur.execute("DELETE FROM settlements WHERE group_id=%s AND is_paid=0", (group_id,))
            for debtor, creditor, amount in settlements:
                cur.execute(
                    "INSERT INTO settlements (group_id, debtor_name, creditor_name, amount) VALUES (%s,%s,%s,%s)",
                    (group_id, debtor, creditor, amount)
                )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def reduce_or_mark_paid(settlement_id: int, payment: float) -> bool:
        st = SettlementRepo.get_by_id(settlement_id)
        if not st or st.is_paid:
            return False
        amount = float(st.amount)
        if payment >= amount - 0.009:
            return SettlementRepo.mark_paid(settlement_id)
        conn, cur = get_db()
        try:
            cur.execute(
                "UPDATE settlements SET amount = %s WHERE settlement_id = %s AND is_paid = 0",
                (round(amount - payment, 2), settlement_id),
            )
            conn.commit()
            return cur.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def mark_paid(settlement_id: int) -> bool:
        conn, cur = get_db()
        try:
            cur.execute("UPDATE settlements SET is_paid=1, paid_at=%s WHERE settlement_id=%s", (datetime.now(), settlement_id))
            conn.commit()
            return cur.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def get_for_group(group_id: int) -> List[Settlement]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM settlements WHERE group_id=%s ORDER BY is_paid, created_at DESC", (group_id,))
            return [SettlementRepo._row(r) for r in cur.fetchall()]
        finally:
            cur.close()

    @staticmethod
    def get_for_user(username: str) -> List[Settlement]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM settlements WHERE debtor_name=%s AND is_paid=0 ORDER BY created_at DESC", (username,))
            return [SettlementRepo._row(r) for r in cur.fetchall()]
        finally:
            cur.close()

    @staticmethod
    def get_owed_to_user(username: str) -> List[Settlement]:
        """Unpaid settlements where this user is the creditor."""
        _, cur = get_db()
        try:
            cur.execute(
                "SELECT * FROM settlements WHERE creditor_name=%s AND is_paid=0 ORDER BY created_at DESC",
                (username,),
            )
            return [SettlementRepo._row(r) for r in cur.fetchall()]
        finally:
            cur.close()

    @staticmethod
    def _row(r: dict) -> Settlement:
        return Settlement(
            settlement_id = r["settlement_id"],
            group_id      = r["group_id"],
            debtor_name   = r["debtor_name"],
            creditor_name = r["creditor_name"],
            amount        = float(r["amount"]),
            is_paid       = bool(r["is_paid"]),
            paid_at       = r.get("paid_at"),
            created_at    = r.get("created_at"),
        )