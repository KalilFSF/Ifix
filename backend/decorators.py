# Decorators de autorização por papel, aplicados nos Controllers depois do
# @login_required (que só garante "tem sessão", não "tem permissão").
#
# Antes disso a checagem era um `if not current_user.eh_tecnico: return 403`
# repetido em cada método de Controller que precisava — mesma resposta,
# escrita várias vezes. Aqui ela existe num lugar só.

from functools import wraps

from flask import jsonify
from flask_login import current_user


def apenas_tecnico(funcao):
    """Libera o endpoint só pra quem tem perfil técnico (Usuario.eh_tecnico
    cobre tanto role="tecnico" quanto a conta cliente que virou técnica)."""

    @wraps(funcao)
    def wrapper(*args, **kwargs):
        if not current_user.eh_tecnico:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403
        return funcao(*args, **kwargs)

    return wrapper
