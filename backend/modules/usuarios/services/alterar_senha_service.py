from exceptions import ValidacaoError

MIN_CARACTERES_SENHA = 6


class AlterarSenhaService:
    """Troca de senha pela tela de perfil.

    Exige a senha atual mesmo com o usuário já logado: uma sessão esquecida
    aberta numa máquina compartilhada não deve bastar pra tomar a conta.
    """

    def executar(self, usuario, dados):
        senha_atual = dados.get("senha_atual") or ""
        nova_senha = dados.get("nova_senha") or ""
        confirmar_senha = dados.get("confirmar_senha") or ""

        if not usuario.check_senha(senha_atual):
            raise ValidacaoError("A senha atual está incorreta.")
        if len(nova_senha) < MIN_CARACTERES_SENHA:
            raise ValidacaoError(f"A nova senha deve ter pelo menos {MIN_CARACTERES_SENHA} caracteres.")
        if nova_senha != confirmar_senha:
            return self._erro_confirmacao()
        if nova_senha == senha_atual:
            raise ValidacaoError("A nova senha precisa ser diferente da atual.")

        usuario.set_senha(nova_senha)
        return usuario.salvar()

    @staticmethod
    def _erro_confirmacao():
        raise ValidacaoError("A confirmação não confere com a nova senha.")
