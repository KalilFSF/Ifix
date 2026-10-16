# Rotas do módulo "usuarios": autenticação, cadastro (cliente/técnico),
# perfil próprio, listagem de técnicos, perfil técnico e conversão
# cliente -> técnico. Só declara endpoint + auth/autorização de sessão e
# encaminha pro Controller — nenhuma regra de negócio aqui.

from flask import Blueprint
from flask_login import login_required

from modules.usuarios.controllers.auth_controller import AuthController
from modules.usuarios.controllers.diretorio_tecnicos_controller import DiretorioTecnicosController
from modules.usuarios.controllers.disponibilidade_controller import DisponibilidadeController
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


@usuarios_bp.route("/api/me/horario-atendimento", methods=["PUT"])
@login_required
def api_horario_atendimento():
    # PUT: a faixa de horário é um recurso único do usuário e reenviar o
    # mesmo par de horários tem o mesmo efeito (idempotente).
    return UsuarioController().definir_horario_atendimento()


@usuarios_bp.route("/api/me/foto", methods=["PUT"])
@login_required
def api_definir_foto_perfil():
    return UsuarioController().definir_foto_perfil()


@usuarios_bp.route("/api/me/senha", methods=["POST"])
@login_required
def api_alterar_senha():
    return UsuarioController().alterar_senha()


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


# Diretório e perfil público de técnicos (funcionalidades 4 e 5): leitura
# aberta a qualquer usuário autenticado, mas só com dados públicos.
@usuarios_bp.route("/api/tecnicos/diretorio", methods=["GET"])
@login_required
def api_diretorio_tecnicos():
    return DiretorioTecnicosController().listar()


@usuarios_bp.route("/api/tecnicos/<int:tecnico_id>/perfil-publico", methods=["GET"])
@login_required
def api_perfil_publico_tecnico(tecnico_id):
    return DiretorioTecnicosController().perfil_publico(tecnico_id)


# Disponibilidade do técnico (funcionalidades 3 e 6). PUT: as janelas são um
# conjunto único substituído por inteiro e "disponível agora" é um estado —
# reenviar o mesmo corpo tem o mesmo efeito (idempotente).
@usuarios_bp.route("/api/tecnico/disponibilidade", methods=["GET"])
@login_required
def api_obter_disponibilidade():
    return DisponibilidadeController().obter()


@usuarios_bp.route("/api/tecnico/disponibilidade", methods=["PUT"])
@login_required
def api_definir_disponibilidade():
    return DisponibilidadeController().definir_janelas()


@usuarios_bp.route("/api/tecnico/disponivel-agora", methods=["PUT"])
@login_required
def api_definir_disponivel_agora():
    return DisponibilidadeController().definir_disponivel_agora()
