from cryptography.fernet import Fernet

from airedteam.storage.secretbox import SecretBox


def test_roundtrip():
    key = Fernet.generate_key().decode()
    box = SecretBox(key)
    ct = box.encrypt({"api_key": "sk-xxx"})
    pt = box.decrypt(ct)
    assert pt == {"api_key": "sk-xxx"}
