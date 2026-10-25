import time
import logging
from typing import Optional
from contextlib import ExitStack
from .mikrotik_client import MikrotikClient
from .mikrotik_routeros import parse_routeros_rss
from config.config_loader import AppConfig, RouterConfig

logger = logging.getLogger(__name__)

class MikroTikUpdater:
    def __init__(self, router: RouterConfig, config: AppConfig, desired_version: str, desired_channel: str):
        self.router = router
        self.config = config
        self.desired_version = desired_version
        self.desired_channel = desired_channel
        self.client: Optional[MikrotikClient] = None

    def _create_client(self) -> MikrotikClient:
        return MikrotikClient(
            ip=self.router.ip,
            username=self.router.user,
            password=self.router.password,
            verify_ssl=self.config.verify_ssl
        )

    def _wait_for_reboot(self) -> bool:
        logger.info(f"-> Attendre que le routeur redémarre")
        time.sleep(60)     #60 secondes    
        for i in range(10): #100 secondes
            time.sleep(10)
            client = MikrotikClient(
                ip=self.router.ip,
                username=self.router.user,
                password=self.router.password,
                verify_ssl=self.config.verify_ssl,
            )
            try:
                if client.is_alive():
                    self.client = client
                    return True
            except Exception:
                pass
            finally:
                client.close()            
        logger.error(f"-> Timeout au redémarrage du routeur")
        return False 

    def _sync_channel(self) -> None:
        current_channel = self.client.get_update_channel()
        if current_channel != self.desired_channel:
            self.client.set_update_channel(self.desired_channel)

    def _update_routeros(self) -> bool: 
        self._sync_channel()
        routeros_current_version = self.client.get_routeros()     
        routeros_new_version = self.desired_version
        if routeros_current_version == routeros_new_version:
            logger.info(f"-> RouterOS est à jour")
            return False

        logger.info(f"-> RouterOS: {routeros_current_version} -> {routeros_new_version}")
        self.client.download_update()
        logger.info(f"-> Téléchargement de routerOS")
        for i in range(10):  # 10 * s = 100s
            time.sleep(10)
            status = self.client.get_update_status()
            status_text = status.get("status", "")
            if "please reboot" in status_text.lower():
                break
        else:
            logger.warning(f"-> Téléchargement non terminé après 90s")
            return False
        self.client.reboot() # Redémarrage pour installer
        if not self._wait_for_reboot():
            raise RuntimeError(f"-> Échec du redémarrage")
        if self.client.get_routeros() == self.desired_version:
            logger.info(f"-> RouterOS est à jour")
        else:
            logger.warning(f"-> RouterOS n'est pas à jour")        
        return True

    def _update_routerboard(self) -> bool:
        routerboard = self.client.get_routerboard()
        routerboard_new_version = routerboard.get("upgrade-firmware")
        routerboard_current_version = routerboard.get("current-firmware", "?")        
        if not routerboard_new_version or routerboard_new_version == routerboard_current_version:
            logger.info(f"-> RouterBOARD est à jour")
            return False

        logger.info(f"-> RouterBOARD: {routerboard_current_version} -> {routerboard_new_version}")
        self.client.upgrade_routerboard()
        self.client.reboot()
        if not self._wait_for_reboot():
            raise RuntimeError(f"-> Échec du redémarrage")
        routerboard = self.client.get_routerboard()
        if routerboard_new_version == routerboard.get("current-firmware", "?"):
            logger.info(f"-> RouterBOARD est à jour")
        else:
            logger.warning(f"-> RouterBOARD n'est pas à jour")
        return True

    def run(self) -> None:
        logger.info(f"")
        logger.info(f"Mise à jour de: {self.router.ip}")
        with ExitStack() as stack:
            self.client = stack.enter_context(self._create_client()) 
            if self._update_routeros():
                self.client = stack.enter_context(self._create_client())
            self._update_routerboard()

def update_all_mikrotik(config: AppConfig) -> None:
    try:
        rss_info = parse_routeros_rss(config.rss_url)
        desired_version = rss_info["version"]
        desired_channel = rss_info["channel"]
        logger.info(f"RouterOS à déployer: {desired_version} (Channel: {desired_channel})")
    except RuntimeError as e:
        logger.error(f"Impossible de lire le flux RSS: {e}")
        return

    for router in config.routers:
        updater = MikroTikUpdater(
            router, config,
            desired_version=desired_version,
            desired_channel=desired_channel,
        )
        try:
            updater.run()
        except Exception as e:
            if "timed out" in str(e).lower():
                logger.error(f"[{router.ip}] ERREUR: Le routeur ne répond pas (timeout)")
            elif "connection refused" in str(e).lower():
                logger.error(f"[{router.ip}] ERREUR: Connexion refusée. Vérifiez que www-ssl est activé")
            else:
                logger.error(f"[{router.ip}] ERREUR: {e}")
            continue