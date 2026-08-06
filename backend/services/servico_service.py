from database import db
from models import Servico, Atendimento, Usuario


class ServicoService:
    @staticmethod
    def listar_servicos(status=None):
        query = Servico.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Servico.criado_em.desc()).all()

    @staticmethod
    def criar_servico(dados, cliente_id):
        servico = Servico(
            titulo=dados["titulo"],
            descricao=dados["descricao"],
            categoria=dados["categoria"],
            preco_estimado=dados.get("preco_estimado", 0),
            cliente_id=cliente_id,
            status="aberto",
        )
        db.session.add(servico)
        db.session.commit()
        return servico

    @staticmethod
    def atribuir_tecnico(servico_id, tecnico_id):
        servico = Servico.query.get_or_404(servico_id)
        servico.tecnico_id = tecnico_id
        servico.status = "em_andamento"
        db.session.commit()
        return servico

    @staticmethod
    def atualizar_status(servico_id, status):
        servico = Servico.query.get_or_404(servico_id)
        servico.status = status
        db.session.commit()
        return servico

    @staticmethod
    def criar_ou_atualizar_atendimento(dados, servico_id, usuario_id, role):
        atendimento = Atendimento.query.filter_by(servico_id=servico_id).first()

        if atendimento is None:
            atendimento = Atendimento(
                titulo=dados.get("titulo") or "Orçamento",
                descricao=dados.get("descricao") or "Orçamento enviado para o cliente.",
                status=dados.get("status", "pendente"),
                valor_orcamento=dados.get("valor_orcamento"),
                cliente_id=dados.get("cliente_id"),
                servico_id=servico_id,
            )
            db.session.add(atendimento)
        else:
            atendimento.titulo = dados.get("titulo", atendimento.titulo)
            atendimento.descricao = dados.get("descricao", atendimento.descricao)
            atendimento.status = dados.get("status", atendimento.status)
            atendimento.valor_orcamento = dados.get("valor_orcamento", atendimento.valor_orcamento)

        if role == "cliente":
            atendimento.cliente_id = usuario_id
        else:
            atendimento.tecnico_id = usuario_id

        db.session.commit()
        return atendimento

    @staticmethod
    def get_servico(servico_id):
        return Servico.query.get_or_404(servico_id)
