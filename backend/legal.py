"""Versões publicadas e validação explícita do aceite no cadastro."""
from exceptions import ValidacaoError

TERMOS_VERSAO = "2026-11-05.1"
PRIVACIDADE_VERSAO = "2026-11-05.1"

def validar_aceite(dados):
    # Não aceitar "false", "0", ausência ou qualquer string truthy.
    if dados.get("aceite_termos") != "1":
        raise ValidacaoError("Para criar sua conta, aceite os Termos de Uso e declare ciência do Aviso de Privacidade.")
    if dados.get("termos_versao") != TERMOS_VERSAO or dados.get("privacidade_versao") != PRIVACIDADE_VERSAO:
        raise ValidacaoError("Os documentos foram atualizados. Recarregue o cadastro, leia os textos atuais e confirme o aceite novamente.")
