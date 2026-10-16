from flask import jsonify, request
from flask_login import login_required

from modules.usuarios.services.listar_diretorio_tecnicos_service import ListarDiretorioTecnicosService
from modules.usuarios.services.obter_perfil_publico_tecnico_service import ObterPerfilPublicoTecnicoService


class DiretorioTecnicosController:
    """Sem try/except de DominioError: o errorhandler global de app.py traduz."""

    def __init__(self):
        self.listar_diretorio_tecnicos_service = ListarDiretorioTecnicosService()
        self.obter_perfil_publico_tecnico_service = ObterPerfilPublicoTecnicoService()

    @login_required
    def listar(self):
        return jsonify(self.listar_diretorio_tecnicos_service.executar(request.args))

    @login_required
    def perfil_publico(self, tecnico_id):
        return jsonify(self.obter_perfil_publico_tecnico_service.executar(tecnico_id))
