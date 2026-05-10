# crediflux/repositories/settlement_repo.py
from core.db_connection import get_db
from core.models import Settlement
from typing import List
from datetime import datetime

class SettlementRepo:
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
    def mark_paid(settlement_id: int) -> bool:
        conn, cur = get_db()
        try:
            cur.execute(
                "UPDATE settlements SET is_paid=1 WHERE settlement_id=%s",
                (settlement_id,)
            )
            conn.commit()
            rows_affected = cur.rowcount
            print(f"[DEBUG] mark_paid: settlement_id={settlement_id}, rows_affected={rows_affected}")
            return rows_affected > 0
        except Exception as e:
            print(f"[ERROR] mark_paid failed: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def get_for_group(group_id: int) -> List[Settlement]:
        _, cur = get_db()
        try:
            cur.execute(
                "SELECT * FROM settlements WHERE group_id=%s ORDER BY is_paid, created_at DESC",
                (group_id,)
            )
            return [SettlementRepo._row(r) for r in cur.fetchall()]
        finally:
            cur.close()

    @staticmethod
    def get_for_user(username: str) -> List[Settlement]:
        _, cur = get_db()
        try:
            cur.execute(
                "SELECT * FROM settlements WHERE debtor_name=%s AND is_paid=0 ORDER BY created_at DESC",
                (username,)
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