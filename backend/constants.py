# Valores válidos de status de um Servico (chamado), centralizados aqui pra
# não ficar espalhado como string livre entre model/service/controller.

STATUS_ABERTO = "aberto"
STATUS_AGUARDANDO = "aguardando"
STATUS_EM_ANALISE = "em_analise"
STATUS_EM_REPARO = "em_reparo"
STATUS_FINALIZADO = "finalizado"

# Os únicos status que um técnico pode definir manualmente via
# PATCH /api/servicos/<id>/status, depois de aceitar o chamado
# ("aberto" é o estado inicial, antes de qualquer técnico aceitar).
STATUS_TECNICO_CHOICES = (
    STATUS_AGUARDANDO,
    STATUS_EM_ANALISE,
    STATUS_EM_REPARO,
    STATUS_FINALIZADO,
)

SOLICITACAO_PENDENTE = "pendente"
SOLICITACAO_ACEITA = "aceita"
SOLICITACAO_RECUSADA = "recusada"
