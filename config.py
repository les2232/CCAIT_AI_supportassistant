import os
import sys


DEFAULT_FLASK_SECRET = "temporary-dev-session-secret-key"
LOGIN_RATE_LIMIT_ATTEMPTS_DEFAULT = 5
LOGIN_RATE_LIMIT_WINDOW_SECONDS_DEFAULT = 300
TRUE_ENV_VALUES = {"1", "true", "yes", "on"}


def env_flag(name, default="0"):
    return os.environ.get(name, default).strip().lower() in TRUE_ENV_VALUES


def local_only_mode_enabled():
    return env_flag("IT_SUPPORT_LOCAL_ONLY", "1")


def env_list(name):
    raw_value = os.environ.get(name, "")
    return {
        item.strip().lower()
        for item in raw_value.split(",")
        if item.strip()
    }


def env_flag_with_optional(name, default):
    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default
    return raw_value.strip().lower() in TRUE_ENV_VALUES


def env_int(name, default):
    raw_value = os.environ.get(name, "").strip()
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def flask_secret_key():
    return os.environ.get("FLASK_SECRET_KEY", DEFAULT_FLASK_SECRET)


def login_rate_limit_attempts():
    return max(0, env_int("LOGIN_RATE_LIMIT_ATTEMPTS", LOGIN_RATE_LIMIT_ATTEMPTS_DEFAULT))


def login_rate_limit_window_seconds():
    return max(1, env_int("LOGIN_RATE_LIMIT_WINDOW_SECONDS", LOGIN_RATE_LIMIT_WINDOW_SECONDS_DEFAULT))


def internal_kb_enabled():
    return env_flag("ENABLE_INTERNAL_KB")


def internal_kb_allowed_users():
    return env_list("INTERNAL_KB_ALLOWED_USERS")


def internal_kb_default_enabled():
    return env_flag("INTERNAL_KB_DEFAULT")


def current_runtime_mode():
    """
    Return a simple normalized runtime mode string.
    """
    return (
        os.environ.get("APP_ENV")
        or os.environ.get("FLASK_ENV")
        or os.environ.get("ENV")
        or "development"
    ).strip().lower()


def configure_session_security(flask_app):
    """
    Set conservative session-cookie defaults while keeping local development usable.
    """
    runtime_mode = current_runtime_mode()
    secure_default = runtime_mode == "production"
    flask_app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=os.environ.get("SESSION_COOKIE_SAMESITE", "Lax").strip() or "Lax",
        SESSION_COOKIE_SECURE=env_flag_with_optional("SESSION_COOKIE_SECURE", secure_default),
    )


def current_openai_api_key():
    return os.environ.get("OPENAI_API_KEY", "").strip()


def realtime_support_enabled():
    return env_flag("ENABLE_REALTIME_SUPPORT")


def build_realtime_session_payload():
    from realtime_tools import REALTIME_FUNCTION_TOOLS

    prompt_id = os.environ.get("OPENAI_REALTIME_PROMPT_ID", "").strip()
    if not prompt_id:
        raise RuntimeError("OPENAI_REALTIME_PROMPT_ID is not configured.")

    session_payload = {
        "session": {
            "type": "realtime",
            "model": os.environ.get("OPENAI_REALTIME_MODEL", "gpt-realtime").strip() or "gpt-realtime",
            "audio": {
                "input": {
                    "turn_detection": {
                        "type": "server_vad",
                    }
                },
                "output": {
                    "voice": os.environ.get("OPENAI_REALTIME_VOICE", "marin").strip() or "marin",
                },
            },
            "prompt": {
                "id": prompt_id,
            },
            "tool_choice": "auto",
            "tools": REALTIME_FUNCTION_TOOLS,
        }
    }
    return session_payload


