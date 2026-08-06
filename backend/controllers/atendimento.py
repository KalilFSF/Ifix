from flask import jsonify, request
from flask_login import current_user, login_required

from database import db
from models import Atendimento


class AtendimentoController:
    @staticmethod
    @login_required
    def listar():
        if current_user.role == "tecnico":
            atendimentos = Atendimento.query.filter_by(tecnico_id=current_user.id).order_by(Atendimento.criado_em.desc()).all()
        elif current_user.role == "cliente":
            atendimentos = Atendimento.query.filter_by(cliente_id=current_user.id).order_by(Atendimento.criado_em.desc()).all()
        else:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        return jsonify([atendimento.to_dict() for atendimento in atendimentos])

    @staticmethod
    @login_required
    def atualizar_status(atendimento_id):
        dados = request.get_json(silent=True) or {}
        if current_user.role != "tecnico":
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        atendimento = Atendimento.query.get_or_404(atendimento_id)
        atendimento.status = dados.get("status", atendimento.status)
        atendimento.valor_orcamento = dados.get("valor_orcamento", atendimento.valor_orcamento)
        atendimento.tecnico_id = current_user.id
        db.session.commit()
        return jsonify({"ok": True, "atendimento": atendimento.to_dict()})
