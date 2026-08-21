from database import db
from modules.usuarios.models.tecnico import PerfilTecnico
from modules.usuarios.models.usuario import Usuario


class UsuarioRepository:
    """Consultas de Usuario que extrapolam CRUD simples (JOIN entre tabelas).
    CRUD básico (buscar_por_id, buscar_por_email, listar_por_role...) já é
    resolvido direto pela Model — este Repository só existe para o que
    precisa juntar dados de mais de uma tabela."""

    def buscar_tecnicos_com_perfil(self):
        return (
            db.session.query(Usuario)
            .join(PerfilTecnico, PerfilTecnico.usuario_id == Usuario.id)
            .filter(Usuario.role == "tecnico")
            .all()
        )

    def buscar_tecnicos_para_ranking(self):
        """Candidatos a SelecionarTecnicosService: técnicos com perfil e com
        lat/long cadastrados (sem coordenada não dá pra calcular distância,
        então ficam de fora do ranking)."""
        return (
            db.session.query(Usuario, PerfilTecnico)
            .join(PerfilTecnico, PerfilTecnico.usuario_id == Usuario.id)
            .filter(Usuario.role == "tecnico")
            .filter(Usuario.latitude.isnot(None), Usuario.longitude.isnot(None))
            .all()
        )