def validate_startup_config():
    """
    Validate deployment-sensitive configuration.
    Local-only conflicts always fail fast.
    In production, fail fast on unsafe security settings.
    In non-production, print warnings only.
    """
    runtime_mode = current_runtime_mode()
    in_production = runtime_mode == "production"

    errors = []
    warnings = []

    if local_only_mode_enabled():
        if current_openai_api_key():
            errors.append(
                "IT_SUPPORT_LOCAL_ONLY=1 conflicts with OPENAI_API_KEY being set. "
                "Remove OPENAI_API_KEY for deterministic KB-only deployment, or set "
                "IT_SUPPORT_LOCAL_ONLY=0 only after explicit review."
            )

        local_only_conflict_flags = (
            "IT_SUPPORT_LLM_ENABLED",
            "IT_SUPPORT_CLASSIFIER_ENABLED",
            "ENABLE_AGENTS",
            "ENABLE_REALTIME_SUPPORT",
            "IT_SUPPORT_EMBEDDINGS_ENABLED",
        )
        for flag_name in local_only_conflict_flags:
            if env_flag(flag_name):
                errors.append(
                    f"IT_SUPPORT_LOCAL_ONLY=1 conflicts with {flag_name}=1. "
                    f"Disable {flag_name} for deterministic KB-only deployment, or set "
                    "IT_SUPPORT_LOCAL_ONLY=0 only after explicit review."
                )

    secret_key = os.environ.get("FLASK_SECRET_KEY", "").strip()
    if not secret_key:
        message = "FLASK_SECRET_KEY is not set."
        if in_production:
            errors.append(message)
        else:
            warnings.append(f"{message} Using a development fallback secret.")
    elif secret_key == DEFAULT_FLASK_SECRET:
        message = "FLASK_SECRET_KEY is using the default development fallback."
        if in_production:
            errors.append(message)
        else:
            warnings.append(message)

    if env_flag("ALLOW_DEV_LOGIN"):
        message = "ALLOW_DEV_LOGIN is enabled."
        if in_production:
            errors.append(f"{message} Disable dev login before deploying.")
        else:
            warnings.append(f"{message} This is only safe for local development.")

    if internal_kb_enabled() and not internal_kb_allowed_users():
        message = "ENABLE_INTERNAL_KB is enabled but INTERNAL_KB_ALLOWED_USERS is empty."
        if in_production:
            errors.append(message)
        else:
            warnings.append(f"{message} Internal KB notes will not be available to any user.")

    ldap_required_vars = (
        "LDAP_SERVER",
        "LDAP_PORT",
        "LDAP_DOMAIN",
        "LDAP_USE_SSL",
        "LDAP_REQUIRED_GROUP_DN",
    )
    missing_ldap_vars = [name for name in ldap_required_vars if not os.environ.get(name, "").strip()]
    if missing_ldap_vars:
        message = "LDAP settings are relying on defaults or are unset: " + ", ".join(missing_ldap_vars)
        if in_production:
            errors.append(message)
        else:
            warnings.append(message)

    ldap_use_ssl_raw = os.environ.get("LDAP_USE_SSL", "").strip()
    if ldap_use_ssl_raw and not env_flag("LDAP_USE_SSL"):
        message = "LDAP_USE_SSL must be set to 1 in production so LDAP binds use LDAPS."
        if in_production:
            errors.append(message)
        else:
            warnings.append(message)

    ldap_port_raw = os.environ.get("LDAP_PORT", "").strip()
    if ldap_port_raw:
        try:
            ldap_port = int(ldap_port_raw)
        except ValueError:
            message = "LDAP_PORT must be a valid integer."
            if in_production:
                errors.append(message)
            else:
                warnings.append(message)
        else:
            if ldap_port == 389:
                message = "LDAP_PORT=389 is cleartext LDAP. Use an LDAPS port such as 636 in production."
                if in_production:
                    errors.append(message)
                else:
                    warnings.append(message)

    if warnings:
        print("Startup configuration warnings", file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        for warning in warnings:
            print(f"- {warning}", file=sys.stderr)

    if errors:
        print("Startup configuration errors", file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise RuntimeError("Unsafe startup configuration. Review startup settings before deployment.")
