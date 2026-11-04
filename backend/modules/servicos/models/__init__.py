"""Pacote backend.modules.servicos.models. Organiza imports; não inicializa a aplicação."""
from .servico import Servico, FotoServico
from .solicitacao import SolicitacaoTecnico
from .historico import HistoricoServico
from .aprovacao import SolicitacaoAprovacao
from .garantia import AcionamentoGarantia

__all__ = [
    "Servico",
    "FotoServico",
    "SolicitacaoTecnico",
    "HistoricoServico",
    "SolicitacaoAprovacao",
    "AcionamentoGarantia",
]
