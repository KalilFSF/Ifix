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


@servicos_bp.route("/api/servicos/<int:servico_id>", methods=["DELETE"])
@login_required
def api_excluir_servico(servico_id):
    return ServicoController().excluir(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/status", methods=["PATCH"])
@login_required
def api_status_servico(servico_id):
    return ServicoController().atualizar_status(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/laudo", methods=["PUT"])
@login_required
def api_laudo_servico(servico_id):
    # PUT: o laudo é um recurso único do chamado e reenviar o mesmo conteúdo
    # tem o mesmo efeito (idempotente).
    return ServicoController().registrar_laudo(servico_id)


# Autorização de custo adicional (funcionalidades 6 e 7): sub-recurso do
# chamado, no plural — vários pedidos ao longo de um mesmo atendimento.
@servicos_bp.route("/api/servicos/<int:servico_id>/aprovacoes", methods=["POST"])
@login_required
def api_solicitar_aprovacao(servico_id):
    return ServicoController().solicitar_aprovacao(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/aprovacoes", methods=["GET"])
@login_required
def api_listar_aprovacoes(servico_id):
    return ServicoController().aprovacoes(servico_id)


@servicos_bp.route("/api/aprovacoes/<int:aprovacao_id>", methods=["PATCH"])
@login_required
def api_responder_aprovacao(aprovacao_id):
    # PATCH: altera só o status (e a justificativa) de uma aprovação que já
    # existe — o recurso não é substituído por inteiro.
    return ServicoController().responder_aprovacao(aprovacao_id)


# Acionamento da garantia (funcionalidade 2).
@servicos_bp.route("/api/servicos/<int:servico_id>/garantia", methods=["POST"])
@login_required
def api_acionar_garantia(servico_id):
    return ServicoController().acionar_garantia(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/garantia", methods=["GET"])
@login_required
def api_listar_acionamentos_garantia(servico_id):
    return ServicoController().acionamentos_garantia(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/cancelar", methods=["POST"])
@login_required
def api_cancelar_servico(servico_id):
    return ServicoController().cancelar(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/historico", methods=["GET"])
@login_required
def api_historico_servico(servico_id):
    return ServicoController().historico(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/orcamentos", methods=["GET"])
@login_required
def api_orcamentos_servico(servico_id):
    return ServicoController().orcamentos(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/avaliar", methods=["POST"])
@login_required
def api_avaliar_servico(servico_id):
    return ServicoController().avaliar(servico_id)


@servicos_bp.route("/api/servicos/<int:servico_id>/avaliacoes", methods=["GET"])
@login_required
def api_avaliacoes_servico(servico_id):
    return ServicoController().avaliacoes(servico_id)


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


@servicos_bp.route("/api/tecnico/solicitacoes/<int:solicitacao_id>/orcamento", methods=["POST"])
@login_required
def api_tecnico_solicitacao_orcamento(solicitacao_id):
    return SolicitacaoController().enviar_orcamento(solicitacao_id)
