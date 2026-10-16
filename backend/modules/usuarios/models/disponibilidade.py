from constants import DIAS_SEMANA_LABELS
from database import db


class JanelaDisponibilidade(db.Model):
    """Faixa de horário em que o técnico atende num dia da semana
    (funcionalidade 3). O cliente só consulta — não há agendamento: serve
    pra ele saber quando o técnico costuma estar disponível.

    dia_semana segue o Python (0 = segunda ... 6 = domingo); inicio/fim são
    "HH:MM" em string pelo mesmo motivo de Usuario.horario_*_atendimento."""

    __tablename__ = "janelas_disponibilidade"

    id = db.Column(db.Integer, primary_key=True)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    dia_semana = db.Column(db.Integer, nullable=False)
    inicio = db.Column(db.String(5), nullable=False)
    fim = db.Column(db.String(5), nullable=False)

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    @classmethod
    def listar_por_tecnico(cls, tecnico_id):
        return cls.query.filter_by(tecnico_id=tecnico_id).order_by(cls.dia_semana, cls.inicio).all()

    @classmethod
    def substituir_todas(cls, tecnico_id, janelas):
        """Troca o conjunto inteiro numa transação só — é o que torna o PUT
        idempotente e evita ficar com metade das janelas se algo falhar."""
        cls.query.filter_by(tecnico_id=tecnico_id).delete(synchronize_session=False)
        for janela in janelas:
            db.session.add(cls(
                tecnico_id=tecnico_id,
                dia_semana=janela["dia_semana"],
                inicio=janela["inicio"],
                fim=janela["fim"],
            ))
        db.session.commit()
        return cls.listar_por_tecnico(tecnico_id)

    def to_dict(self):
        return {
            "dia_semana": self.dia_semana,
            "dia_label": DIAS_SEMANA_LABELS[self.dia_semana],
            "inicio": self.inicio,
            "fim": self.fim,
        }
