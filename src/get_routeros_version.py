import re
import requests
import xml.etree.ElementTree as ET

from typing import Dict


def get_routeros_version_from_rss(rss_url: str, timeout: int = 10) -> Dict[str, str]:
    try:
        response = requests.get(rss_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Impossible de contacter le flux RSS : {e}")

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        raise RuntimeError(f"Flux RSS mal formaté : {e}")

    # Cherche le premier <item><title>RouterOS X.Y.Z [channel]</title></item>
    for item in root.iter("item"):
        title = item.findtext("title", "")
        match = re.search(r"RouterOS\s+([\w.]+)\s+\[([\w-]+)\]", title, re.IGNORECASE)
        if match:
            return {
                "version": match.group(1),
                "channel": match.group(2),
            }

    raise RuntimeError(f"Version introuvable dans le flux RSS : {rss_url}")