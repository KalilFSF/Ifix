# Rotas do módulo "usuarios": autenticação, cadastro (cliente/técnico),
# perfil próprio, listagem de técnicos, perfil técnico e conversão
# cliente -> técnico. Só declara endpoint + auth/autorização de sessão e
# encaminha pro Controller — nenhuma regra de negócio aqui.

from flask import Blueprint
from flask_login import login_required

from modules.usuarios.controllers.auth_controller import AuthController
from modules.usuarios.controllers.perfil_tecnico_controller import PerfilTecnicoController
from modules.usuarios.controllers.usuario_controller import UsuarioController

usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/api/login", methods=["POST"])
def api_login():
    return AuthController().login()


@usuarios_bp.route("/api/cadastro/cliente", methods=["POST"])
def api_cadastro_cliente():
    return UsuarioController().cadastrar_cliente()


@usuarios_bp.route("/api/cadastro/tecnico", methods=["POST"])
def api_cadastro_tecnico():
    return UsuarioController().cadastrar_tecnico()


@usuarios_bp.route("/api/me", methods=["GET"])
@login_required
def api_me():
    return UsuarioController().me()


@usuarios_bp.route("/api/me", methods=["PATCH"])
@login_required
def api_atualizar_me():
    return UsuarioController().atualizar_me()


@usuarios_bp.route("/api/tecnicos", methods=["GET"])
@login_required
def api_tecnicos():
    return UsuarioController().listar_tecnicos()


@usuarios_bp.route("/api/conta/tornar-tecnico", methods=["POST"])
@login_required
def api_conta_tornar_tecnico():
    return UsuarioController().tornar_tecnico()


@usuarios_bp.route("/api/tecnico/perfil", methods=["GET"])
@login_required
def api_perfil_tecnico():
    return PerfilTecnicoController().obter()


@usuarios_bp.route("/api/tecnico/perfil", methods=["PATCH"])
@login_required
def api_atualizar_perfil_tecnico():
    return PerfilTecnicoController().atualizar()
