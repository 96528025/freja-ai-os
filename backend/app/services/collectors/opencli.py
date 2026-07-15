import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from app.core.config import Settings


class OpenCLIClient:
    """Small read-only boundary around the local OpenCLI browser bridge."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.command = Path(settings.opencli_path).expanduser()

    def is_ready(self) -> bool:
        if not self.command.is_file():
            return False
        try:
            response = httpx.get(
                self.settings.opencli_status_url,
                headers={"X-OpenCLI": "1"},
                timeout=0.5,
            )
            response.raise_for_status()
            return bool(response.json().get("extensionConnected"))
        except (httpx.HTTPError, ValueError):
            return False

    async def read(self, site: str, action: str, *args: str) -> list[dict[str, Any]]:
        if not self.command.is_file():
            raise RuntimeError(f"OpenCLI is not installed at {self.command}")
        process = await asyncio.create_subprocess_exec(
            str(self.command),
            site,
            action,
            *args,
            "--format",
            "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
        except TimeoutError:
            process.kill()
            await process.wait()
            raise RuntimeError(f"OpenCLI {site}/{action} timed out") from None
        if process.returncode != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(detail or f"OpenCLI {site}/{action} failed")
        try:
            payload = json.loads(stdout.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise RuntimeError(f"OpenCLI {site}/{action} returned invalid JSON") from error
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("items", []))
        if not isinstance(payload, list):
            raise RuntimeError(f"OpenCLI {site}/{action} returned an unexpected shape")
        return [item for item in payload if isinstance(item, dict)]


def metric(value: object) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    raw = str(value or "0").strip().lower().replace(",", "")
    multipliers = {"k": 1_000, "m": 1_000_000, "万": 10_000, "千": 1_000}
    for suffix, multiplier in multipliers.items():
        if raw.endswith(suffix):
            try:
                return int(float(raw.removesuffix(suffix)) * multiplier)
            except ValueError:
                return 0
    try:
        return int(float(raw))
    except ValueError:
        return 0
