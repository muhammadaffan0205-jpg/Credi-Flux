# crediflux/repositories/user_repo.py
from core.db_connection import get_db
from core.models import User
from typing import Optional

class UserRepo:
    @staticmethod
    def save(full_name: str, username: str, phone: str, password: str) -> Optional[int]:
        conn, cur = get_db()
        try:
            cur.execute(
                "INSERT INTO users (full_name, username, phone, password) VALUES (%s,%s,%s,%s)",
                (full_name, username, phone, password)
            )
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            return None
        finally:
            cur.close()

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            return UserRepo._row_to_model(row) if row else None
        finally:
            cur.close()

    @staticmethod
    def get_by_phone(phone: str) -> Optional[User]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM users WHERE phone = %s", (phone,))
            row = cur.fetchone()
            return UserRepo._row_to_model(row) if row else None
        finally:
            cur.close()

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        _, cur = get_db()
        try:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return UserRepo._row_to_model(row) if row else None
        finally:
            cur.close()

    @staticmethod
    def update_easypaisa_num(user_id: int, ep_number: str) -> bool:
        conn, cur = get_db()
        try:
            cur.execute(
                "UPDATE users SET easypaisa_num = %s WHERE id = %s",
                (ep_number, user_id)
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def _row_to_model(row: dict) -> User:
        return User(
            user_id        = row["id"],
            full_name      = row["full_name"],
            username       = row["username"],
            phone          = row["phone"],
            password       = row["password"],
            easypaisa_num  = row.get("easypaisa_num"),
            wallet_balance = float(row.get("wallet_balance", 0)),
            created_at     = row.get("created_at"),
        )