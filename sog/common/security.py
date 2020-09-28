""" security class - manages password encryption and comparison
    The encryption library is abstracted to this file in case we want to
    change it at some later date """

from passlib.context import CryptContext
from re import sub

cryptObj = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)


def hash_password(password):
    return cryptObj.hash(password)


def password_is_encrypted(password):
    crypt_scheme_prefix = sub("_.*", "", cryptObj.default_scheme())
    return(crypt_scheme_prefix in password)


def check_encrypted_password(password, password_hash):
    try:
        return(cryptObj.verify(password, password_hash))
    except ValueError:
        return(False)
    return False
