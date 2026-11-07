import keyring

SERVICE = "linkedin-workbench"
USERNAME = "ai_api_key"


def get_api_key() -> str:
    try:
        return keyring.get_password(SERVICE, USERNAME) or ""
    except Exception:
        return ""


def set_api_key(key: str) -> None:
    if key:
        keyring.set_password(SERVICE, USERNAME, key)
    else:
        try:
            keyring.delete_password(SERVICE, USERNAME)
        except Exception:
            pass
