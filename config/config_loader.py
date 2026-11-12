import json

from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class RouterConfig:
    name: str
    ip: str
    user: str
    password: str
    verify_ssl: bool
    download_timeout: int
    reboot_timeout: int


@dataclass
class AppConfig:
    routers: List[RouterConfig]
    rss_url: str


def config_load(config_path: str = "app_config.json") -> AppConfig:
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
        missing = [
            k for k in ("name", "ip", "user", "password", "verify_ssl",
                        "download_timeout", "reboot_timeout")
            if k not in r or r[k] in (None, "")
        ]
        if missing:
            raise ValueError(
                f"Routeur #{i} invalide : champs manquants {missing}."
            )

        if not isinstance(r["verify_ssl"], bool):
            raise ValueError(
                f"Routeur #{i} : 'verify_ssl' doit être un booléen (true/false)."
            )

        if not isinstance(r["download_timeout"], int) or isinstance(r["download_timeout"], bool):
            raise ValueError(
                f"Routeur #{i} : 'download_timeout' doit être un entier."
            )
        if r["download_timeout"] < 60:
            raise ValueError(
                f"Routeur #{i} : 'download_timeout' doit être >= 60 secondes."
            )

        if not isinstance(r["reboot_timeout"], int) or isinstance(r["reboot_timeout"], bool):
            raise ValueError(
                f"Routeur #{i} : 'reboot_timeout' doit être un entier."
            )
        if r["reboot_timeout"] < 60:
            raise ValueError(
                f"Routeur #{i} : 'reboot_timeout' doit être >= 60 secondes."
            )
        valeur = r["ip"]
        if not isinstance(valeur, str):
            raise ValueError(
                f"Routeur #{i} : 'ip' doit être une chaîne de caractères."
            )
        if valeur != valeur.strip():
            raise ValueError(
                f"Routeur #{i} : 'ip' ne doit pas commencer ou finir par un espace."
            )
        if " " in valeur:
            raise ValueError(
                f"Routeur #{i} : 'ip' ne doit pas contenir d'espaces."
            )
        routers.append(RouterConfig(
            name=r["name"],
            ip=r["ip"],
            user=r["user"],
            password=r["password"],
            verify_ssl=r["verify_ssl"],
            download_timeout=r["download_timeout"],
            reboot_timeout=r["reboot_timeout"],
        ))

    settings = data.get("settings", {})
    if "rss_url" not in settings or not settings["rss_url"]:
        raise ValueError(
            "Clé manquante dans 'settings' : 'rss_url'. "
            "Consultez app_config.example.json pour le format attendu."
        )

    return AppConfig(
        routers=routers,
        rss_url=settings["rss_url"],
    )