import logging
from ldap3 import ALL, Connection, Server
from config import LDAP_SERVER, LDAP_DOMAIN

logger = logging.getLogger("bwiki.auth")


def check_ldap_login(username: str, password: str) -> bool:
    """
    Prueft Benutzername/Passwort gegen den LDAP-Server.
    
    Args:
        username: LDAP Benutzername (ohne Domain)
        password: LDAP Passwort
        
    Returns:
        True wenn Login erfolgreich, False sonst
    """
    try:
        server = Server(LDAP_SERVER, get_info=ALL)
        user_dn = f"{username}@{LDAP_DOMAIN}"
        
        # auto_bind=True führt den Login direkt beim Erstellen der Connection aus
        conn = Connection(server, user=user_dn, password=password, auto_bind=True)
        logger.info(f"✅ Login ERFOLGREICH für User: {username}")
        conn.unbind()
        return True
        
    except Exception as e:
        logger.warning(f"❌ Login FEHLGESCHLAGEN für {username}. Grund: {e}")
        return False