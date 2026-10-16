# Valores válidos de status de um Servico (chamado), centralizados aqui pra
# não ficar espalhado como string livre entre model/service/controller.

STATUS_ABERTO = "aberto"
STATUS_AGUARDANDO = "aguardando"
STATUS_EM_ANALISE = "em_analise"
STATUS_EM_REPARO = "em_reparo"
# PAGAMENTO: entraria aqui — antes de permitir a transição pra
# STATUS_FINALIZADO (ver AtualizarStatusServicoService), exigindo
# confirmação de pagamento. Não implementado nesta etapa: técnico e cliente
# podem concluir o chamado depois que os requisitos do reparo forem atendidos.
STATUS_FINALIZADO = "finalizado"
STATUS_CANCELADO = "cancelado"

# Quem pode definir o quê em PATCH /api/servicos/<id>/status.
#
# O técnico conduz o reparo e pode concluí-lo depois de registrar o laudo e
# resolver as autorizações pendentes. O cliente também pode confirmar a
# conclusão. Nos dois casos, o prazo da garantia começa em
# servicos.finalizado_em.
#
# "aberto" fica de fora dos dois: é o estado inicial, antes de qualquer
# técnico aceitar, e não se volta pra ele.
STATUS_TECNICO_CHOICES = (
    STATUS_AGUARDANDO,
    STATUS_EM_ANALISE,
    STATUS_EM_REPARO,
    STATUS_FINALIZADO,
)

STATUS_CLIENTE_CHOICES = (STATUS_FINALIZADO,)

# O cliente só confirma a conclusão a partir daqui: finalizar um chamado que
# nem chegou a entrar em reparo não descreve nada que aconteceu.
STATUS_MINIMO_PARA_FINALIZAR = STATUS_EM_REPARO

# Estados de onde não se sai. Sem essa trava, "finalizado" -> "em_reparo"
# era aceito e o chamado voltava a andar com finalizado_em já gravado — ou
# seja, com a garantia correndo em paralelo.
STATUS_TERMINAIS = (STATUS_FINALIZADO, STATUS_CANCELADO)

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
# 5 MB por foto (era 2 MB). Atenção: Serverless Functions do Vercel têm um
# limite de payload da própria plataforma (historicamente ~4,5 MB por
# request, fora do controle do Flask) — com várias fotos grandes juntas
# nesse limite pode ser atingido antes mesmo de chegar no MAX_CONTENT_LENGTH
# configurado em config.py. Se isso acontecer em produção, a saída correta
# é subir a foto direto do navegador pro Cloudinary (upload assinado) em
# vez de passar pelo backend, e não só aumentar esse número de novo.
MAX_BYTES_FOTO_CHAMADO = 5 * 1024 * 1024

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
#
# Os valores subiram (15 -> 40 km inicial, 240 -> 600 km de teto) porque a
# expansão automática só dispara com MENOS de TECNICOS_SELECIONADOS_MIN
# candidatos: com dois técnicos a 10 km o raio nunca crescia, e um terceiro
# a 16 km — possivelmente melhor avaliado e mais barato — ficava de fora.
# Um raio inicial maior é o que dá ao score de fato o que comparar.
RAIO_SELECAO_TECNICOS_KM = 40
RAIO_SELECAO_TECNICOS_KM_MAXIMO = 600

# Teto do botão "Ampliar busca" (AmpliarBuscaTecnicosService), que o cliente
# aciona quando ninguém respondeu. Vai além do teto automático de propósito:
# é uma escolha explícita dele de aceitar um técnico mais distante.
RAIO_AMPLIACAO_MAXIMO_KM = 1200

# Depois deste tempo sem nenhum orçamento, o painel do cliente passa a
# sugerir ativamente ampliar a busca (o front compara com criado_em).
MINUTOS_PARA_SUGERIR_AMPLIAR_BUSCA = 15
TECNICOS_SELECIONADOS_MIN = 2
TECNICOS_SELECIONADOS_MAX = 3

# Pesos do score combinado (proximidade + avaliação + preço) — devem somar 1.
PESO_DISTANCIA = 0.5
PESO_AVALIACAO = 0.3
PESO_PRECO = 0.2

