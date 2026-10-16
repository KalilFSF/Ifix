# Rotas do módulo "notificacoes" (avisos dentro do app, o "sino") — só declara
# endpoint + auth e encaminha pro Controller.

from flask import Blueprint
from flask_login import login_required

from modules.notificacoes.controllers.notificacao_controller import NotificacaoController

notificacoes_bp = Blueprint("notificacoes", __name__)


@notificacoes_bp.route("/api/notificacoes", methods=["GET"])
@login_required
def api_listar_notificacoes():
    return NotificacaoController().listar()


@notificacoes_bp.route("/api/notificacoes/lidas", methods=["POST"])
@login_required
def api_marcar_notificacoes_lidas():
    return NotificacaoController().marcar_todas_lidas()


@notificacoes_bp.route("/api/notificacoes/<int:notificacao_id>/lida", methods=["POST"])
@login_required
def api_marcar_notificacao_lida(notificacao_id):
    return NotificacaoController().marcar_lida(notificacao_id)
