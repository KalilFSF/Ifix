# Rotas do módulo "servicos": chamados (Servico) e as solicitações feitas
# a técnicos específicos (SolicitacaoTecnico) — só declara endpoint +
# auth/autorização de sessão e encaminha pro Controller.

from flask import Blueprint
from flask_login import login_required

from modules.servicos.controllers.servico_controller import ServicoController
from modules.servicos.controllers.solicitacao_controller import SolicitacaoController

servicos_bp = Blueprint("servicos", __name__)


@servicos_bp.route("/api/servicos", methods=["GET"])
@login_required
def api_servicos():
    # Legado: alias autenticado e escopado de /api/servicos/meus (mesmo
    # filtro ?status= de antes). Antes não exigia login e devolvia os
    # chamados de todos os clientes — isso foi fechado.
    return ServicoController().meus()


@servicos_bp.route("/api/servicos/meus", methods=["GET"])
@login_required
def api_servicos_meus():
    return ServicoController().meus()


@servicos_bp.route("/api/servicos", methods=["POST"])
@login_required
def api_criar_servico():
    return ServicoController().criar()


@servicos_bp.route("/api/servicos/<int:servico_id>")
@login_required
def api_detalhes_servico(servico_id):
    return ServicoController().detalhes(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/aceitar", methods=["POST"])
@login_required
def api_aceitar_servico(servico_id):
    return ServicoController().atribuir_tecnico(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/status", methods=["PATCH"])
@login_required
def api_status_servico(servico_id):
    return ServicoController().atualizar_status(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/historico", methods=["GET"])
@login_required
def api_historico_servico(servico_id):
    return ServicoController().historico(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/solicitar-tecnicos", methods=["POST"])
@login_required
def api_solicitar_tecnicos(servico_id):
    return ServicoController().solicitar(servico_id)


@servicos_bp.route("/api/tecnico/solicitacoes", methods=["GET"])
@login_required
def api_tecnico_solicitacoes():
    return SolicitacaoController().listar()


@servicos_bp.route("/api/tecnico/solicitacoes/<int:solicitacao_id>/aceitar", methods=["POST"])
@login_required
def api_tecnico_solicitacao_aceitar(solicitacao_id):
    return SolicitacaoController().aceitar(solicitacao_id)


@servicos_bp.route("/api/tecnico/solicitacoes/<int:solicitacao_id>/recusar", methods=["POST"])
@login_required
def api_tecnico_solicitacao_recusar(solicitacao_id):
    return SolicitacaoController().recusar(solicitacao_id)
