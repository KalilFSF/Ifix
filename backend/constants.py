# Valores válidos de status de um Servico (chamado), centralizados aqui pra
# não ficar espalhado como string livre entre model/service/controller.

STATUS_ABERTO = "aberto"
STATUS_AGUARDANDO = "aguardando"
STATUS_EM_ANALISE = "em_analise"
STATUS_EM_REPARO = "em_reparo"
# PAGAMENTO: entraria aqui — antes de permitir a transição pra
# STATUS_FINALIZADO (ver AtualizarStatusServicoService), exigindo
# confirmação de pagamento. Não implementado nesta etapa: por ora o
# técnico finaliza o chamado diretamente.
STATUS_FINALIZADO = "finalizado"
STATUS_CANCELADO = "cancelado"

# Os únicos status que um técnico pode definir manualmente via
# PATCH /api/servicos/<id>/status, depois de aceitar o chamado
# ("aberto" é o estado inicial, antes de qualquer técnico aceitar).
STATUS_TECNICO_CHOICES = (
    STATUS_AGUARDANDO,
    STATUS_EM_ANALISE,
    STATUS_EM_REPARO,
    STATUS_FINALIZADO,
)

# Rótulos em pt-BR pro corpo do e-mail de notificação de status (ver
# AtualizarStatusServicoService) — mesmos textos usados nos badges do
# front (tecnico-home.js / cliente-chamados.js), duplicados aqui porque o
# backend não tem acesso ao JS do front pra reaproveitar.
STATUS_LABELS_EMAIL = {
    STATUS_ABERTO: "Aguardando técnico",
    STATUS_AGUARDANDO: "Aguardando início",
    STATUS_EM_ANALISE: "Em análise",
    STATUS_EM_REPARO: "Em reparo",
    STATUS_FINALIZADO: "Finalizado",
    STATUS_CANCELADO: "Cancelado",
}

SOLICITACAO_PENDENTE = "pendente"
SOLICITACAO_ORCAMENTO_ENVIADO = "orcamento_enviado"
SOLICITACAO_ACEITA = "aceita"
SOLICITACAO_RECUSADA = "recusada"

# Status de um orçamento (Atendimento) enviado por um técnico pra um
# chamado — vários técnicos podem enviar orçamento pro mesmo chamado;
# quando o cliente escolhe um, os demais viram "recusado" automaticamente.
ORCAMENTO_PENDENTE = "pendente"
ORCAMENTO_ACEITO = "aceito"
ORCAMENTO_RECUSADO = "recusado"

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

# Seleção automática de técnicos (SelecionarTecnicosService): raio inicial
# de busca, dobrado sucessivamente até achar TECNICOS_SELECIONADOS_MIN
# candidatos ou estourar o raio máximo — a partir daí usa todos os técnicos
# cadastrados (com lat/long), mesmo fora do raio, pra nunca deixar um
# chamado sem nenhum técnico notificado se houver algum no sistema.
RAIO_SELECAO_TECNICOS_KM = 15
RAIO_SELECAO_TECNICOS_KM_MAXIMO = 240
TECNICOS_SELECIONADOS_MIN = 2
TECNICOS_SELECIONADOS_MAX = 3

# Pesos do score combinado (proximidade + avaliação + preço) — devem somar 1.
PESO_DISTANCIA = 0.5
PESO_AVALIACAO = 0.3
PESO_PRECO = 0.2
