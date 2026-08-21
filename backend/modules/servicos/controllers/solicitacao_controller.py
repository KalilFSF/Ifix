from flask import jsonify
from flask_login import current_user, login_required

from exceptions import DominioError
from modules.servicos.services.aceitar_solicitacao_service import AceitarSolicitacaoService
from modules.servicos.services.listar_solicitacoes_pendentes_service import ListarSolicitacoesPendentesService
from modules.servicos.services.recusar_solicitacao_service import RecusarSolicitacaoService


class SolicitacaoController:
    def __init__(self):
        self.listar_solicitacoes_pendentes_service = ListarSolicitacoesPendentesService()
        self.aceitar_solicitacao_service = AceitarSolicitacaoService()
        self.recusar_solicitacao_service = RecusarSolicitacaoService()

    @login_required
    def listar(self):
        if not current_user.eh_tecnico:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        solicitacoes = self.listar_solicitacoes_pendentes_service.executar(current_user.id)
        return jsonify([solicitacao.to_dict_painel() for solicitacao in solicitacoes])

    @login_required
    def aceitar(self, solicitacao_id):
        if not current_user.eh_tecnico:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        try:
            solicitacao = self.aceitar_solicitacao_service.executar(solicitacao_id, current_user.id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "solicitacao": solicitacao.to_dict()})

    @login_required
    def recusar(self, solicitacao_id):
        if not current_user.eh_tecnico:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        try:
            solicitacao = self.recusar_solicitacao_service.executar(solicitacao_id, current_user.id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "solicitacao": solicitacao.to_dict()})
