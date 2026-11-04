"""Valida a faixa diária de contato usada pelo envio de e-mail de solicitação."""
from transactions import atomic, lock_model, lock_child
from exceptions import ValidacaoError
from utils import parsear_horario


class DefinirHorarioAtendimentoService:
    """Restrição de horário (funcionalidade 9): o usuário define a faixa do dia
    em que aceita ser atendido/acionado.

    Para o cliente, evita ser incomodado fora de hora; para o técnico, evita
    receber solicitação de chamado fora do expediente (quem filtra é
    SolicitarTecnicosService, na hora de notificar).

    A faixa é guardada como "HH:MM" e pode virar a meia-noite (ex: 22:00 às
    06:00, de quem trabalha à noite) — por isso não se exige inicio < fim."""

    @atomic
    def executar(self, usuario, dados):
        from modules.usuarios.models.usuario import Usuario
        usuario = lock_model(Usuario, usuario.id)
        inicio = self._parse_horario(dados.get("horario_inicio_atendimento"), "de início")
        fim = self._parse_horario(dados.get("horario_fim_atendimento"), "de término")

        if inicio == fim:
            raise ValidacaoError("O horário de início e o de término não podem ser iguais.")

        return usuario.definir_horario_atendimento(inicio, fim)

    @staticmethod
    def _parse_horario(valor, nome_campo):
        horario = parsear_horario(valor)
        if horario is None:
            raise ValidacaoError(f"Informe um horário {nome_campo} válido (HH:MM).")
        return horario.strftime("%H:%M")
