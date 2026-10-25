import json
from dataclasses import dataclass
from typing import List
from pathlib import Path

@dataclass
class RouterConfig:
    ip: str
    user: str
    password: str

@dataclass
class AppConfig:
    routers: List[RouterConfig]
    rss_url: str
    verify_ssl: bool

def load_config(config_path: str = "app_config.json") -> AppConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier de configuration introuvable : {config_path}\n"
            f"Copiez app_config.example.json vers app_config.json "
            f"et remplissez vos valeurs."
        )

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    routers_data = data.get("routers", [])
    if not routers_data:
        raise ValueError("Aucun routeur défini dans le fichier de configuration.")

    routers = []
    for i, r in enumerate(routers_data, start=1):
        missing = [k for k in ("ip", "user", "password") if k not in r or not r[k]]
        if missing:
            raise ValueError(
                f"Routeur #{i} invalide : champs manquants {missing}. "
                f"Les champs 'ip', 'user' et 'password' sont requis."
            )
        routers.append(RouterConfig(
            ip=r["ip"],
            user=r["user"],
            password=r["password"]
        ))

    settings = data.get("settings", {})
    required_keys = ["rss_url", "verify_ssl"]
    missing = [k for k in required_keys if k not in settings]
    if missing:
        raise ValueError(
            f"Clés manquantes dans 'settings' : {missing}. "
            f"Consultez app_config.example.json pour le format attendu."
        )

    if not isinstance(settings["verify_ssl"], bool):
        raise ValueError("'verify_ssl' doit être un booléen (true/false).")

    return AppConfig(
        routers=routers,
        rss_url=settings["rss_url"],
        verify_ssl=settings["verify_ssl"]
    )