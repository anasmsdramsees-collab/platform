"""Encrypted backup and restore (spec §22 Phase 8, §4.2, §26).

A backup of a SYLTRA hub contains a household's behavioural history: when
people are home, when they sleep, what they cook, which rooms they use. It is
the single most sensitive artifact the platform produces, so encryption is not
an option flag — `create_backup` has no path that writes plaintext.

Design choices worth stating:

- **AES-256-GCM**, which authenticates as well as encrypts. A corrupted or
  tampered backup fails to decrypt rather than restoring subtly wrong data.
- **scrypt** for key derivation from a passphrase, with per-backup salt. An
  operator passphrase is low-entropy, and scrypt makes an offline attack on a
  stolen backup expensive in memory as well as time.
- **The manifest is authenticated but not encrypted.** An operator needs to see
  what a backup contains — which home, when, which schema version — before
  deciding whether to restore it. It therefore carries no household data, only
  metadata, and is bound into the AEAD so it cannot be swapped.
"""

import hashlib
import json
import os
import secrets
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

BACKUP_FORMAT = "syltra-backup-v1"
MAGIC = b"SYLTRABK1"

SALT_BYTES = 16
NONCE_BYTES = 12
KEY_BYTES = 32

# scrypt parameters: ~64 MiB of memory per derivation. Deliberately costly for
# an attacker with a stolen backup file, and acceptable for an operator who
# restores rarely.
SCRYPT_N = 2**16
SCRYPT_R = 8
SCRYPT_P = 1

MIN_PASSPHRASE_LENGTH = 12


class BackupError(RuntimeError):
    """Backup could not be created or restored."""


class BackupIntegrityError(BackupError):
    """The backup is corrupt, tampered with, or the passphrase is wrong.

    Deliberately one error for all three: distinguishing "wrong passphrase"
    from "tampered file" would tell an attacker which of the two they achieved.
    """


@dataclass
class BackupManifest:
    """Metadata an operator can read before restoring. No household data."""

    format: str = BACKUP_FORMAT
    home_id: str = ""
    hub_id: str = ""
    created_at: str = ""
    schema_version: str = ""
    table_counts: dict[str, int] = field(default_factory=dict)
    payload_sha256: str = ""
    """Digest of the plaintext, so a restore can prove it recovered exactly
    what was backed up."""

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()


def derive_key(passphrase: str, salt: bytes) -> bytes:
    if len(passphrase) < MIN_PASSPHRASE_LENGTH:
        msg = (
            f"backup passphrase must be at least {MIN_PASSPHRASE_LENGTH} characters; "
            "a household's behavioural history is behind it"
        )
        raise BackupError(msg)
    kdf = Scrypt(salt=salt, length=KEY_BYTES, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return kdf.derive(passphrase.encode())


def create_backup(
    payload: dict[str, Any],
    passphrase: str,
    destination: Path,
    home_id: str,
    hub_id: str = "",
    schema_version: str = "1.0",
) -> BackupManifest:
    """Encrypt ``payload`` to ``destination``.

    There is no plaintext branch: the only way this function writes a file is
    through the AEAD.
    """
    plaintext = json.dumps(payload, sort_keys=True, default=str).encode()
    manifest = BackupManifest(
        home_id=home_id,
        hub_id=hub_id,
        created_at=datetime.now(tz=UTC).isoformat(),
        schema_version=schema_version,
        table_counts={
            key: len(value) for key, value in payload.items() if isinstance(value, list)
        },
        payload_sha256=hashlib.sha256(plaintext).hexdigest(),
    )

    salt = secrets.token_bytes(SALT_BYTES)
    nonce = secrets.token_bytes(NONCE_BYTES)
    key = derive_key(passphrase, salt)
    manifest_bytes = manifest.to_bytes()
    # The manifest is authenticated additional data: readable, but it cannot be
    # altered or swapped onto a different backup without decryption failing.
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, manifest_bytes)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        handle.write(MAGIC)
        handle.write(len(manifest_bytes).to_bytes(4, "big"))
        handle.write(manifest_bytes)
        handle.write(salt)
        handle.write(nonce)
        handle.write(ciphertext)
    # Readable by the owner only: a hub backup on a shared volume should not be
    # world-readable.
    os.chmod(destination, 0o600)  # noqa: S103, PTH101
    return manifest


def read_manifest(source: Path) -> BackupManifest:
    """Read the manifest without the passphrase, for inspection before restore."""
    with source.open("rb") as handle:
        if handle.read(len(MAGIC)) != MAGIC:
            msg = f"{source} is not a SYLTRA backup"
            raise BackupError(msg)
        length = int.from_bytes(handle.read(4), "big")
        manifest_bytes = handle.read(length)
    try:
        return BackupManifest(**json.loads(manifest_bytes))
    except (ValueError, TypeError) as exc:
        msg = "backup manifest is unreadable"
        raise BackupError(msg) from exc


def restore_backup(source: Path, passphrase: str) -> tuple[dict[str, Any], BackupManifest]:
    """Decrypt and verify a backup.

    Verification is belt and braces: the AEAD tag proves the ciphertext and
    manifest were not altered, and the payload digest proves the plaintext is
    exactly what was backed up.
    """
    with source.open("rb") as handle:
        if handle.read(len(MAGIC)) != MAGIC:
            msg = f"{source} is not a SYLTRA backup"
            raise BackupError(msg)
        length = int.from_bytes(handle.read(4), "big")
        manifest_bytes = handle.read(length)
        salt = handle.read(SALT_BYTES)
        nonce = handle.read(NONCE_BYTES)
        ciphertext = handle.read()

    manifest = BackupManifest(**json.loads(manifest_bytes))
    key = derive_key(passphrase, salt)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, manifest_bytes)
    except InvalidTag as exc:
        msg = "backup could not be decrypted: wrong passphrase, or the file was altered"
        raise BackupIntegrityError(msg) from exc

    digest = hashlib.sha256(plaintext).hexdigest()
    if manifest.payload_sha256 and digest != manifest.payload_sha256:
        msg = "restored payload does not match the digest recorded at backup time"
        raise BackupIntegrityError(msg)

    payload: dict[str, Any] = json.loads(plaintext)
    return payload, manifest


def looks_encrypted(source: Path) -> bool:
    """True when the file body carries no recognisable plaintext.

    Used by a test that asserts household data never reaches disk in the clear.
    """
    body = source.read_bytes()
    manifest_length = int.from_bytes(body[len(MAGIC) : len(MAGIC) + 4], "big")
    payload = body[len(MAGIC) + 4 + manifest_length :]
    # A JSON document would be full of ASCII; ciphertext is not.
    printable = sum(1 for byte in payload if 32 <= byte < 127)
    return printable / max(len(payload), 1) < 0.5
