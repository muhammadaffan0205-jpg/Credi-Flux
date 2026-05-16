# backend/repositories/user_repo.py
import re
from core.db_connection import get_db
from core.models import User
from typing import List, Optional

class UserRepo:
    @staticmethod
    def _phone_lookup_candidates(raw: str) -> List[str]:
        """Match stored phones even when UI typing differs (spaces, leading 0, 92 prefix)."""
        if not raw:
            return []
        digits = re.sub(r'\D', '', raw)
        if not digits:
            return []
        ordered: List[str] = []
        seen = set()

        def add(p: str):
            if p and p not in seen:
                seen.add(p)
                ordered.append(p)

        add(digits)
        # e.g. 03001234567 (11) stored as 3001234567 (10)
        if len(digits) == 11 and digits.startswith('0'):
            add(digits[1:])
        elif len(digits) == 10:
            add('0' + digits)
        # Pakistan country code
        if digits.startswith('92') and len(digits) >= 12:
            core = digits[2:]
            add(core)
            if len(core) == 11 and core.startswith('0'):
                add(core[1:])
            elif len(core) == 10:
                add('0' + core)
        return ordered

    @staticmethod
    def save(full_name: str, username: str, phone: str, password_hash: str, salt: str) -> Optional[int]:
        conn, cur = get_db()
        try:
            cur.execute(
                "INSERT INTO users (full_name, username, phone, password, salt) VALUES (%s,%s,%s,%s,%s)",
                (full_name, username, phone, password_hash, salt)
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
            for candidate in UserRepo._phone_lookup_candidates(phone):
                cur.execute("SELECT * FROM users WHERE phone = %s", (candidate,))
                row = cur.fetchone()
                if row:
                    return UserRepo._row_to_model(row)
            return None
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
            salt           = row["salt"],
            easypaisa_num  = row.get("easypaisa_num"),
            wallet_balance = float(row.get("wallet_balance", 0)),
            created_at     = row.get("created_at"),
        )