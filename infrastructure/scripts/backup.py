"""Backup, restore and diagnostics CLI (spec §22 Phase 8).

Thin wrappers over `syltra_operations` so the documented `make` targets do what
the documentation says.
"""

import argparse
import getpass
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from syltra_operations import (
    BackupError,
    CollectionError,
    collect_home,
    create_backup,
    diagnostic_bundle,
    read_manifest,
    restore_backup,
)


def _passphrase(confirm: bool = False) -> str:
    value = getpass.getpass("Backup passphrase: ")
    if confirm and value != getpass.getpass("Confirm passphrase: "):
        print("passphrases do not match", file=sys.stderr)
        raise SystemExit(2)
    return value


def _database_url() -> str:
    """Credentials from the environment only (spec §25.3)."""
    import os

    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        print("POSTGRES_PASSWORD is not set; source your .env", file=sys.stderr)
        raise SystemExit(2)
    user = os.environ.get("POSTGRES_USER", "syltra")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    database = os.environ.get("POSTGRES_DB", "syltra")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


class _Session:
    """Adapts a SQLAlchemy connection to the collector's narrow protocol."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def execute(self, statement: str, parameters: dict[str, Any]) -> Any:
        return self._connection.execute(text(statement), parameters)


def _collect(home_id: str) -> dict[str, Any]:
    """Read every household table for this home.

    Raises rather than returning a partial result: a backup missing a table is
    a backup that fails when someone needs it.
    """
    engine = create_engine(_database_url())
    with engine.connect() as connection:
        result = collect_home(_Session(connection), home_id)
    print(f"  collected {result.row_count} rows across {len(result.tables)} tables")
    return result.as_payload()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="syltra-backup")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create an encrypted backup")
    create.add_argument("--home-id", required=True)
    create.add_argument("--out", type=Path, required=True)

    info = sub.add_parser("info", help="read a backup manifest (no passphrase)")
    info.add_argument("file", type=Path)

    restore = sub.add_parser("restore", help="verify and restore a backup")
    restore.add_argument("file", type=Path)

    diagnostics = sub.add_parser("diagnostics", help="build a redacted support bundle")
    diagnostics.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            manifest = create_backup(
                _collect(args.home_id), _passphrase(confirm=True), args.out,
                home_id=args.home_id,
            )
            print(f"✔ encrypted backup written to {args.out}")
            print(f"  home={manifest.home_id} created={manifest.created_at}")
        elif args.command == "info":
            manifest = read_manifest(args.file)
            print(json.dumps(manifest.__dict__, indent=2))
        elif args.command == "restore":
            payload, manifest = restore_backup(args.file, _passphrase())
            print(f"✔ verified backup for {manifest.home_id} ({manifest.created_at})")
            print(f"  {len(payload)} top-level sections")
        elif args.command == "diagnostics":
            bundle = diagnostic_bundle({"note": "collected by CLI"})
            args.out.write_text(json.dumps(bundle, indent=2))
            print(f"✔ redacted diagnostic bundle written to {args.out}")
    except (BackupError, CollectionError) as exc:
        print(f"✘ {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
