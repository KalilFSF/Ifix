# Rotas do módulo "atendimentos" (orçamentos/registros de atendimento
# ligados a um Servico) — só declara endpoint + auth e encaminha pro
# Controller.

from flask import Blueprint
from flask_login import login_required

from modules.atendimentos.controllers.atendimento_controller import AtendimentoController

atendimentos_bp = Blueprint("atendimentos", __name__)


@atendimentos_bp.route("/api/atendimentos", methods=["GET"])
@login_required
def api_atendimentos():
    return AtendimentoController().listar()


@atendimentos_bp.route("/api/servicos/<int:servico_id>/atendimentos", methods=["POST"])
@login_required
def api_criar_atendimento(servico_id):
    return AtendimentoController().criar(servico_id)


@atendimentos_bp.route("/api/atendimentos/<int:atendimento_id>/status", methods=["PATCH"])
@login_required
def api_status_atendimento(atendimento_id):
    return AtendimentoController().atualizar_status(atendimento_id)


@atendimentos_bp.route("/api/atendimentos/<int:atendimento_id>/escolher", methods=["POST"])
@login_required
def api_escolher_atendimento(atendimento_id):
    return AtendimentoController().escolher(atendimento_id)
