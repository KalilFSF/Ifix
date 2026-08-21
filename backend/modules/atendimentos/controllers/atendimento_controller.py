from flask import jsonify, request
from flask_login import current_user, login_required

from exceptions import DominioError
from modules.atendimentos.services.atualizar_status_atendimento_service import AtualizarStatusAtendimentoService
from modules.atendimentos.services.criar_ou_atualizar_atendimento_service import CriarOuAtualizarAtendimentoService
from modules.atendimentos.services.listar_atendimentos_service import ListarAtendimentosService


class AtendimentoController:
    def __init__(self):
        self.criar_ou_atualizar_atendimento_service = CriarOuAtualizarAtendimentoService()
        self.listar_atendimentos_service = ListarAtendimentosService()
        self.atualizar_status_atendimento_service = AtualizarStatusAtendimentoService()

    @login_required
    def listar(self):
        if current_user.role not in {"cliente", "tecnico"}:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        atendimentos = self.listar_atendimentos_service.executar(current_user.id, current_user.role)
        return jsonify([atendimento.to_dict() for atendimento in atendimentos])

    @login_required
    def criar(self, servico_id):
        dados = request.get_json(silent=True) or {}
        if current_user.role not in {"cliente", "tecnico"}:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        atendimento = self.criar_ou_atualizar_atendimento_service.executar(dados, servico_id, current_user.id, current_user.role)
        return jsonify({"ok": True, "atendimento": atendimento.to_dict()})

    @login_required
    def atualizar_status(self, atendimento_id):
        dados = request.get_json(silent=True) or {}
        if current_user.role != "tecnico":
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        try:
            atendimento = self.atualizar_status_atendimento_service.executar(atendimento_id, dados, current_user.id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "atendimento": atendimento.to_dict()})
