from unittest import TestCase
import base64

from security.security_manager import SecurityManager


class TestSecurityManager(TestCase):

    def setUp(self):
        # 16-byte test key -> AES-128 (pycryptodome picks the variant based on key length)
        self.key = "0123456789abcdef"
        self.manager = SecurityManager(self.key)

    def test_encrypt_data_returns_base64_string(self):
        # --- ARRANGE ---
        data = {"status": "DROWSY_DETECTED", "probability": 0.91}

        # --- ACT ---
        result = self.manager.encrypt_data(data)

        # --- ASSERT ---
        self.assertIsInstance(result, str)
        # must be decodable as base64 without errors
        decoded = base64.b64decode(result)
        # must contain at least IV (16 bytes) + one encrypted block (16 bytes)
        self.assertGreaterEqual(len(decoded), 32)

    def test_encrypt_data_uses_random_iv_each_time(self):
        # --- ARRANGE ---
        data = {"status": "DROWSY_DETECTED", "probability": 0.91}

        # --- ACT ---
        result1 = self.manager.encrypt_data(data)
        result2 = self.manager.encrypt_data(data)

        # --- ASSERT ---
        # same plaintext data, but different random IV -> different encrypted output
        self.assertNotEqual(result1, result2)

    def test_decrypt_data_returns_original_dict(self):
        # --- ARRANGE ---
        data = {"status": "DROWSY_DETECTED", "timestamp": "2026-07-09 12:00:00", "probability": 0.75}

        # --- ACT ---
        encrypted = self.manager.encrypt_data(data)
        decrypted = self.manager.decrypt_data(encrypted)

        # --- ASSERT ---
        self.assertEqual(decrypted, data)
