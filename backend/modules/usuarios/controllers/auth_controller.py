"""Controller HTTP: lê a requisição, chama os services de usuarios e devolve o contrato JSON da API."""
from flask import jsonify, request
from flask_login import login_user
from http_security import login_session

from exceptions import DominioError
from modules.usuarios.services.autenticar_usuario_service import AutenticarUsuarioService


class AuthController:
    """Autentica via /api/login e cria uma sessão nova antes do Flask-Login.

    Logout fica em page_routes.py: POST com CSRF encerra a sessão e redireciona.
    O link da interface é interceptado em api.js para realizar esse POST.
    """

    def __init__(self):
        self.autenticar_usuario_service = AutenticarUsuarioService()

    def login(self):
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        try:
            usuario = self.autenticar_usuario_service.executar(email, senha)
        except DominioError as erro:
            return jsonify(ok=False, erro=erro.mensagem, **erro.extra), erro.status_code

        login_session()
        login_user(usuario)
        return jsonify({"ok": True, "redirect": f"/{usuario.role}/home"})
