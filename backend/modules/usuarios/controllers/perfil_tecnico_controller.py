from flask import jsonify, request
from flask_login import current_user, login_required

from decorators import apenas_tecnico
from exceptions import DominioError
from modules.usuarios.services.atualizar_perfil_tecnico_service import AtualizarPerfilTecnicoService
from modules.usuarios.services.obter_perfil_tecnico_service import ObterPerfilTecnicoService


class PerfilTecnicoController:
    def __init__(self):
        self.obter_perfil_tecnico_service = ObterPerfilTecnicoService()
        self.atualizar_perfil_tecnico_service = AtualizarPerfilTecnicoService()

    @login_required
    @apenas_tecnico
    def obter(self):
        try:
            perfil = self.obter_perfil_tecnico_service.executar(current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({
            "ok": True,
            "usuario": current_user.to_dict(),
            "perfil": perfil.to_dict(),
            "diplomas": [diploma.to_dict() for diploma in perfil.diplomas],
        })

    @login_required
    @apenas_tecnico
    def atualizar(self):

        dados = request.get_json(silent=True) or {}
        try:
            perfil = self.atualizar_perfil_tecnico_service.executar(current_user, dados)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "perfil": perfil.to_dict()})
