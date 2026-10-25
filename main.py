#Point d'entrée du script de mise à jour des routeurs MikroTik.

import sys
import logging
from config.config_loader import load_config
from src.updater import update_all_mikrotik

def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

def main() -> int:
    setup_logging()
    logger = logging.getLogger(__name__)
    try:
        config = load_config()
        logger.info(f"")
        logger.info(f"{len(config.routers)} routeur(s) MikroTik à mettre à jour")
        update_all_mikrotik(config)
        return 0

    except FileNotFoundError as e:
        logger.error(f"Fichier de configuration manquant : {e}")
        return 1
    except ValueError as e:
        logger.error(f"Erreur de configuration : {e}")
        return 1
    except KeyboardInterrupt:
        logger.warning("Interruption par l'utilisateur.")
        return 130
    except Exception as e:
        logger.exception(f"Erreur inattendue : {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())