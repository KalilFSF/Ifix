from constants import MIN_CARACTERES_MODELO_HISTORICO
from modules.servicos.repositories.servico_repository import ServicoRepository


class ObterHistoricoAparelhoService:
    """Chamados anteriores do mesmo cliente para o mesmo aparelho
    (funcionalidade 10): mostra, antes e durante um novo chamado, o que já
    aconteceu com aquele modelo e qual foi a causa registrada no laudo.

    Só enxerga os chamados do próprio usuário — o cliente_id vem da sessão e
    nunca da requisição, então não há como consultar o histórico de outra
    pessoa. Modelo curto demais devolve lista vazia (e não erro): o front
    consulta enquanto o cliente ainda está digitando."""

    def __init__(self):
        self.servico_repository = ServicoRepository()

    def executar(self, cliente, equipamento, excluir_servico_id=None):
        modelo = (equipamento or "").strip()
        if len(modelo) < MIN_CARACTERES_MODELO_HISTORICO:
            return []
        return self.servico_repository.buscar_historico_aparelho(cliente.id, modelo, excluir_servico_id)
