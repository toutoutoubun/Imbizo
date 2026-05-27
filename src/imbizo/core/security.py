"""Local security controls for project data."""

from __future__ import annotations

import os
from pathlib import Path

from imbizo.app.errors import UserFacingError


def is_probably_nonlocal_path(path: Path) -> bool:
    """Return whether a path looks like a network or mounted remote destination."""

    text = str(path)
    lowered = text.lower()
    return lowered.startswith("\\\\") or lowered.startswith("smb://") or lowered.startswith("nfs://")


def require_local_export_destination(path: Path, confirmed: bool = False) -> None:
    """Warn-block export destinations that appear non-local unless confirmed."""

    if is_probably_nonlocal_path(path) and not confirmed:
        raise UserFacingError("This export destination looks non-local. Confirm before exporting sensitive data.")


def encrypt_file_aes256(source: Path, destination: Path, passphrase: str) -> Path:
    """Encrypt a file with AES-256-GCM using a passphrase.

    The implementation uses the open-source `cryptography` package when the
    optional security dependency is installed. No key escrow or network service
    is used; the passphrase is never stored by Imbizo-CS Workbench.
    """

    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
    except ImportError as exc:
        raise UserFacingError("Encryption requires the optional local security dependency: cryptography.") from exc

    salt = os.urandom(16)
    nonce = os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    key = kdf.derive(passphrase.encode("utf-8"))
    encrypted = AESGCM(key).encrypt(nonce, source.read_bytes(), None)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"IMBIZO-AES256-GCM\0" + salt + nonce + encrypted)
    return destination


def decrypt_file_aes256(source: Path, destination: Path, passphrase: str) -> Path:
    """Decrypt a file encrypted with `encrypt_file_aes256`."""

    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
    except ImportError as exc:
        raise UserFacingError("Decryption requires the optional local security dependency: cryptography.") from exc

    blob = source.read_bytes()
    header = b"IMBIZO-AES256-GCM\0"
    if not blob.startswith(header):
        raise UserFacingError("This file does not look like an Imbizo encrypted file.")
    payload = blob[len(header):]
    salt, nonce, encrypted = payload[:16], payload[16:28], payload[28:]
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    key = kdf.derive(passphrase.encode("utf-8"))
    plaintext = AESGCM(key).decrypt(nonce, encrypted, None)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(plaintext)
    return destination


def delete_and_verify(path: Path, passes: int = 1) -> None:
    """Overwrite a local file before deleting it, then verify removal.

    Modern SSD wear-leveling can limit overwrite guarantees, so this function
    is a best-effort local deletion control rather than a forensic guarantee.
    """

    if not path.exists():
        return
    if path.is_dir():
        raise UserFacingError("Delete-and-verify expects a file, not a folder.")
    size = path.stat().st_size
    with path.open("r+b") as handle:
        for _ in range(max(1, passes)):
            handle.seek(0)
            handle.write(os.urandom(size))
            handle.flush()
            os.fsync(handle.fileno())
    path.unlink()
    if path.exists():
        raise UserFacingError("The file could not be deleted.")
