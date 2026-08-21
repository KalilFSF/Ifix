from flask import jsonify, request
from flask_login import login_user

from exceptions import DominioError
from modules.usuarios.services.autenticar_usuario_service import AutenticarUsuarioService


class AuthController:
    """Login via /api/login. O logout é só navegação de página (link comum
    <a href="/logout">) e fica em page_routes.py — não é um caso de uso de
    negócio, é encerrar a sessão do Flask-Login e redirecionar."""

    def __init__(self):
        self.autenticar_usuario_service = AutenticarUsuarioService()

    def login(self):
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        try:
            usuario = self.autenticar_usuario_service.executar(email, senha)
        except DominioError as erro:
            return jsonify(ok=False, erro=erro.mensagem, **erro.extra), erro.status_code

        login_user(usuario)
        return jsonify({"ok": True, "redirect": f"/{usuario.role}/home"})
