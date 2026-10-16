from exceptions import RecursoNaoEncontradoError, ValidacaoError


class DefinirDisponivelAgoraService:
    """Liga/desliga o status "disponível agora" (funcionalidade 6). Ligado,
    vale por DISPONIVEL_AGORA_VALIDADE_HORAS — ver PerfilTecnico."""

    def executar(self, tecnico, dados):
        perfil = tecnico.perfil_tecnico
        if perfil is None:
            raise RecursoNaoEncontradoError("Perfil não encontrado.")

        disponivel = dados.get("disponivel")
        if not isinstance(disponivel, bool):
            raise ValidacaoError("Informe se você está disponível agora (true ou false).")

        return perfil.definir_disponivel_agora(disponivel)
