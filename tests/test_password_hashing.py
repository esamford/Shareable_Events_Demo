import random
import unittest

from flask_app.utils.passwords import bcrypt_password_if_not
from flask_app import bcrypt


class TestPasswordHashing(unittest.TestCase):
    def test_passwords_match(self):
        password = "p@sSw0rd123"
        hashed_password = bcrypt_password_if_not(password)

        self.assertTrue(bcrypt.check_password_hash(hashed_password, password))

    def test_multiple_hashes(self):
        # Passwords should not be hashed again if they are already in a hashed state.
        password = "p@sSw0rd123"

        hashed_password = bcrypt_password_if_not(password)
        for _ in range(10):
            print(hashed_password)
            hashed_password_2 = bcrypt_password_if_not(hashed_password)
            self.assertEqual(hashed_password, hashed_password_2)
            hashed_password = hashed_password_2

    def test_print_hashed_passwords(self):
        for _ in range(50):
            password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz1234567890") for __ in range(32)])
            print(bytes(bcrypt_password_if_not(password)).decode())

