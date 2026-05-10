# crediflux/managers/auth_manager.py
# this is the auth manager file
import hashlib
from repositories.user_repo import UserRepo
from core.models import User
from typing import Optional

class AuthManager:
    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def register(full_name: str, username: str, phone: str, password: str) -> tuple:
        if not all([full_name.strip(), username.strip(), phone.strip(), password]):
            return False, "All fields are required."
        if len(phone) < 10:
            return False, "Enter a valid phone number."
        if UserRepo.get_by_username(username):
            return False, "Username already taken."
        if UserRepo.get_by_phone(phone):
            return False, "Phone number already registered."
        hashed = AuthManager._hash(password)
        uid = UserRepo.save(full_name.strip(), username.strip(), phone.strip(), hashed)
        if uid is None:
            return False, "Registration failed. Try again."
        user = UserRepo.get_by_id(uid)
        return True, user

    @staticmethod
    def login(username: str, password: str) -> tuple:
        if not username or not password:
            return False, "Enter username and password."
        user = UserRepo.get_by_username(username)
        if not user:
            return False, "Username not found."
        if user.password != AuthManager._hash(password):
            return False, "Wrong password."
        return True, user

    @staticmethod
    def update_easypaisa(user_id: int, ep_number: str) -> tuple:
        if not ep_number.strip():
            return False, "Enter EasyPaisa number."
        ok = UserRepo.update_easypaisa_num(user_id, ep_number.strip())
        return (True, "Saved.") if ok else (False, "Could not save.")