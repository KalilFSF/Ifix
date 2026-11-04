# Contratos JSON e equivalência das rotinas

Os endpoints e métodos permanecem nos arquivos `backend/modules/*/routes.py`. O frontend continua usando `requisitar`, `obterJson`, `obterLista`, `enviarJson` e `enviarFormulario` em `frontend/js/api.js`.

## Formatos na raiz

| Endpoint/grupo | Retorno de sucesso |
|---|---|
| GET `/api/servicos`, `/api/servicos/meus`, `/api/tecnicos`, `/api/tecnicos/diretorio`, `/api/tecnico/solicitacoes`, `/api/atendimentos` | Array direto, inclusive `[]` |
| GET histórico do aparelho; histórico, orçamentos, avaliações, aprovações, garantia e mensagens de um chamado | Array direto |
| GET `/api/me` | Objeto de conta; perfil/diplomas e aliases profissionais quando técnico |
| GET `/api/servicos/<id>` | Objeto autorizado com `atendimentos` (todos para dono, próprios para responsável); convidado recebe objeto reduzido sem essa coleção |
| GET `/api/csrf` | `{csrf_token, max_request_bytes}`; token de sessão e limite total para o frontend |
| GET `/api/tecnicos/<id>/perfil-publico` | Objeto público com certificados, janelas e últimas avaliações |
| GET `/api/notificacoes` | `{notificacoes: [], nao_lidas: 0}` |
| GET `/api/mensagens/nao-lidas` | Mapa de IDs de serviço para quantidade; chaves JSON são strings |
| GET `/api/tecnico/perfil` | `{ok: true, usuario, perfil, diplomas}` |
| GET `/api/tecnico/disponibilidade` | `{ok: true, janelas, disponivel_agora}` |
| Login e cadastro | `{ok: true, redirect}` |
| Demais escritas | Envelope original `ok: true`, com serviço/atendimento/avaliação/mensagem/aprovação/acionamento ou contagem correspondente |

Erros de domínio mantêm `{ok: false, erro, ...extras}` e status HTTP anteriores. Foram preservados 201 no envio de mensagem, criação de aprovação e acionamento de garantia; as outras escritas conservam os códigos existentes. GET /logout apresenta confirmação HTML; POST /logout exige CSRF, encerra sessão e redireciona. Os links da interface são interceptados pelo cliente para POST protegido.

Não foi introduzido `{dados: [...]}` na API. `obterLista` depende de array na raiz. No frontend, `resultado.dados` é parte do wrapper JavaScript, não um novo envelope do servidor.

## Tipos e recortes

- Dinheiro e métricas são números JSON; jamais strings Decimal. Isso preserva chamadas `.toFixed()` existentes na interface.
- IDs/contagens são inteiros; MySQL BOOL/TINYINT de resultados SQL é convertido explicitamente nos campos booleanos dos serializers.
- Datas de calendário usam `YYYY-MM-DD`; timestamps usam ISO 8601 UTC com `+00:00`.
- Ausência é `null`; coleção sem registros é `[]`. Não substituir ambos por strings vazias.
- Fotos preservam `id`, `arquivo`, `url`, `enviado_em`; para novos uploads de chamado, arquivo/url são endpoints autenticados da API, sem referência ou assinatura Cloudinary.
- Painel de serviço inclui participantes e contadores de solicitações, propostas, avaliações, mensagens não lidas e aprovações pendentes.
- Convite pendente inclui serviço em allowlist reduzida com fotos do problema para preparar o orçamento; sem coordenadas, laudo, contatos ou atendimentos alheios. Cliente irmão somente id/nome/foto. Fotos novas usam URL autenticada, disponível ao convidado legítimo enquanto aberto e sem responsável definido.
- Proposta inclui técnico com nome, telefone, foto, nota, total de avaliações, selo, disponibilidade, concluídos e taxa de sucesso.
- Perfil público inclui `preco_medio` (enquanto perfil próprio usa `valor_medio`), três médias de critérios, certificados, janelas e cinco avaliações recentes com primeiro nome do autor.
- Preservada diferença existente: POST de mensagem não inclui `autor_foto`; GET inclui. Não houve expansão silenciosa desse contrato.
- Conta própria mantém CPF; diretório e perfil público não expõem CPF, e-mail, telefone, senha ou coordenadas. O endpoint legado `/api/tecnicos` também usa o diretório público e sua allowlist.

