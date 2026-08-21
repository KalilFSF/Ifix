from flask import jsonify, request
from flask_login import current_user, login_required

from exceptions import DominioError
from modules.servicos.services.atribuir_tecnico_service import AtribuirTecnicoService
from modules.servicos.services.atualizar_status_servico_service import AtualizarStatusServicoService
from modules.servicos.services.criar_servico_service import CriarServicoService
from modules.servicos.services.listar_meus_servicos_service import ListarMeusServicosService
from modules.servicos.services.obter_detalhes_servico_service import ObterDetalhesServicoService
from modules.servicos.services.obter_historico_servico_service import ObterHistoricoServicoService
from modules.servicos.services.solicitar_tecnicos_service import SolicitarTecnicosService


class ServicoController:
    def __init__(self):
        self.criar_servico_service = CriarServicoService()
        self.listar_meus_servicos_service = ListarMeusServicosService()
        self.obter_detalhes_servico_service = ObterDetalhesServicoService()
        self.atualizar_status_servico_service = AtualizarStatusServicoService()
        self.obter_historico_servico_service = ObterHistoricoServicoService()
        self.solicitar_tecnicos_service = SolicitarTecnicosService()
        self.atribuir_tecnico_service = AtribuirTecnicoService()

    @login_required
    def meus(self):
        status = request.args.get("status")
        if current_user.role not in {"cliente", "tecnico"}:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        servicos = self.listar_meus_servicos_service.executar(current_user.id, current_user.role, status)
        return jsonify([servico.to_dict_painel() for servico in servicos])

    @login_required
    def criar(self):
        dados = request.get_json(silent=True) or {}
        if current_user.role != "cliente":
            return jsonify({"ok": False, "erro": "Apenas clientes podem abrir serviços."}), 403

        servico = self.criar_servico_service.executar(dados, current_user.id)
        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    def detalhes(self, servico_id):
        try:
            servico = self.obter_detalhes_servico_service.executar(servico_id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        payload = servico.to_dict()
        payload["atendimentos"] = [atendimento.to_dict() for atendimento in servico.atendimentos]
        return jsonify(payload)

    @login_required
    def atualizar_status(self, servico_id):
        dados = request.get_json(silent=True) or {}
        status = dados.get("status")
        if not status:
            return jsonify({"ok": False, "erro": "Status é obrigatório."}), 400

        try:
            servico = self.atualizar_status_servico_service.executar(servico_id, status, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    def historico(self, servico_id):
        try:
            entradas = self.obter_historico_servico_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify([entrada.to_dict() for entrada in entradas])

    @login_required
    def solicitar(self, servico_id):
        dados = request.get_json(silent=True) or {}
        tecnico_ids = dados.get("tecnico_ids") or []
        if current_user.role != "cliente":
            return jsonify({"ok": False, "erro": "Apenas o cliente dono do chamado pode solicitar técnicos."}), 403
        if not tecnico_ids:
            return jsonify({"ok": False, "erro": "Informe ao menos um tecnico_id."}), 400

        try:
            solicitacoes = self.solicitar_tecnicos_service.executar(servico_id, tecnico_ids, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "solicitacoes": [solicitacao.to_dict() for solicitacao in solicitacoes]})

    @login_required
    def atribuir_tecnico(self, servico_id):
        """Legado — ver AtribuirTecnicoService."""
        if current_user.role != "tecnico":
            return jsonify({"ok": False, "erro": "Apenas técnicos podem aceitar serviços."}), 403

        try:
            servico = self.atribuir_tecnico_service.executar(servico_id, current_user.id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "servico": servico.to_dict()})
