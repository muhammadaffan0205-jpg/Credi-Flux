# backend/managers/auth_manager.py
from utils.hashing import generate_salt, hash_password, verify_password
from repositories.user_repo import UserRepo
from core.models import User

class AuthManager:
    @staticmethod
    def register(full_name: str, username: str, phone: str, password: str):
        if not all([full_name.strip(), username.strip(), phone.strip(), password]):
            return False, "All fields are required."
        if len(phone) < 10:
            return False, "Enter a valid phone number."
        if UserRepo.get_by_username(username):
            return False, "Username already taken."
        if UserRepo.get_by_phone(phone):
            return False, "Phone number already registered."
        salt = generate_salt()
        password_hash = hash_password(password, salt)
        uid = UserRepo.save(full_name.strip(), username.strip(), phone.strip(), password_hash, salt)
        if uid is None:
            return False, "Registration failed."
        user = UserRepo.get_by_id(uid)
        return True, user

    @staticmethod
    def login(username: str, password: str):
        if not username or not password:
            return False, "Enter username and password."
        user = UserRepo.get_by_username(username)
        if not user:
            return False, "Username not found."
        if not verify_password(password, user.salt, user.password):
            return False, "Wrong password."
        return True, user

    @staticmethod
    def update_easypaisa(user_id: int, ep_number: str):
        if not ep_number.strip():
            return False, "Enter EasyPaisa number."
        ok = UserRepo.update_easypaisa_num(user_id, ep_number.strip())
        if ok:
            return True, "Saved."
        return False, "Could not save. Try restarting the app so the database migration runs, or check MySQL errors."