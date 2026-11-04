"""Ativa ou desativa a disponibilidade temporária do próprio técnico."""
from transactions import atomic, lock_model, lock_child
from exceptions import RecursoNaoEncontradoError, ValidacaoError


class DefinirDisponivelAgoraService:
    """Liga/desliga o status "disponível agora" (funcionalidade 6). Ligado,
    vale por DISPONIVEL_AGORA_VALIDADE_HORAS — ver PerfilTecnico."""

    @atomic
    def executar(self, tecnico, dados):
        from modules.usuarios.models.usuario import Usuario
        tecnico = lock_model(Usuario, tecnico.id)
        perfil = lock_model(type(tecnico.perfil_tecnico),tecnico.perfil_tecnico.id) if tecnico.perfil_tecnico else None
        if perfil is None:
            raise RecursoNaoEncontradoError("Perfil não encontrado.")

        disponivel = dados.get("disponivel")
        if not isinstance(disponivel, bool):
            raise ValidacaoError("Informe se você está disponível agora (true ou false).")

        return perfil.definir_disponivel_agora(disponivel)
