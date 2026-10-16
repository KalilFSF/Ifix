from flask import jsonify
from flask_login import current_user, login_required

from decorators import apenas_tecnico
from modules.usuarios.services.definir_disponivel_agora_service import DefinirDisponivelAgoraService
from modules.usuarios.services.definir_janelas_disponibilidade_service import DefinirJanelasDisponibilidadeService
from modules.usuarios.services.obter_disponibilidade_service import ObterDisponibilidadeService
from utils import corpo_json


class DisponibilidadeController:
    """Janelas semanais e "disponível agora" do técnico logado. Sem
    try/except de DominioError: o errorhandler global de app.py traduz."""

    def __init__(self):
        self.obter_disponibilidade_service = ObterDisponibilidadeService()
        self.definir_janelas_service = DefinirJanelasDisponibilidadeService()
        self.definir_disponivel_agora_service = DefinirDisponivelAgoraService()

    @login_required
    @apenas_tecnico
    def obter(self):
        return jsonify({"ok": True, **self.obter_disponibilidade_service.executar(current_user)})

    @login_required
    @apenas_tecnico
    def definir_janelas(self):
        janelas = self.definir_janelas_service.executar(current_user, corpo_json())
        return jsonify({"ok": True, "janelas": [janela.to_dict() for janela in janelas]})

    @login_required
    @apenas_tecnico
    def definir_disponivel_agora(self):
        perfil = self.definir_disponivel_agora_service.executar(current_user, corpo_json())
        return jsonify({"ok": True, "disponivel_agora": perfil.disponivel_agora})
