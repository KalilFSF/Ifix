from flask import jsonify, request
from flask_login import current_user, login_required

from services.usuario_service import UsuarioService


class UsuarioController:
    @staticmethod
    @login_required
    def me():
        usuario = current_user
        dados = {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "role": usuario.role,
        }

        if usuario.role == "tecnico" and usuario.perfil_tecnico:
            perfil = usuario.perfil_tecnico
            dados.update({
                "especialidade": perfil.especialidade,
                "regiao_atendimento": perfil.regiao_atendimento,
                "foto_perfil": f"/uploads/perfil/{perfil.foto_perfil}",
                "diplomas_count": len(perfil.diplomas),
            })

        return jsonify(dados)

    @staticmethod
    @login_required
    def listar_tecnicos():
        tecnicos = UsuarioService.listar_tecnicos()
        return jsonify([tecnico.to_dict() for tecnico in tecnicos])

    @staticmethod
    @login_required
    def atualizar_me():
        dados = request.get_json(silent=True) or {}
        usuario = UsuarioService.atualizar_usuario(current_user, dados)
        return jsonify({"ok": True, "usuario": usuario.to_dict()})
