"""Todos os 14 modelos, sem app nem conexão."""
from modules.usuarios.models.usuario import Usuario
from modules.usuarios.models.tecnico import PerfilTecnico, Diploma
from modules.usuarios.models.disponibilidade import JanelaDisponibilidade
from modules.servicos.models.servico import Servico, FotoServico
from modules.servicos.models.solicitacao import SolicitacaoTecnico
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.aprovacao import SolicitacaoAprovacao
from modules.servicos.models.garantia import AcionamentoGarantia
from modules.atendimentos.models.atendimento import Atendimento
from modules.atendimentos.models.avaliacao import Avaliacao
from modules.chat.models.mensagem import MensagemChamado
from modules.notificacoes.models.notificacao import Notificacao