# Penalidade por comportamento (funcionalidade 4 do projeto): nota de
# comportamento/colaboração <= este valor conta como "alerta" quando um
# técnico avalia um cliente; ao acumular LIMITE_ALERTAS_COMPORTAMENTO
# alertas, a conta do cliente é suspensa automaticamente (ver
# Usuario.registrar_alerta_comportamento / AvaliarService).
NOTA_COMPORTAMENTO_LIMITE = 2
LIMITE_ALERTAS_COMPORTAMENTO = 3

# Relatório técnico (funcionalidade 8): causa do defeito identificada pelo
# técnico. É um catálogo fechado, e não texto livre, de propósito — a
# funcionalidade 10 (alerta de reincidência por modelo de aparelho) precisa
# agrupar defeitos iguais, o que só dá pra fazer com valor padronizado. O
# detalhe em texto livre fica no laudo, ao lado.
CAUSA_COMPONENTE_DEFEITUOSO = "componente_defeituoso"
CAUSA_SUPERAQUECIMENTO = "superaquecimento"
CAUSA_DANO_POR_LIQUIDO = "dano_por_liquido"
CAUSA_SOFTWARE_CORROMPIDO = "software_corrompido"
CAUSA_MALWARE = "malware"
CAUSA_DESGASTE_NATURAL = "desgaste_natural"
CAUSA_MAU_USO = "mau_uso"
CAUSA_OUTRO = "outro"

CAUSAS_DEFEITO = (
    CAUSA_COMPONENTE_DEFEITUOSO,
    CAUSA_SUPERAQUECIMENTO,
    CAUSA_DANO_POR_LIQUIDO,
    CAUSA_SOFTWARE_CORROMPIDO,
    CAUSA_MALWARE,
    CAUSA_DESGASTE_NATURAL,
    CAUSA_MAU_USO,
    CAUSA_OUTRO,
)

CAUSAS_DEFEITO_LABELS = {
    CAUSA_COMPONENTE_DEFEITUOSO: "Componente defeituoso",
    CAUSA_SUPERAQUECIMENTO: "Superaquecimento",
    CAUSA_DANO_POR_LIQUIDO: "Dano por líquido",
    CAUSA_SOFTWARE_CORROMPIDO: "Software corrompido",
    CAUSA_MALWARE: "Vírus / malware",
    CAUSA_DESGASTE_NATURAL: "Desgaste natural",
    CAUSA_MAU_USO: "Mau uso",
    CAUSA_OUTRO: "Outro",
}

# Tamanho mínimo do laudo, pra evitar "ok"/"consertado" como explicação —
# a funcionalidade pede um relatório que o cliente leigo entenda.
MIN_CARACTERES_LAUDO = 20

# Restrição de horário de atendimento (funcionalidade 9): faixa em que o
# usuário aceita ser contatado/atendido, guardada como "HH:MM" (string) em
# vez de Time — é o formato que o <input type="time"> do front manda e lê,
# e evita qualquer conversão de fuso horário no caminho.
HORARIO_ATENDIMENTO_PADRAO_INICIO = "08:00"
HORARIO_ATENDIMENTO_PADRAO_FIM = "18:00"

# Autorização de custo adicional (funcionalidades 6 e 7): quando o técnico
# encontra um problema novo durante o reparo, ele não executa nada por conta
# própria — abre um pedido de autorização com o valor a mais, e o cliente
# aprova ou recusa remotamente. Enquanto houver pedido pendente, o chamado
# não pode ser finalizado (ver AtualizarStatusServicoService).
APROVACAO_PENDENTE = "pendente"
APROVACAO_APROVADA = "aprovada"
APROVACAO_RECUSADA = "recusada"
APROVACAO_STATUS_RESPOSTA = (APROVACAO_APROVADA, APROVACAO_RECUSADA)

# Tamanho mínimo da descrição do problema novo, pelo mesmo motivo do laudo:
# o cliente precisa entender o que está autorizando.
MIN_CARACTERES_DESCRICAO_APROVACAO = 15

# Acionamento da garantia (funcionalidade 2): se o problema voltar dentro de
# GARANTIA_DIAS após a finalização, o cliente escolhe entre ser reembolsado
# ou receber um novo atendimento gratuito com o mesmo técnico.
GARANTIA_TIPO_REEMBOLSO = "reembolso"
GARANTIA_TIPO_NOVO_ATENDIMENTO = "novo_atendimento"
GARANTIA_TIPOS = (GARANTIA_TIPO_REEMBOLSO, GARANTIA_TIPO_NOVO_ATENDIMENTO)

