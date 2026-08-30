"""One error model, so a failure reads the same in a log, an API response and a
spoken reply."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SellaError(Exception):
    """Every failure carries a code for the machine and a sentence for a person.

    The spoken sentence is separate from the technical detail on purpose. A
    voice assistant that reads an exception aloud is a voice assistant nobody
    talks to twice.
    """

    code: str
    detail: str
    spoken: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


class ToolError(SellaError):
    """A tool ran and could not do what was asked."""


class PermissionRefused(SellaError):
    """The action is not permitted at this risk level for this user."""


class ProviderError(SellaError):
    """An external provider failed or timed out."""
