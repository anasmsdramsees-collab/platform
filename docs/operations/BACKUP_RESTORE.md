# Backup and restore

A SYLTRA backup contains a household's behavioural history: when people are
home, when they sleep, what they cook, which rooms they use. Treat it as the
most sensitive artifact the platform produces, because it is.

## Taking a backup

```bash
make backup
```

Prompts for a passphrase and writes an encrypted archive. There is no plaintext
option — `create_backup()` has no code path that writes unencrypted data.

| Property | Choice | Why |
|---|---|---|
| Cipher | AES-256-GCM | Authenticated: a tampered backup fails to decrypt rather than restoring subtly wrong data |
| Key derivation | scrypt, N=2¹⁶, r=8, p=1 | ~64 MiB per derivation; an operator passphrase is low-entropy, so an offline attack must be made expensive |
| Salt and nonce | Fresh per backup | Two backups of identical data differ, so an observer cannot tell when nothing changed |
| File mode | `0600` | A hub backup on a shared volume should not be world-readable |
| Minimum passphrase | 12 characters | Enforced, not advised |

## Inspecting a backup without the passphrase

```bash
make backup-info FILE=hub-2026-08-19.syltrabk
```

The manifest is authenticated but not encrypted, so an operator can see *what* a
backup is before deciding to restore it: home id, hub id, creation time, schema
version, row counts. It deliberately carries **no household data** — a test
asserts that.

Because the manifest is bound into the AEAD as additional data, it cannot be
edited or swapped onto a different backup: doing so makes decryption fail.

## Restoring

```bash
make restore FILE=hub-2026-08-19.syltrabk
```

Verification is belt and braces:

1. The AEAD tag proves the ciphertext and manifest were not altered.
2. The payload SHA-256 recorded at backup time proves the plaintext is exactly
   what was backed up.

A wrong passphrase and a tampered file produce **the same error**, deliberately:
distinguishing them would tell an attacker which of the two they achieved.

## Before you restore

- Take a backup of the current state first. Restoring is destructive.
- Check the manifest's `home_id` matches the hub you are restoring to.
- Stop the services, restore, run `make migrate`, then start.

## What a backup does and does not contain

**Contains:** homes, rooms, devices, event history, current state, contexts,
recommendations, policy decisions, actions, feedback, risk cases, audit trail,
model metadata.

**Does not contain:** access tokens (only hashes are ever stored, and they are
excluded), the backup passphrase, or anything from the classes spec §26 forbids
collecting — no audio, no video, no biometrics, no location trails.

## Storage

- Keep backups off the hub. A backup on the machine it protects is not a backup.
- Keep the passphrase somewhere separate from the archive.
- **The passphrase cannot be recovered.** There is no escrow, no recovery key,
  and no vendor path to decrypt a household's data — which is the point.

## Testing a restore

Do it. An untested backup is a hypothesis.

```bash
make test-integration   # includes a backup round-trip against a real database
```
