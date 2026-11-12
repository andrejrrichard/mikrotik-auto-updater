import sys
import asyncio
import logging

from config.config_loader import config_load
from src.get_routeros_version import get_routeros_version_from_rss
from src.mikrotik_client import MikrotikClient


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def update(routers):
    await asyncio.gather(
        *(r.get_routeros() for r in routers),
        return_exceptions=True,
    )
    
    await asyncio.gather(
        *(r.update() for r in routers),
        return_exceptions=True,
    )


def main() -> int:
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        config = config_load()
        rss = get_routeros_version_from_rss(config.rss_url)

        logger.info("=== MAJ MikroTik ===")
        routers = [
            MikrotikClient(
                name=r.name,
                ip=r.ip,
                username=r.user,
                password=r.password,
                verify_ssl=r.verify_ssl,
                download_timeout=r.download_timeout,
                reboot_timeout=r.reboot_timeout,
                desired_version=rss["version"],
                desired_channel=rss["channel"],
            )
            for r in config.routers
        ]

        asyncio.run(update(routers))
        
        for r in routers:
            logger.info(f"{r.get_name()}: {r.get_ip()}: {r.get_status()}")            
        return 0

    except FileNotFoundError as e:
        logger.error(f"Config manquante : {e}")
        return 1

    except ValueError as e:
        logger.error(f"Config invalide : {e}")
        return 1

    except KeyboardInterrupt:
        logger.warning("Interruption utilisateur")
        return 130

    except Exception as e:
        logger.exception(f"Erreur inattendue : {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())