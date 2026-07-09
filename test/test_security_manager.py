from unittest import TestCase
import base64

from security.security_manager import SecurityManager


class TestSecurityManager(TestCase):

    def setUp(self):
        # Chiave di test da 16 byte -> AES-128 (pycryptodome sceglie la variante dalla lunghezza chiave)
        self.key = "0123456789abcdef"
        self.manager = SecurityManager(self.key)

    def test_encrypt_data_returns_base64_string(self):
        # --- ARRANGE ---
        data = {"status": "DROWSY_DETECTED", "probability": 0.91}

        # --- ACT ---
        result = self.manager.encrypt_data(data)

        # --- ASSERT ---
        self.assertIsInstance(result, str)
        # deve essere decodificabile in base64 senza errori
        decoded = base64.b64decode(result)
        # deve contenere almeno IV (16 byte) + un blocco cifrato (16 byte)
        self.assertGreaterEqual(len(decoded), 32)

    def test_encrypt_data_uses_random_iv_each_time(self):
        # --- ARRANGE ---
        data = {"status": "DROWSY_DETECTED", "probability": 0.91}

        # --- ACT ---
        result1 = self.manager.encrypt_data(data)
        result2 = self.manager.encrypt_data(data)

        # --- ASSERT ---
        # stesso dato in chiaro, ma IV casuale diverso -> output cifrato diverso
        self.assertNotEqual(result1, result2)

    def test_decrypt_data_returns_original_dict(self):
        # --- ARRANGE ---
        data = {"status": "DROWSY_DETECTED", "timestamp": "2026-07-09 12:00:00", "probability": 0.75}

        # --- ACT ---
        encrypted = self.manager.encrypt_data(data)
        decrypted = self.manager.decrypt_data(encrypted)

        # --- ASSERT ---
        self.assertEqual(decrypted, data)
