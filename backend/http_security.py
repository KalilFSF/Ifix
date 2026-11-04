"""Proteção CSRF, isolamento da sessão e cabeçalhos HTTP."""
import hmac
import secrets
from flask import current_app,jsonify,request,session,g
from werkzeug.exceptions import Forbidden

SAFE = {"GET","HEAD","OPTIONS"}
BINDING_KEY = "_ifix_session_version"


def session_scope():
    return current_app.config.get("SESSION_SCOPE","local-mysql-v3")


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def login_session():
    session.clear()
    session[BINDING_KEY] = session_scope()
    csrf_token()



def install_security(app):
    @app.before_request
    def protect_request():
        g.pop("_login_user",None)
        # Antes que Flask-Login carregue um ID de usuário de outro banco/ambiente.
        if session.get("_user_id") is not None and session.get(BINDING_KEY) != session_scope():
            session.clear()
        if request.method in SAFE:
            return
        api = request.path.startswith("/api/")
        if not api and request.path != "/logout":
            return
        if app.config.get("CSRF_ENABLED",True):
            supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token","")
            expected = session.get("_csrf")
            if not isinstance(supplied,str) or not expected or not hmac.compare_digest(expected,supplied):
                raise Forbidden("Token de segurança ausente ou inválido. Atualize a página.")
            origin = request.headers.get("Origin")
            expected_origin = ("https://"+request.host) if app.config.get("ON_VERCEL") else request.host_url.rstrip("/")
            if origin and origin.rstrip("/") != expected_origin:
                raise Forbidden("Origem da requisição não autorizada.")

    @app.get("/api/csrf")
    def api_csrf():
        response = jsonify(csrf_token=csrf_token(),max_request_bytes=app.config["MAX_CONTENT_LENGTH"])
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.after_request
    def secure_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        if request.path.startswith("/api/") or request.path == "/logout" or "Set-Cookie" in response.headers:
            response.headers["Cache-Control"] = "no-store"
        if app.config.get("ON_VERCEL"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
