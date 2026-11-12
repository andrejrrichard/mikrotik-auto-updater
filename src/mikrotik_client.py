import asyncio
import aiohttp

from datetime import datetime
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Result:
    value: Optional[Any]
    success: bool


class MikrotikClient:
    def __init__(self, name, ip, username, password, verify_ssl,
            download_timeout, reboot_timeout,
            desired_version, desired_channel):
        self._name = name
        self._ip = ip
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._desired_version = desired_version
        self._desired_channel = desired_channel
        self._download_timeout = download_timeout
        self._reboot_timeout = reboot_timeout
        self._base_url = f"https://{ip}/rest"
        self._status = "UNKNOWN"

    def _session(self):
        return aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self._username, self._password),
            connector=aiohttp.TCPConnector(ssl=self._verify_ssl),
            timeout=aiohttp.ClientTimeout(total=30),
        )


    async def _get(self, session, endpoint):
        async with session.get(f"{self._base_url}{endpoint}") as r:
            r.raise_for_status()
            return await r.json()


    async def _post(self, session, endpoint, data=None):
        headers = {"Content-Type": "application/json"}
        async with session.post(f"{self._base_url}{endpoint}", json=data, headers=headers) as r:
            r.raise_for_status()
            return await r.json() if r.content_length else None


    async def _execute(self, session, script):
        return await self._post(session, "/execute", {"script": script})


    async def _request(self, request) -> Result:
        try:
            return Result(await request, True)
        except Exception as e:
            self._status = "OFFLINE"
            return Result(None, False)


    async def _reboot(self, session):
        if not (await self._request(
            self._execute(session, "/system/reboot")
        )).success:
            return False
        await asyncio.sleep(15)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._reboot_timeout
        while loop.time() < deadline:
            try:
                await self._get(session, "/system/resource")
                await asyncio.sleep(15)
                return True
            except Exception:
                await asyncio.sleep(10)
        self._status = "REBOOT_TIMEOUT"
        return False


    async def _is_routeros_updated(self, session) -> bool:
        result = await self._request(
            self._get(session, "/system/package/update")
        )
        if not result.success:
            return False
        update = result.value

        channel = update.get("channel")
        if channel != self._desired_channel:
            if not (await self._request(
                self._execute(
                    session,
                    f"/system/package/update/set channel={self._desired_channel}",
                )
            )).success:
                return False
            result = await self._request(
                self._get(session, "/system/package/update")
            )
            if not result.success:
                return False
            update = result.value

        return update.get("installed-version", "?") == self._desired_version


    async def _download_routeros(self, session):
        if await self._is_routeros_updated(session):
            self._status = "ROUTEROS_UPDATED"
            return
        if self._status == "OFFLINE":
            return

        if not (await self._request(
            self._post(session, "/system/package/update/download")
        )).success:
            return

        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._download_timeout
        while loop.time() < deadline:
            await asyncio.sleep(5)
            result = await self._request(
                self._get(session, "/system/package/update")
            )
            if not result.success:
                continue
            status = result.value.get("status", "").lower()
            if "please reboot" in status:
                self._status = "ROUTEROS_DOWNLOADED"
                return
            if "downloading" not in status and status != "":
                await self._request(
                    self._post(session, "/system/package/update/download")
                )
        self._status = "DOWNLOAD_TIMEOUT"


    async def _is_routerboard_updated(self, session) -> bool:
        for num_try in range(3):
            result = await self._request(
                self._get(session, "/system/routerboard")
            )
            if result.success:
                rb = result.value
                new = rb.get("upgrade-firmware")
                cur = rb.get("current-firmware", "?")
                return bool(new) and new == cur
            await asyncio.sleep(10)
        return False


    async def _update_routerboard(self, session):
        if await self._is_routerboard_updated(session):
            self._status = "UPGRADE_COMPLETE"
            return
        if self._status == "OFFLINE":
            return

        if not (await self._request(
            self._execute(session, "/system/routerboard/upgrade")
        )).success:
            return
        if not await self._reboot(session):
            return
        if await self._is_routerboard_updated(session):
            self._status = "UPGRADE_COMPLETE"
        elif self._status != "OFFLINE":
            self._status = "ROUTERBOARD_UPDATE_FAILED"


    async def _update_routeros(self, session):
        if self._status == "ROUTEROS_UPDATED":
            return True
        if self._status == "ROUTEROS_DOWNLOADED":
            if not await self._reboot(session):
                return False
            if await self._is_routeros_updated(session):
                self._status = "ROUTEROS_UPDATED"
                return True
            self._status = "ROUTEROS_UPDATED_FAILED"
        return False


    def get_name(self):
        return self._name


    def get_ip(self):
        return self._ip


    def get_status(self):
        return self._status


    async def get_routeros(self):
        try:
            async with self._session() as session:
                await self._download_routeros(session)
        except Exception:
            pass


    async def update(self):
        try:
            async with self._session() as session:
                if await self._update_routeros(session):
                    await self._update_routerboard(session)
        except Exception:
            pass