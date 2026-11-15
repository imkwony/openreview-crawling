"""Password-encrypt the data file so a static host can't serve it in the clear.

Format (JSON): gzip -> AES-256-GCM, key from PBKDF2-HMAC-SHA256. The browser
(assets/table.js) reverses it with WebCrypto, so keep the two in sync.
"""
import base64
import gzip
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 600_000
VERSION = 1


def normalize_password(password):
    """Case-insensitive, whitespace-insensitive: 'Foo  Bar' == 'foo bar'."""
    return " ".join(password.lower().split())


def _key(password, salt, iterations):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(normalize_password(password).encode("utf-8"))


def _b64(raw):
    return base64.b64encode(raw).decode("ascii")


def encrypt_payload(plaintext, password, iterations=ITERATIONS):
    salt, iv = os.urandom(16), os.urandom(12)
    sealed = AESGCM(_key(password, salt, iterations)).encrypt(iv, gzip.compress(plaintext, 9), None)
    return {"v": VERSION, "iter": iterations, "salt": _b64(salt), "iv": _b64(iv), "data": _b64(sealed)}


def decrypt_payload(payload, password):
    key = _key(password, base64.b64decode(payload["salt"]), payload["iter"])
    sealed = AESGCM(key).decrypt(base64.b64decode(payload["iv"]), base64.b64decode(payload["data"]), None)
    return gzip.decompress(sealed)
