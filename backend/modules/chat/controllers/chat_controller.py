from flask import jsonify, request
from flask_login import current_user, login_required

from modules.chat.services.enviar_mensagem_service import (
    EnviarMensagemService,
    MarcarMensagensLidasService,
)
from modules.chat.services.listar_mensagens_service import (
    ContarMensagensNaoLidasService,
    ListarMensagensService,
)
from utils import corpo_json


class ChatController:
    """Sem try/except de DominioError: o errorhandler global registrado em
    app.py já traduz a exceção no status e na mensagem certos."""

    def __init__(self):
        self.listar_mensagens_service = ListarMensagensService()
        self.enviar_mensagem_service = EnviarMensagemService()
        self.marcar_mensagens_lidas_service = MarcarMensagensLidasService()
        self.contar_nao_lidas_service = ContarMensagensNaoLidasService()

    @login_required
    def listar(self, servico_id):
        # `desde` permite ao polling pedir só o que chegou depois da última
        # mensagem já exibida, em vez de rebaixar a conversa inteira a cada 7s.
        desde_id = request.args.get("desde", type=int)
        mensagens = self.listar_mensagens_service.executar(servico_id, current_user, desde_id)
        return jsonify(mensagens)

    @login_required
    def enviar(self, servico_id):
        dados = corpo_json()
        mensagem = self.enviar_mensagem_service.executar(servico_id, current_user, dados)
        return jsonify({"ok": True, "mensagem": mensagem.to_dict()}), 201

    @login_required
    def marcar_lidas(self, servico_id):
        total = self.marcar_mensagens_lidas_service.executar(servico_id, current_user)
        return jsonify({"ok": True, "marcadas": total})

    @login_required
    def nao_lidas(self):
        return jsonify(self.contar_nao_lidas_service.executar(current_user))
