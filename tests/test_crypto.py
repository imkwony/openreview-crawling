import json

import pytest

from crawler.crypto import decrypt_payload, encrypt_payload, normalize_password


def test_normalize_password_is_case_and_space_insensitive():
    assert normalize_password("Some PASS Word") == "some pass word"
    assert normalize_password("  some   pass word ") == "some pass word"


def test_roundtrip_and_gzip_inside():
    rows = [["id1", "Title", 1, None, None, 0]]
    payload = encrypt_payload(json.dumps(rows).encode(), "Test Secret", iterations=1000)
    assert set(payload) == {"v", "iter", "salt", "iv", "data"}
    assert json.loads(decrypt_payload(payload, "test  secret")) == rows


def test_wrong_password_fails():
    payload = encrypt_payload(b"[]", "Test Secret", iterations=1000)
    with pytest.raises(Exception):
        decrypt_payload(payload, "Other Secret")


def test_ciphertext_does_not_contain_plaintext():
    secret = b"Very Distinctive Paper Title"
    payload = encrypt_payload(secret, "Test Secret", iterations=1000)
    assert secret.decode() not in json.dumps(payload)
