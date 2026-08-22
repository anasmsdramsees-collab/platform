"""SYLTRA Edge integration tests (spec §27).

Home Assistant is not a dependency of this repository — ADR-001 keeps it an
embedded, replaceable runtime, and installing it here would invert that. The
integration's pure logic therefore lives in `validation.py`, which imports no
Home Assistant module and can be tested directly; the coordinator and entity
classes are exercised inside Home Assistant's own test harness during
integration validation, which is where they belong.
"""

import importlib.util
import json
import pathlib
import sys

import pytest

INTEGRATION = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "syltra_edge"
MANIFEST = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
STRINGS = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
EN = json.loads((INTEGRATION / "translations" / "en.json").read_text(encoding="utf-8"))
AR = json.loads((INTEGRATION / "translations" / "ar.json").read_text(encoding="utf-8"))
SERVICES = (INTEGRATION / "services.yaml").read_text(encoding="utf-8")


def _module_source(name: str) -> str:
    return (INTEGRATION / f"{name}.py").read_text(encoding="utf-8")


def _load_validation() -> object:
    """Import the integration's Home-Assistant-free helper module."""
    spec = importlib.util.spec_from_file_location(
        "syltra_edge_validation", INTEGRATION / "validation.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validation = _load_validation()


# ── manifest (spec §27) ──


def test_the_domain_is_unique_to_syltra() -> None:
    # Must not shadow a built-in integration (spec §27).
    assert MANIFEST["domain"] == "syltra_edge"
    assert MANIFEST["domain"] not in {"homeassistant", "mqtt", "zha", "matter", "default_config"}


def test_the_integration_declares_a_config_flow() -> None:
    assert MANIFEST["config_flow"] is True


def test_the_integration_is_local_and_takes_no_external_requirements() -> None:
    # Spec §4.2: no cloud dependency for local control.
    assert MANIFEST["iot_class"].startswith("local")
    assert MANIFEST["requirements"] == []


def test_every_required_file_exists() -> None:
    # The minimum file set from spec §27.
    for filename in (
        "manifest.json",
        "__init__.py",
        "config_flow.py",
        "const.py",
        "coordinator.py",
        "diagnostics.py",
        "services.yaml",
        "strings.json",
        "translations/ar.json",
        "translations/en.json",
    ):
        assert (INTEGRATION / filename).is_file(), f"missing {filename}"


# ── URL validation ──


@pytest.mark.parametrize(
    ("url", "error"),
    [
        ("http://localhost:8081", None),
        ("https://hub.local:8443", None),
        ("http://192.168.1.50:8081/", None),
        ("ftp://localhost:8081", "invalid_scheme"),
        ("localhost:8081", "invalid_scheme"),
        ("", "invalid_scheme"),
        ("http://", "invalid_host"),
    ],
)
def test_url_validation(url: str, error: str | None) -> None:
    assert validation.validate_url(url) == error  # type: ignore[attr-defined]


# ── diagnostics redaction (spec §27, §25.3) ──


@pytest.mark.safety
def test_secrets_are_redacted_from_diagnostics() -> None:
    payload = {
        "edge_url": "http://hub.local:8081",
        "token": "super-secret-token",
        "nested": {"password": "hunter2", "api_key": "abc123", "ok": "visible"},
        "list": [{"secret": "s3cr3t"}, {"harmless": 1}],
    }
    result = validation.redact(payload)  # type: ignore[attr-defined]
    serialized = json.dumps(result)
    for secret in ("super-secret-token", "hunter2", "abc123", "s3cr3t"):
        assert secret not in serialized, f"{secret} leaked into diagnostics"
    assert result["nested"]["ok"] == "visible"  # type: ignore[index]


@pytest.mark.safety
def test_a_credential_embedded_in_the_url_cannot_survive() -> None:
    # A URL like http://user:token@host/ would otherwise carry a secret into a
    # bundle shared with support.
    assert (
        validation.safe_url(  # type: ignore[attr-defined]
            "http://admin:s3cr3t@hub.local:8081/path?token=x"
        )
        == "http://hub.local:8081"
    )


def test_redaction_keys_cover_the_usual_suspects() -> None:
    for key in ("token", "password", "api_key", "authorization", "secret"):
        assert key in validation.REDACTED_KEYS  # type: ignore[attr-defined]


def test_the_pure_helpers_import_no_home_assistant_module() -> None:
    # The point of validation.py: it must stay importable without Home
    # Assistant, or these tests could not run in this repository at all.
    assert "homeassistant" not in _module_source("validation")


# ── services (spec §27) ──


def test_only_syltra_specific_services_are_registered() -> None:
    # Spec §27: register only SYLTRA-specific services that do not duplicate
    # standard entity services.
    registered = [
        line.split(":")[0]
        for line in SERVICES.splitlines()
        if line and not line.startswith((" ", "#")) and line.strip().endswith(":")
    ]
    assert registered == ["refresh_health"]
    for standard in ("turn_on", "turn_off", "toggle", "set_temperature", "lock", "unlock"):
        assert f"\n{standard}:" not in SERVICES


@pytest.mark.safety
def test_the_integration_does_not_control_devices() -> None:
    # ADR-001: device control goes through the Edge Agent and the supported
    # Home Assistant APIs, never through a second component.
    source = _module_source("__init__") + _module_source("coordinator")
    for forbidden in ("async_call", "call_service", "turn_on", "turn_off"):
        assert forbidden not in source


def test_home_assistant_core_is_never_modified() -> None:
    # Spec §0 rule 11 and ADR-001. The integration lives entirely in its own
    # directory and imports Home Assistant only as a consumer.
    for path in INTEGRATION.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "homeassistant.core." not in source.replace("from homeassistant.core import", "")
        assert "monkeypatch" not in source
        assert "setattr(homeassistant" not in source


# ── translations (spec §27) ──


def _flatten(data: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        keys.add(path)
        if isinstance(value, dict):
            keys |= _flatten(value, path)
    return keys


def test_english_and_arabic_translations_have_the_same_shape() -> None:
    assert _flatten(EN) == _flatten(AR)


def test_translations_match_the_strings_file() -> None:
    assert _flatten(STRINGS) == _flatten(EN)


def test_arabic_translations_are_arabic() -> None:
    def walk(node: object) -> list[str]:
        if isinstance(node, dict):
            return [text for value in node.values() for text in walk(value)]
        return [node] if isinstance(node, str) else []

    for text in walk(AR):
        # Technical tokens (URLs, "TLS", "SYLTRA Edge") legitimately stay Latin;
        # every sentence-length string must contain Arabic.
        if len(text) > 25:
            assert any("؀" <= ch <= "ۿ" for ch in text), f"not translated: {text}"


def test_every_config_flow_error_has_a_message_in_both_languages() -> None:
    errors = set(EN["config"]["error"])
    # `cannot_connect` is raised by the flow; the validation errors live in the
    # Home-Assistant-free helper module.
    source = _module_source("config_flow") + _module_source("validation")
    raised = {"cannot_connect", "invalid_scheme", "invalid_host"}
    assert raised <= errors, f"undocumented errors: {raised - errors}"
    for error in raised:
        assert error in source
        assert AR["config"]["error"][error]


def test_the_config_flow_explains_that_the_address_stays_local() -> None:
    # Spec §4.1: the platform is local-first, and the installer should know it.
    assert "home network" in EN["config"]["step"]["user"]["description"]
    assert "شبكة منزلك" in AR["config"]["step"]["user"]["description"]