GARANTIA_TIPOS_LABELS = {
    GARANTIA_TIPO_REEMBOLSO: "Reembolso",
    GARANTIA_TIPO_NOVO_ATENDIMENTO: "Novo atendimento gratuito",
}

GARANTIA_STATUS_PENDENTE = "pendente"
GARANTIA_STATUS_APROVADO = "aprovado"
GARANTIA_STATUS_RECUSADO = "recusado"
GARANTIA_STATUS_CONCLUIDO = "concluido"

# Mesma razão do laudo e da aprovação: o técnico precisa entender o que
# voltou a acontecer pra saber se é o mesmo defeito.
MIN_CARACTERES_DESCRICAO_GARANTIA = 15

# Atendimento de urgência (funcionalidade 1): o cliente marca na abertura e
# paga uma taxa sobre o orçamento escolhido; o técnico tem URGENCIA_PRAZO_HORAS
# a partir do momento em que é escolhido. Como a taxa da garantia, ela é só
# informada e registrada — o iFix ainda não cobra — e não entra no teto de
# gasto. Espelhada em fn_urgencia_taxa_percentual (procedures.sql).
URGENCIA_TAXA_PERCENTUAL = 20
URGENCIA_PRAZO_HORAS = 2

# Modalidade de atendimento (funcionalidade 2): onde o reparo acontece. O
# cliente escolhe na abertura; o técnico diz em /perfil quais ele atende.
MODALIDADE_LOJA = "loja"
MODALIDADE_DOMICILIO = "domicilio"
MODALIDADE_REMOTO = "remoto"
MODALIDADES = (MODALIDADE_LOJA, MODALIDADE_DOMICILIO, MODALIDADE_REMOTO)

MODALIDADES_LABELS = {
    MODALIDADE_LOJA: "Na loja do técnico",
    MODALIDADE_DOMICILIO: "Visita domiciliar",
    MODALIDADE_REMOTO: "Suporte remoto",
}

# Janelas de disponibilidade do técnico (funcionalidade 3): dia da semana no
# padrão do Python (0 = segunda ... 6 = domingo), faixa em "HH:MM" pelo mesmo
# motivo de HORARIO_ATENDIMENTO_PADRAO_*.
DIAS_SEMANA_LABELS = (
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo",
)
MAX_JANELAS_DISPONIBILIDADE = 14

# "Disponível agora" (funcionalidade 6): o técnico liga o status e ele vale
# por este tempo. Sem prazo, quem esquece de desligar continuaria aparecendo
# como disponível horas depois de ter saído do ar.
DISPONIVEL_AGORA_VALIDADE_HORAS = 4

# Pontos somados ao score de seleção (SelecionarTecnicosService) de quem está
# "disponível agora" — pesa pouco: desempata, não passa por cima de distância,
# nota e preço.
BONUS_DISPONIVEL_AGORA = 0.05

# Selo "Especialista verificado" (funcionalidade 7): regra automática, sem
# aprovação manual. Espelhada em fn_tecnico_eh_especialista (procedures.sql).
SELO_MIN_ATENDIMENTOS = 5
SELO_NOTA_MINIMA = 4.5
SELO_MIN_CERTIFICADOS = 1

# Comparativo de propostas (funcionalidade 8): quantos orçamentos um chamado
# recebe. Passado disso o cliente teria o trabalho de comparar quem já não
# vai ser escolhido.
MAX_ORCAMENTOS_POR_CHAMADO = 3

# Notificações no app (funcionalidade 9).
NOTIFICACAO_NOVA_SOLICITACAO = "nova_solicitacao"
NOTIFICACAO_ORCAMENTO_RECEBIDO = "orcamento_recebido"
NOTIFICACAO_TECNICO_DEFINIDO = "tecnico_definido"
NOTIFICACAO_STATUS = "status_atualizado"
NOTIFICACAO_AUTORIZACAO_PEDIDA = "autorizacao_pedida"
NOTIFICACAO_AUTORIZACAO_RESPONDIDA = "autorizacao_respondida"
MAX_NOTIFICACOES_LISTADAS = 30

# Histórico do aparelho (funcionalidade 10): tamanho mínimo do modelo pra
# buscar chamados anteriores — "a" casaria com tudo.
MIN_CARACTERES_MODELO_HISTORICO = 2
