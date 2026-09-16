from flask import jsonify, request
from flask_login import current_user, login_required

from decorators import apenas_tecnico
from exceptions import DominioError
from modules.atendimentos.services.enviar_orcamento_service import EnviarOrcamentoService
from modules.servicos.services.aceitar_solicitacao_service import AceitarSolicitacaoService
from modules.servicos.services.listar_solicitacoes_pendentes_service import ListarSolicitacoesPendentesService
from modules.servicos.services.recusar_solicitacao_service import RecusarSolicitacaoService
from utils import corpo_json


class SolicitacaoController:
    def __init__(self):
        self.listar_solicitacoes_pendentes_service = ListarSolicitacoesPendentesService()
        self.aceitar_solicitacao_service = AceitarSolicitacaoService()
        self.recusar_solicitacao_service = RecusarSolicitacaoService()
        self.enviar_orcamento_service = EnviarOrcamentoService()

    @login_required
    @apenas_tecnico
    def listar(self):
        solicitacoes = self.listar_solicitacoes_pendentes_service.executar(current_user.id)
        return jsonify(solicitacoes)

    @login_required
    @apenas_tecnico
    def aceitar(self, solicitacao_id):
        try:
            solicitacao = self.aceitar_solicitacao_service.executar(solicitacao_id, current_user.id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "solicitacao": solicitacao.to_dict()})

    @login_required
    @apenas_tecnico
    def enviar_orcamento(self, solicitacao_id):
        dados = corpo_json()
        try:
            atendimento = self.enviar_orcamento_service.executar(solicitacao_id, current_user.id, dados)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "atendimento": atendimento.to_dict()})

    @login_required
    @apenas_tecnico
    def recusar(self, solicitacao_id):
        try:
            solicitacao = self.recusar_solicitacao_service.executar(solicitacao_id, current_user.id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "solicitacao": solicitacao.to_dict()})
