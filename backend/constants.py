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

TIPO_NOTEBOOK = "notebook"
TIPO_DESKTOP = "desktop"
TIPOS_EQUIPAMENTO = (TIPO_NOTEBOOK, TIPO_DESKTOP)

CATEGORIA_HARDWARE = "hardware"
CATEGORIA_SOFTWARE = "software"
CATEGORIAS_PROBLEMA = (CATEGORIA_HARDWARE, CATEGORIA_SOFTWARE)

MAX_FOTOS_CHAMADO = 5
MAX_BYTES_FOTO_CHAMADO = 2 * 1024 * 1024  # 2 MB por foto

# Garantia opcional na abertura do chamado: +7% sobre o valor do serviço.
# Se o problema voltar em até 10 dias após a finalização, o cliente pode
# pedir reembolso ou um novo atendimento gratuito.
GARANTIA_PERCENTUAL = 0.07
GARANTIA_DIAS = 10
