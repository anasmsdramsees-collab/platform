"""Structured error model (spec §21).

Every failure returns the same envelope: a stable machine `error` code, a
human `message` in the caller's locale where one exists, and the correlation id
so a user reporting a problem can be traced through the logs.

Errors deliberately reveal nothing about internals — no stack traces, no table
names, no broker subjects (spec §14.9).
"""

from typing import Any

from fastapi import HTTPException


class ApiError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        correlation_id: str | None = None,
        **extra: Any,
    ) -> None:
        detail: dict[str, Any] = {"error": code, "message": message, **extra}
        if correlation_id:
            detail["correlation_id"] = correlation_id
        super().__init__(status_code=status_code, detail=detail)
        self.code = code


def unauthenticated(code: str, message: str) -> ApiError:
    return ApiError(401, code, message)


def forbidden(code: str, message: str) -> ApiError:
    return ApiError(403, code, message)


def not_found(code: str, message: str) -> ApiError:
    return ApiError(404, code, message)


def conflict(code: str, message: str, **extra: Any) -> ApiError:
    return ApiError(409, code, message, **extra)


def bad_request(code: str, message: str, **extra: Any) -> ApiError:
    return ApiError(400, code, message, **extra)


def rate_limited(retry_after_seconds: float) -> ApiError:
    return ApiError(
        429,
        "RATE_LIMITED",
        "too many requests; slow down",
        retry_after_seconds=round(retry_after_seconds, 1),
    )
