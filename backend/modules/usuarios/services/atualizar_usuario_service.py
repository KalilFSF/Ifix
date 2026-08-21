class AtualizarUsuarioService:
    def executar(self, usuario, dados):
        return usuario.atualizar(dados)
