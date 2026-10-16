from flask import jsonify
from flask_login import current_user, login_required

from modules.notificacoes.services.listar_notificacoes_service import ListarNotificacoesService
from modules.notificacoes.services.marcar_notificacoes_lidas_service import MarcarNotificacoesLidasService


class NotificacaoController:
    """Sem try/except de DominioError: o errorhandler global de app.py traduz."""

    def __init__(self):
        self.listar_notificacoes_service = ListarNotificacoesService()
        self.marcar_notificacoes_lidas_service = MarcarNotificacoesLidasService()

    @login_required
    def listar(self):
        return jsonify(self.listar_notificacoes_service.executar(current_user))

    @login_required
    def marcar_todas_lidas(self):
        total = self.marcar_notificacoes_lidas_service.executar_todas(current_user)
        return jsonify({"ok": True, "marcadas": total})

    @login_required
    def marcar_lida(self, notificacao_id):
        self.marcar_notificacoes_lidas_service.executar_uma(notificacao_id, current_user)
        return jsonify({"ok": True})
