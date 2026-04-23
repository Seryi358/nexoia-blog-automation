"""WordPress authentication strategies.

Supports:
- `basic` (default): Basic Auth with WP Application Password
- `jwt`: JWT Authentication for WP-API plugin
  (https://wordpress.org/plugins/jwt-authentication-for-wp-rest-api/)

Hostinger's managed WP + Kadence plugins degrade Application Password capabilities
to read-only (confirmed 2026-04-23). JWT bypasses that filter because the token
is minted by the plugin and carries the real user caps.
"""
import asyncio
import base64

import httpx
from loguru import logger

from app.config import Settings


USER_AGENT = "IAPracticaBot/1.0 (+https://iapractica.co)"


class WPAuth:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.wp_url.rstrip("/")
        self.method = (getattr(settings, "wp_auth_method", "basic") or "basic").lower()
        self._jwt_token: str | None = None
        self._lock = asyncio.Lock()

    async def headers(self) -> dict:
        """Return the Authorization + Content-Type + UA headers for a REST call."""
        base = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }
        if self.method == "jwt":
            token = await self._get_jwt()
            return {**base, "Authorization": f"Bearer {token}"}

        creds = f"{self.settings.wp_user}:{self.settings.wp_app_password}"
        encoded = base64.b64encode(creds.encode()).decode()
        return {**base, "Authorization": f"Basic {encoded}"}

    async def auth_only_header(self) -> dict:
        """Return just {Authorization: ...} for cases where the caller sets Content-Type manually."""
        h = await self.headers()
        return {"Authorization": h["Authorization"], "User-Agent": USER_AGENT}

    async def _get_jwt(self) -> str:
        if self._jwt_token:
            return self._jwt_token

        async with self._lock:
            if self._jwt_token:  # re-check after lock
                return self._jwt_token

            # JWT plugin needs the user's LOGIN password, not the App Password.
            # We fall back to wp_app_password if wp_password is empty to keep
            # single-env-var setups working; users on JWT mode should set
            # WP_PASSWORD explicitly.
            pw = (getattr(self.settings, "wp_password", "") or self.settings.wp_app_password)
            if not pw:
                raise RuntimeError("WP_PASSWORD (or WP_APP_PASSWORD) required for JWT auth")

            url = f"{self.base_url}/wp-json/jwt-auth/v1/token"
            payload = {"username": self.settings.wp_user, "password": pw}

            async with httpx.AsyncClient(timeout=25) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"JWT auth failed {resp.status_code}: {resp.text[:400]}"
                    )
                data = resp.json()
                token = (
                    data.get("token")
                    or (data.get("data") or {}).get("token")
                )
                if not token:
                    raise RuntimeError(f"JWT response missing token: {data}")

            self._jwt_token = token
            logger.info("JWT token acquired from plugin")
            return token

    def invalidate(self) -> None:
        """Clear cached JWT token so the next call re-authenticates."""
        self._jwt_token = None
