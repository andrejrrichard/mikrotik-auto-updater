import re
import requests
from typing import Dict

def parse_routeros_rss(rss_url: str, timeout: int = 2) -> Dict[str, str]:
    """
    Lit un flux RSS MikroTik et retourne la version et le channel.

    Returns:
        {"version": "7.24.5", "channel": "stable"}

    Raises:
        RuntimeError: Si le flux est inaccessible ou mal formaté.
    """
    try:
        response = requests.get(rss_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Impossible de contacter le flux RSS : {e}")

    match = re.search(
        r"<title>RouterOS\s+([\w.]+)\s+\[(\w[\w-]*)\]</title>",
        response.text
    )
    if not match:
        raise RuntimeError(f"Version introuvable dans le flux RSS : {rss_url}")

    return {
        "version": match.group(1),
        "channel": match.group(2)
    }