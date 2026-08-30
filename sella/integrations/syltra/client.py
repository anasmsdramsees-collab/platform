"""The platform, as SELLA sees it.

SELLA does not talk to Home Assistant. It talks to the SYLTRA API, which then
talks to Home Assistant through the Edge Agent. Everything the specification
asks for in §16 already stands on that path: the policy chain decides, the
orchestrator verifies, the audit trail records, and a life safety actuator is
refused outside production.

Going straight to Home Assistant would be two fewer network hops and a hole
through the middle of the product.
"""

from typing import Any, Protocol

import httpx

from sella_core.errors import ProviderError


class SyltraClient(Protocol):
    async def devices(self) -> list[dict[str, Any]]: ...
    async def rooms(self) -> list[dict[str, Any]]: ...
    async def scenes(self) -> list[dict[str, Any]]: ...
    async def risks(self) -> dict[str, Any]: ...
    async def energy(self) -> dict[str, Any]: ...
    async def set_capability(
        self, device_id: str, capability: str, value: Any
    ) -> dict[str, Any]: ...
    async def activate_scene(self, scene_id: str) -> dict[str, Any]: ...


class HttpSyltraClient:
    def __init__(self, base_url: str, token: str, home_id: str, timeout: float = 10.0) -> None:
        self._base = base_url.rstrip("/")
        self._home = home_id
        self._client = httpx.AsyncClient(
            base_url=self._base,
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}", "Accept-Language": "ar"},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str) -> Any:
        try:
            response = await self._client.get(f"/v1/homes/{self._home}{path}?locale=ar")
        except httpx.HTTPError as exc:
            raise ProviderError(
                code="HUB_UNREACHABLE",
                detail=str(exc),
                spoken="ما قدرت أوصل للهَب.",
            ) from exc
        if response.status_code >= 400:
            raise ProviderError(
                code=f"HUB_{response.status_code}",
                detail=response.text[:300],
                spoken="الهَب رفض الطلب.",
            )
        return response.json()

    async def devices(self) -> list[dict[str, Any]]:
        payload = await self._get("/devices?limit=200")
        return list(payload.get("items", []))

    async def rooms(self) -> list[dict[str, Any]]:
        return list((await self._get("/rooms")).get("rooms", []))

    async def scenes(self) -> list[dict[str, Any]]:
        return list((await self._get("/scenes")).get("items", []))

    async def risks(self) -> dict[str, Any]:
        return dict(await self._get("/risks"))

    async def energy(self) -> dict[str, Any]:
        return dict(await self._get("/energy/history?resolution=hour"))

    async def set_capability(self, device_id: str, capability: str, value: Any) -> dict[str, Any]:
        try:
            response = await self._client.post(
                f"/v1/homes/{self._home}/devices/{device_id}/{capability}?locale=ar",
                json={"value": value},
            )
        except httpx.HTTPError as exc:
            raise ProviderError(
                code="HUB_UNREACHABLE", detail=str(exc), spoken="ما قدرت أوصل للهَب."
            ) from exc
        body = response.json() if response.content else {}
        if response.status_code >= 400:
            raise ProviderError(
                code=str(body.get("detail", {}).get("error", f"HUB_{response.status_code}")),
                detail=str(body)[:300],
                spoken=str(body.get("detail", {}).get("message", "الطلب ما نفّذ.")),
            )
        return dict(body)

    async def activate_scene(self, scene_id: str) -> dict[str, Any]:
        response = await self._client.post(
            f"/v1/homes/{self._home}/scenes/{scene_id}/activate?locale=ar"
        )
        body = response.json() if response.content else {}
        if response.status_code >= 400:
            raise ProviderError(
                code=f"HUB_{response.status_code}",
                detail=str(body)[:300],
                spoken="السيناريو ما اشتغل.",
            )
        return dict(body)
