from flask import jsonify, request
from flask_login import login_required, login_user, logout_user

from services.auth_service import AuthService
from models import Usuario


class AuthController:
    @staticmethod
    def login():
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = AuthService.autenticar(email, senha)
        if usuario is None:
            return jsonify({"ok": False, "erro": "Email ou senha inválidos."}), 401
        login_user(usuario)
        return jsonify({"ok": True, "redirect": f"/{usuario.role}/home"})

    @staticmethod
    @login_required
    def logout():
        logout_user()
        return jsonify({"ok": True, "redirect": "/"})
