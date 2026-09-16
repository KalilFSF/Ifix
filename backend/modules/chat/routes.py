# Rotas do módulo "chat" (conversa entre cliente e técnico dentro de um
# chamado) — só declara endpoint + auth e encaminha pro Controller.

from flask import Blueprint
from flask_login import login_required

from modules.chat.controllers.chat_controller import ChatController

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/servicos/<int:servico_id>/mensagens", methods=["GET"])
@login_required
def api_listar_mensagens(servico_id):
    return ChatController().listar(servico_id)


@chat_bp.route("/api/servicos/<int:servico_id>/mensagens", methods=["POST"])
@login_required
def api_enviar_mensagem(servico_id):
    return ChatController().enviar(servico_id)


@chat_bp.route("/api/servicos/<int:servico_id>/mensagens/lidas", methods=["POST"])
@login_required
def api_marcar_mensagens_lidas(servico_id):
    return ChatController().marcar_lidas(servico_id)


@chat_bp.route("/api/mensagens/nao-lidas", methods=["GET"])
@login_required
def api_mensagens_nao_lidas():
    return ChatController().nao_lidas()
