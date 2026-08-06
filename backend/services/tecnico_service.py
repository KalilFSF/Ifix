from database import db
from models import PerfilTecnico


class TecnicoService:
    @staticmethod
    def criar_perfil(usuario, dados_tecnico, foto_perfil, diplomas_arquivos):
        perfil = PerfilTecnico(
            usuario_id=usuario.id,
            especialidade=dados_tecnico.get("especialidade", ""),
            escolaridade=dados_tecnico.get("escolaridade", ""),
            curso_superior=dados_tecnico.get("curso_superior") or None,
            regiao_atendimento=dados_tecnico.get("regiao_atendimento", ""),
            cursos_experiencias=dados_tecnico.get("cursos_experiencias") or None,
            especializacoes=dados_tecnico.get("especializacoes") or None,
            foto_perfil=foto_perfil,
        )
        db.session.add(perfil)
        db.session.commit()
        return perfil

    @staticmethod
    def atualizar_perfil(perfil, dados):
        for campo in ["especialidade", "escolaridade", "curso_superior", "regiao_atendimento", "cursos_experiencias", "especializacoes"]:
            if campo in dados:
                setattr(perfil, campo, dados[campo])
        db.session.commit()
        return perfil
