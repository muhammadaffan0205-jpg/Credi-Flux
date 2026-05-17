# backend/managers/group_manager.py
from repositories.group_repo import GroupRepo
from core.models import Group, Person
from typing import List, Optional, Tuple

class GroupManager:
    @staticmethod
    def create(name: str, creator_id: int) -> Tuple[Optional[Group], Optional[str]]:
        if not name.strip():
            return None, "Enter a group name."
        gid, err = GroupRepo.create(name.strip(), creator_id)
        if gid is None:
            return None, err or "Could not create group in database."
        return Group(
            group_id=gid,
            group_name=name.strip(),
            created_by=creator_id,
            member_count=1,
        ), None

    @staticmethod
    def get_user_groups(user_id: int) -> List[Group]:
        return GroupRepo.get_user_groups(user_id)

    @staticmethod
    def delete(group_id: int) -> bool:
        return GroupRepo.delete(group_id)

    @staticmethod
    def add_member(group_id: int, display_name: str):
        if not display_name.strip():
            return False, "Enter a name."
        ok = GroupRepo.add_person(group_id, display_name.strip())
        return (True, f"'{display_name}' added.") if ok else (False, "Already in group or error.")

    @staticmethod
    def remove_member(group_id: int, person_id: int) -> bool:
        return GroupRepo.remove_person(group_id, person_id)

    @staticmethod
    def get_people(group_id: int) -> List[Person]:
        return GroupRepo.get_people(group_id)