from flask_app import bcrypt, BCRYPT_HASH_REGEX


def bcrypt_password_if_not(password: str) -> str:
    if isinstance(password, bytes):
        password = password.decode()

    # If the password is not already written as a bcrypt hash, hash it with bcrypt.
    if BCRYPT_HASH_REGEX.match(password) is None:
        return bytes(bcrypt.generate_password_hash(password)).decode()
    else:
        return password