## Mapeamento das 23 funções anteriores

Todas as funcionalidades foram adaptadas. Mantivemos os nomes `fn_` para facilitar rastreio; doze agora são **procedures**, chamadas por CALL.

| Nome | Destino MySQL |
|---|---|
| fn_garantia_dias | Função escalar: 10 dias |
| fn_garantia_expira_em | Função escalar com DATE_ADD |
| fn_rotulo_causa_defeito | Função escalar CASE; serializers usam o catálogo Python |
| fn_urgencia_taxa_percentual | Função escalar: 20 |
| fn_rotulo_modalidade | Função escalar CASE; serializers usam o catálogo Python |
| fn_modalidades_json | Função escalar retorna CSV, apesar do nome legado; serializer gera a lista |
| fn_tecnico_disponivel_agora | Função escalar com UTC_TIMESTAMP(6) |
| fn_tecnico_atendimentos_concluidos | Função escalar COUNT |
| fn_tecnico_taxa_sucesso | Função escalar de agregação condicional |
| fn_tecnico_tempo_medio_horas | Função escalar com subconsulta agrupada e TIMESTAMPDIFF |
| fn_tecnico_eh_especialista | Função escalar: cinco concluídos, nota ≥4,5 e um certificado |
| fn_listar_tecnicos_com_perfil | Procedure legada sem uso no app; fonte local pública, definição remota anterior preservada |
| fn_listar_tecnicos_para_ranking | Procedure: candidatos com coordenadas; ranking permanece no Python |
| fn_listar_orcamentos_por_servico | Procedure: proposta e colunas do técnico |
| fn_listar_aprovacoes_por_servico | Procedure: aprovação e nome do técnico |
| fn_listar_servicos_participante | Procedure: serviços + segundo result set de fotos |
| fn_listar_solicitacoes_pendentes | Procedure: solicitações/detalhes + fotos |
| fn_listar_mensagens_chamado | Procedure: mensagens filtradas por ID incremental |
| fn_contar_mensagens_nao_lidas | Procedure: contagem por chamado escopada ao participante |
| fn_listar_avaliacoes_por_servico | Procedure: avaliações com nomes |
| fn_listar_tecnicos_diretorio | Procedure: LIKE com collation explícita, FIND_IN_SET e filtros |
| fn_perfil_publico_tecnico | Procedure: perfil, certificados, janelas e avaliações em quatro result sets |
| fn_historico_aparelho | Procedure: normalização de caixa/espaços, escopo cliente, exclusão e limite dez |

Ordenações e limites foram mantidos. As rotinas e tabelas usam collation explícita `utf8mb4_0900_as_ci`, evitando depender da collation padrão do schema Aiven. Nenhuma usa JSON_OBJECT/JSON_ARRAYAGG como substituto da camada Python.

A revisão local foi verificada antes de retirar os arquivos de teste a pedido. Validação remota desta versão continua manual; detalhes operacionais em PRODUCAO.md.


## Alterações explícitas de segurança

Escritas exigem token X-CSRF-Token ou campo csrf_token associado à sessão; Origin diferente é recusada. Login gira sessão/token e o cliente descarta o token anterior. Nenhum token é enviado a domínios externos. Faltas/erros de token retornam 403; Conflitos de concorrência podem retornar 409; não há limitador de tentativas no backend. Erros genéricos de API também usam ok:false/erro, sem traceback. Páginas normais conservam HTML.

As mudanças de projeção de convites/legado e dos links de fotos são intencionais para privacidade; não há envelope novo nas respostas de sucesso. Diretório e perfil continuam públicos nos campos profissionais; foto e certificados são públicos, com aviso na interface. Campos pessoais da própria conta continuam restritos à sessão do titular. Ver RELATORIO_SEGURANCA.md para limites e pendências externas.
