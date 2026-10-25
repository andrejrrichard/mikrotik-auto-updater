import requests
import urllib3
from typing import Optional, Dict, Any

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MikrotikClient:
    def __init__(
        self,
        ip: str,
        username: str,
        password: str,
        verify_ssl: bool
    ):
        self.ip = ip
        self.base_url = f"https://{ip}/rest"
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = verify_ssl

    def _get(self, endpoint: str) -> Any:
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, timeout=5)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data, timeout=5)
        response.raise_for_status()
        return response.json() if response.content else None

    def _execute(self, script: str) -> Any:
        return self._post("/execute", {"script": script})
    
    def get_update_channel(self) -> str:
        status = self._get("/system/package/update")
        return status.get("channel", "stable")

    def set_update_channel(self, channel: str) -> None:
        self._execute(f"/system/package/update/set channel={channel}")

    def get_routeros(self) -> str:
        status = self._get("/system/package/update")
        return status.get("installed-version", "inconnue")

    def get_routerboard(self) -> Dict:
        return self._get("/system/routerboard")

    def download_update(self) -> None:
        self._post("/system/package/update/download", {"once": ""})

    def get_update_status(self) -> Dict:
        return self._get("/system/package/update")

    def upgrade_routerboard(self) -> None:
        self._execute("/system/routerboard/upgrade")

    def reboot(self) -> None:
        self._execute("/system/reboot")

    def is_alive(self) -> bool:
        try:
            data = self._get("/system/resource")
            # Vérifier que c'est un dictionnaire non vide avec au moins un champ
            if isinstance(data, dict) and "version" in data:
                return True
            return False
        except requests.RequestException:
            return False

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()