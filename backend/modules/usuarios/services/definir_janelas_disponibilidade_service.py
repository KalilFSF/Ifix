from constants import MAX_JANELAS_DISPONIBILIDADE
from exceptions import ValidacaoError
from modules.usuarios.models.disponibilidade import JanelaDisponibilidade
from utils import parsear_horario


class DefinirJanelasDisponibilidadeService:
    """Substitui as janelas semanais do técnico (funcionalidade 3).

    Lista vazia é válida: quem apaga tudo quer dizer "sem horário fixo".
    Faixa que atravessa a meia-noite não é aceita aqui — quem trabalha de
    madrugada cadastra duas janelas (até 23:59 e a partir de 00:00)."""

    def executar(self, tecnico, dados):
        janelas = dados.get("janelas")
        if not isinstance(janelas, list):
            raise ValidacaoError("Informe as janelas de disponibilidade em uma lista.")
        if len(janelas) > MAX_JANELAS_DISPONIBILIDADE:
            raise ValidacaoError(f"Cadastre no máximo {MAX_JANELAS_DISPONIBILIDADE} janelas.")

        validadas = [self._validar_janela(janela) for janela in janelas]
        self._validar_sem_sobreposicao(validadas)
        return JanelaDisponibilidade.substituir_todas(tecnico.id, validadas)

    @staticmethod
    def _validar_janela(janela):
        if not isinstance(janela, dict):
            raise ValidacaoError("Janela de disponibilidade inválida.")

        dia = janela.get("dia_semana")
        if isinstance(dia, bool) or not isinstance(dia, int) or not 0 <= dia <= 6:
            raise ValidacaoError("Escolha um dia da semana válido.")

        inicio = parsear_horario(janela.get("inicio"))
        fim = parsear_horario(janela.get("fim"))
        if inicio is None or fim is None:
            raise ValidacaoError("Informe horários válidos no formato HH:MM.")
        if inicio >= fim:
            raise ValidacaoError("O horário de início deve ser anterior ao de fim.")

        return {"dia_semana": dia, "inicio": inicio.strftime("%H:%M"), "fim": fim.strftime("%H:%M")}

    @staticmethod
    def _validar_sem_sobreposicao(janelas):
        ordenadas = sorted(janelas, key=lambda j: (j["dia_semana"], j["inicio"]))
        for anterior, atual in zip(ordenadas, ordenadas[1:]):
            if anterior["dia_semana"] == atual["dia_semana"] and atual["inicio"] < anterior["fim"]:
                raise ValidacaoError("Há janelas sobrepostas no mesmo dia.")
