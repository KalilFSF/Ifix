"""Configuração por ambiente, sem .env e sem abrir conexões."""
import os
from pathlib import Path
from datetime import timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.engine import make_url
from mysql_tls import tls_context

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

class Config:
    @staticmethod
    def from_environment():
        secret = os.environ.get("SECRET_KEY")
        on_vercel = bool(os.environ.get("VERCEL"))
        environment = os.environ.get("VERCEL_ENV","local")
        if on_vercel and (not secret or len(secret) < 32 or secret == "dev-secret-key-troque-em-producao"):
            raise RuntimeError("Configure SECRET_KEY segura na Vercel.")
        url = make_url(os.environ["DATABASE_URL"])
        if url.drivername not in {"mysql", "mysql+pymysql"}:
            raise RuntimeError("DATABASE_URL deve usar mysql+pymysql://; não publique com a URL antiga.")
        # make_url decodifica percent-encoding uma vez; nunca concatenamos a senha.
        url = url.set(drivername="mysql+pymysql")
        expected_db = "ifix_test" if environment == "preview" else "ifix"
        if url.database != expected_db:
            raise RuntimeError(f"Este ambiente requer o banco {expected_db}.")
        if url.query:
            raise RuntimeError("Configure TLS por MYSQL_SSL_CA ou MYSQL_SSL_CA_PEM, sem parâmetros na URL.")
        timezone_name = os.environ.get("BUSINESS_TIMEZONE","America/Sao_Paulo")
        ZoneInfo(timezone_name) # Falhar na configuração inválida, não no meio do envio.
        scope = f"{environment}-mysql-v3"
        return {
            "SECRET_KEY": secret or "dev-secret-key-troque-em-producao",
            "SECRET_KEY_FALLBACKS": [],
            "SESSION_SCOPE": scope,
            "SESSION_COOKIE_NAME": ("__Host-ifix-" if on_vercel else "ifix-") + scope,
            "SESSION_COOKIE_DOMAIN": None,
            "REMEMBER_COOKIE_NAME": ("__Host-ifix-remember-" if on_vercel else "ifix-remember-")+scope,
            "REMEMBER_COOKIE_HTTPONLY": True,
            "REMEMBER_COOKIE_SECURE": on_vercel,
            "REMEMBER_COOKIE_SAMESITE": "Lax",
            "SESSION_COOKIE_PATH": "/",
            "PERMANENT_SESSION_LIFETIME": timedelta(hours=12),
            "CSRF_ENABLED": True,
            "BUSINESS_TIMEZONE": timezone_name,
            "ON_VERCEL": on_vercel,
            "TRUSTED_HOSTS": [host for host in (os.environ.get("VERCEL_URL"),os.environ.get("VERCEL_PROJECT_PRODUCTION_URL"),"ifix-main.vercel.app" if environment=="production" else None) if host] if on_vercel else None,
            "SQLALCHEMY_DATABASE_URI": url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "pool_pre_ping": True, "pool_recycle": 240,
                "pool_size": 2, "max_overflow": 0, "pool_timeout": 10,
                "connect_args": {
                    "ssl": tls_context(), "charset": "utf8mb4",
                    "connect_timeout": 10, "read_timeout": 20, "write_timeout": 20,
                    "init_command": "SET time_zone = '+00:00'",
                },
            },
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
            "SESSION_COOKIE_SECURE": bool(os.environ.get("VERCEL")),
            "UPLOAD_FOLDER": str(FRONTEND_DIR / "uploads"),
            "MAX_CONTENT_LENGTH": 4 * 1024 * 1024,
        }
