from flask import jsonify, request
from flask_login import current_user, login_required

from services.servico_service import ServicoService


class ServicoController:
    @staticmethod
    def listar():
        status = request.args.get("status")
        servicos = ServicoService.listar_servicos(status=status)
        return jsonify([servico.to_dict() for servico in servicos])

    @staticmethod
    @login_required
    def criar():
        dados = request.get_json(silent=True) or {}
        if current_user.role != "cliente":
            return jsonify({"ok": False, "erro": "Apenas clientes podem abrir serviços."}), 403

        servico = ServicoService.criar_servico(dados, current_user.id)
        return jsonify({"ok": True, "servico": servico.to_dict()})

    @staticmethod
    @login_required
    def atribuir_tecnico(servico_id):
        if current_user.role != "tecnico":
            return jsonify({"ok": False, "erro": "Apenas técnicos podem aceitar serviços."}), 403

        servico = ServicoService.atribuir_tecnico(servico_id, current_user.id)
        return jsonify({"ok": True, "servico": servico.to_dict()})

    @staticmethod
    @login_required
    def atualizar_status(servico_id):
        dados = request.get_json(silent=True) or {}
        status = dados.get("status")
        if not status:
            return jsonify({"ok": False, "erro": "Status é obrigatório."}), 400

        servico = ServicoService.atualizar_status(servico_id, status)
        return jsonify({"ok": True, "servico": servico.to_dict()})

    @staticmethod
    @login_required
    def detalhes(servico_id):
        servico = ServicoService.get_servico(servico_id)
        atendimentos = [atendimento.to_dict() for atendimento in servico.atendimentos]
        payload = servico.to_dict()
        payload["atendimentos"] = atendimentos
        return jsonify(payload)

    @staticmethod
    @login_required
    def criar_atendimento(servico_id):
        dados = request.get_json(silent=True) or {}
        if current_user.role not in {"cliente", "tecnico"}:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        atendimento = ServicoService.criar_ou_atualizar_atendimento(
            dados,
            servico_id,
            current_user.id,
            current_user.role,
        )
        return jsonify({"ok": True, "atendimento": atendimento.to_dict()})
