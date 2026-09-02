from sqlalchemy import text

from database import db


class UsuarioRepository:
    """Consultas de Usuario que extrapolam CRUD simples (JOIN entre tabelas).
    CRUD básico (buscar_por_id, buscar_por_email, listar_por_role...) já é
    resolvido direto pela Model — este Repository só existe para o que
    precisa juntar dados de mais de uma tabela, e faz isso chamando as
    procedures definidas em backend/database/procedures.sql (nunca Model/
    SQLAlchemy ORM direto)."""

    def buscar_tecnicos_com_perfil(self):
        resultado = db.session.execute(text("SELECT * FROM fn_listar_tecnicos_com_perfil()"))
        return [linha[0] for linha in resultado]

    def buscar_tecnicos_para_ranking(self):
        """Candidatos a SelecionarTecnicosService: técnicos com perfil e com
        lat/long cadastrados (sem coordenada não dá pra calcular distância,
        então ficam de fora do ranking)."""
        resultado = db.session.execute(text("SELECT * FROM fn_listar_tecnicos_para_ranking()"))
        return resultado.mappings().all()
