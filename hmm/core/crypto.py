from functools import cache
from cryptography.fernet import Fernet

from hmm.config import get_settings
from passlib.hash import bcrypt

password_context = bcrypt.using(salt=get_settings().auth.salt, rounds=12)


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


@cache
def get_fernet():
    return Fernet(get_settings().auth.real_key)
