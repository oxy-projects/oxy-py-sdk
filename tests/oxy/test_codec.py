import unittest

from Crypto.Random import get_random_bytes

from oxy.utils.codec import md5, des, crypto, sha256


ORIGIN_MSG = '{"cleanOrderPriceInfo":{"payPrice":0,"orderCode":"2023030118223149810020125265498","type":2}}'


class CodecTestCase(unittest.TestCase):
    def test_md5(self):
        digest = md5.encrypt(ORIGIN_MSG)
        self.assertIsInstance(digest, str)
        self.assertEqual(len(digest), 32)

    def test_sha256(self):
        digest = sha256.encrypt(ORIGIN_MSG)
        self.assertIsInstance(digest, str)
        self.assertEqual(len(digest), 64)

    def test_des_roundtrip(self):
        key = get_random_bytes(8)
        iv = get_random_bytes(8)
        encrypted = des.encrypt(ORIGIN_MSG, key=key, iv=iv)
        decrypted = des.decrypt(encrypted, key=key, iv=iv)
        self.assertEqual(decrypted, ORIGIN_MSG)

    def test_rsa_roundtrip_generated_keys(self):
        private_key, public_key = crypto.generate_rsa_keys()
        _, encrypted = crypto.encrypt_message(public_key, ORIGIN_MSG)
        _, decrypted = crypto.decrypt_message(private_key, encrypted)
        self.assertEqual(decrypted, ORIGIN_MSG)
        _, sign = crypto.sign_message(private_key, ORIGIN_MSG)
        _, verified = crypto.verify_message(public_key, ORIGIN_MSG, sign)
        self.assertTrue(verified)


if __name__ == '__main__':
    unittest.main()
