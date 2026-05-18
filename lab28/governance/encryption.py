"""
Layer 5 — Governance: Field-Level Encryption
AES-256-GCM encryption for data at rest and in transit.
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key() -> bytes:
    """Generate a random 256-bit (32-byte) encryption key"""
    return AESGCM.generate_key(bit_length=256)


def encrypt_value(plaintext: str, key: bytes) -> str:
    """Encrypt a string value with AES-256-GCM.
    Returns base64-encoded ciphertext (nonce + ciphertext).
    """
    if isinstance(key, str):
        key = bytes.fromhex(key) if len(key) == 64 else key.encode()[:32]
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Prepend nonce to ciphertext
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode("ascii")


def decrypt_value(encrypted: str, key: bytes) -> str:
    """Decrypt a value encrypted with encrypt_value."""
    if isinstance(key, str):
        key = bytes.fromhex(key) if len(key) == 64 else key.encode()[:32]
    aesgcm = AESGCM(key)
    combined = base64.b64decode(encrypted)
    nonce, ciphertext = combined[:12], combined[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def encrypt_record(record: dict, sensitive_fields: list[str], key: bytes) -> dict:
    """Encrypt sensitive fields in a record."""
    encrypted = dict(record)
    for field in sensitive_fields:
        if field in encrypted and encrypted[field] is not None:
            encrypted[field] = encrypt_value(str(encrypted[field]), key)
    return encrypted


def encrypt_file(input_path: str, output_path: str, key: bytes) -> None:
    """Encrypt an entire file with AES-256-GCM."""
    with open(input_path, "rb") as f:
        plaintext = f.read()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    with open(output_path, "wb") as f:
        f.write(nonce + ciphertext)
