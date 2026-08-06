from flask import jsonify, request
from flask_login import current_user, login_required

from services.tecnico_service import TecnicoService


class TecnicoController:
    @staticmethod
    @login_required
    def perfil():
        if current_user.role != "tecnico":
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        perfil = current_user.perfil_tecnico
        if not perfil:
            return jsonify({"ok": False, "erro": "Perfil não encontrado."}), 404

        return jsonify({
            "ok": True,
            "usuario": current_user.to_dict(),
            "perfil": perfil.to_dict(),
            "diplomas": [diploma.to_dict() for diploma in perfil.diplomas],
        })

    @staticmethod
    @login_required
    def atualizar_perfil():
        if current_user.role != "tecnico":
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        dados = request.get_json(silent=True) or {}
        perfil = current_user.perfil_tecnico
        if not perfil:
            return jsonify({"ok": False, "erro": "Perfil não encontrado."}), 404

        perfil = TecnicoService.atualizar_perfil(perfil, dados)
        return jsonify({"ok": True, "perfil": perfil.to_dict()})
