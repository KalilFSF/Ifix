from exceptions import ValidacaoError
from modules.chat.models.mensagem import MAX_CARACTERES_MENSAGEM, MensagemChamado
from modules.chat.services.listar_mensagens_service import garantir_acesso_ao_chat


class EnviarMensagemService:
    """Grava uma mensagem do chat do chamado.

    Não dispara e-mail de propósito: uma conversa gera muitas mensagens
    seguidas, e avisar a cada uma transformaria a caixa de entrada do outro
    lado em ruído — e o ruído acaba fazendo ignorar também os avisos que
    importam (status, autorização de custo, garantia). O aviso aqui é o
    badge de não lidas no painel, que o polling já atualiza.
    """

    def executar(self, servico_id, autor, dados):
        servico = garantir_acesso_ao_chat(servico_id, autor)

        if servico.tecnico_id is None:
            raise ValidacaoError(
                "A conversa fica disponível depois que você escolher um orçamento."
            )

        conteudo = (dados.get("conteudo") or "").strip()
        if not conteudo:
            raise ValidacaoError("Escreva uma mensagem antes de enviar.")
        if len(conteudo) > MAX_CARACTERES_MENSAGEM:
            raise ValidacaoError(
                f"A mensagem deve ter no máximo {MAX_CARACTERES_MENSAGEM} caracteres."
            )

        return MensagemChamado.criar(servico_id, autor.id, conteudo)


class MarcarMensagensLidasService:
    def executar(self, servico_id, usuario):
        garantir_acesso_ao_chat(servico_id, usuario)
        return MensagemChamado.marcar_lidas(servico_id, usuario.id)
