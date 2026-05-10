# crediflux/managers/group_manager.py
from repositories.group_repo import GroupRepo
from core.models import Group, Person
from typing import List, Optional

class GroupManager:
    @staticmethod
    def create(name: str, creator_id: int) -> Optional[Group]:
        if not name.strip():
            return None
        gid = GroupRepo.create(name.strip(), creator_id)
        if gid is None:
            return None
        groups = GroupRepo.get_user_groups(creator_id)
        return next((g for g in groups if g.group_id == gid), None)

    @staticmethod
    def get_user_groups(user_id: int) -> List[Group]:
        return GroupRepo.get_user_groups(user_id)

    @staticmethod
    def delete(group_id: int) -> bool:
        return GroupRepo.delete(group_id)

    @staticmethod
    def add_member(group_id: int, display_name: str) -> tuple:
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