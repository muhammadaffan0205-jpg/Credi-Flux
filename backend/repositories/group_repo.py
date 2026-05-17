# backend/repositories/group_repo.py
from core.db_connection import get_db
from core.models import Group, Person
from typing import List, Optional, Tuple

class GroupRepo:
    @staticmethod
    def create(name: str, creator_id: int) -> Tuple[Optional[int], Optional[str]]:
        conn, cur = get_db()
        try:
            cur.execute("INSERT INTO groupss (group_name, created_by) VALUES (%s, %s)", (name, creator_id))
            group_id = cur.lastrowid
            cur.execute(
                "INSERT INTO group_members (group_id, user_id) VALUES (%s, %s)",
                (group_id, creator_id),
            )
            cur.execute("SELECT username FROM users WHERE id = %s", (creator_id,))
            row = cur.fetchone()
            display_name = row["username"] if row else str(creator_id)
            cur.execute(
                "INSERT INTO group_people (group_id, user_id, display_name) VALUES (%s, %s, %s)",
                (group_id, creator_id, display_name),
            )
            conn.commit()
            return group_id, None
        except Exception as e:
            conn.rollback()
            print(f"[GroupRepo.create] {e}")
            return None, str(e)
        finally:
            cur.close()

    @staticmethod
    def delete(group_id: int) -> bool:
        conn, cur = get_db()
        try:
            cur.execute("DELETE mes FROM manual_expense_shares mes JOIN manual_expenses me ON mes.expense_id = me.expense_id WHERE me.group_id = %s", (group_id,))
            cur.execute("DELETE FROM manual_expenses WHERE group_id = %s", (group_id,))
            cur.execute("DELETE FROM settlements WHERE group_id = %s", (group_id,))
            cur.execute("DELETE FROM group_people WHERE group_id = %s", (group_id,))
            cur.execute("DELETE FROM group_members WHERE group_id = %s", (group_id,))
            cur.execute("DELETE FROM groupss WHERE group_id = %s", (group_id,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def get_user_groups(user_id: int) -> List[Group]:
        _, cur = get_db()
        try:
            cur.execute(
                """SELECT g.group_id, g.group_name, g.created_by, g.created_at,
                          COUNT(gp.person_id) AS member_count
                   FROM groupss g
                   JOIN group_members gm ON g.group_id = gm.group_id
                   LEFT JOIN group_people gp ON g.group_id = gp.group_id
                   WHERE gm.user_id = %s
                   GROUP BY g.group_id, g.group_name, g.created_by, g.created_at""",
                (user_id,)
            )
            return [GroupRepo._row_to_group(r) for r in cur.fetchall()]
        finally:
            cur.close()

    @staticmethod
    def get_member_user_ids(group_id: int) -> List[int]:
        _, cur = get_db()
        try:
            cur.execute(
                "SELECT DISTINCT user_id FROM group_members WHERE group_id = %s AND user_id IS NOT NULL",
                (group_id,),
            )
            return [int(r['user_id']) for r in cur.fetchall()]
        finally:
            cur.close()

    @staticmethod
    def add_person(group_id: int, display_name: str, user_id: Optional[int] = None) -> bool:
        conn, cur = get_db()
        try:
            if user_id is None:
                cur.execute("SELECT id FROM users WHERE username = %s", (display_name,))
                row = cur.fetchone()
                if row:
                    user_id = row["id"]
                    cur.execute("INSERT IGNORE INTO group_members (group_id, user_id) VALUES (%s,%s)", (group_id, user_id))
            cur.execute(
                "INSERT INTO group_people (group_id, user_id, display_name) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE display_name = display_name",
                (group_id, user_id, display_name.strip())
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def remove_person(group_id: int, person_id: int) -> bool:
        conn, cur = get_db()
        try:
            cur.execute("DELETE FROM manual_expense_shares WHERE person_id = %s", (person_id,))
            cur.execute("DELETE FROM group_people WHERE group_id=%s AND person_id=%s", (group_id, person_id))
            conn.commit()
            return cur.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def get_people(group_id: int) -> List[Person]:
        _, cur = get_db()
        try:
            cur.execute("SELECT person_id, group_id, user_id, display_name FROM group_people WHERE group_id=%s ORDER BY person_id", (group_id,))
            return [Person(**r) for r in cur.fetchall()]
        finally:
            cur.close()

    @staticmethod
    def get_member_count(group_id: int) -> int:
        _, cur = get_db()
        try:
            cur.execute("SELECT COUNT(*) AS c FROM group_people WHERE group_id=%s", (group_id,))
            return cur.fetchone()["c"]
        finally:
            cur.close()

    @staticmethod
    def _row_to_group(row: dict) -> Group:
        return Group(
            group_id     = row["group_id"],
            group_name   = row["group_name"],
            created_by   = row["created_by"],
            created_at   = row.get("created_at"),
            member_count = row.get("member_count", 0),
        )