import os

try:
    from ldap3 import ALL, Connection, Server
except ImportError:
    ALL = None
    Connection = None
    Server = None


LDAP_SERVER_HOST = os.environ.get("LDAP_SERVER", "CCCDC01.ccc.ccofc.edu")
LDAP_PORT = int(os.environ.get("LDAP_PORT", "389"))
LDAP_DOMAIN = os.environ.get("LDAP_DOMAIN", "ccc.ccofc.edu")
LDAP_USE_SSL = os.environ.get("LDAP_USE_SSL", "0").strip() == "1"
LDAP_REQUIRED_GROUP_DN = os.environ.get(
    "LDAP_REQUIRED_GROUP_DN",
    "CN=CCA_Leslie_Project,OU=CCA_Groups_Security_User,OU=CCA,DC=ccc,DC=ccofc,DC=edu",
)
ALLOW_DEV_LOGIN = os.environ.get("ALLOW_DEV_LOGIN", "0").strip() == "1"

# TEMPORARY dev-only fallback credentials. Default disabled unless ALLOW_DEV_LOGIN=1.
TEMP_LOGIN_USERNAME = "admin"
TEMP_LOGIN_PASSWORD = "test123"


def ldap_search_base_dn():
    """
    Derive a search base from the required group DN or LDAP domain.
    """
    dc_parts = [part for part in LDAP_REQUIRED_GROUP_DN.split(",") if part.startswith("DC=")]
    if dc_parts:
        return ",".join(dc_parts)
    return ",".join(f"DC={part}" for part in LDAP_DOMAIN.split(".") if part)


def escape_ldap_filter_value(value):
    """
    Escape special characters in LDAP filter values.
    """
    escaped = value.replace("\\", "\\5c")
    escaped = escaped.replace("*", "\\2a")
    escaped = escaped.replace("(", "\\28")
    escaped = escaped.replace(")", "\\29")
    escaped = escaped.replace("\x00", "\\00")
    return escaped


def authenticate_with_ldap(username, password):
    """
    Authenticate against AD/LDAP and require direct membership in the configured group.
    """
    if not username or not password:
        return False, "Enter your username and password."

    if Server is None or Connection is None:
        return False, "LDAP authentication is unavailable because ldap3 is not installed."

    user_principal_name = f"{username}@{LDAP_DOMAIN}"
    search_base = ldap_search_base_dn()
    safe_username = escape_ldap_filter_value(username)
    safe_upn = escape_ldap_filter_value(user_principal_name)
    safe_group_dn = escape_ldap_filter_value(LDAP_REQUIRED_GROUP_DN)
    search_filter = (
        "(&"
        "(objectClass=user)"
        f"(|(sAMAccountName={safe_username})(userPrincipalName={safe_upn}))"
        f"(memberOf={safe_group_dn})"
        ")"
    )

    try:
        server = Server(LDAP_SERVER_HOST, port=LDAP_PORT, use_ssl=LDAP_USE_SSL, get_info=ALL)
        with Connection(server, user=user_principal_name, password=password, auto_bind=True) as conn:
            found = conn.search(search_base=search_base, search_filter=search_filter, attributes=["cn"])
            if found and conn.entries:
                return True, None
            return False, "You are not authorized to access this assistant."
    except Exception:
        return False, "Sign-in failed. Check your credentials or contact IT if the issue continues."
