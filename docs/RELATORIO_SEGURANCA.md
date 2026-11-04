# Revisão final — configuração sem Redis

O projeto foi ajustado para Flask na Vercel e MySQL no Aiven. A integração Redis, sua validação de startup, seus limites e variáveis de configuração foram removidos. CSRF, sessão, autorização, TLS, serializers, transações e validação de uploads permanecem.

Antes da retirada dos arquivos de teste solicitada pelo responsável, a regressão local sem rede passou com **182 passed, 56 deselected**. Os 56 casos MySQL não foram executados. Os testes, seus runners, dependências exclusivas de desenvolvimento e seed fictício foram então removidos; nenhum registro remoto foi apagado.

README.md agora descreve cada pasta/camada, os arquivos compartilhados, relações principais, funcionalidades e um roteiro para apresentar o código. docs/PRODUCAO.md contém o passo a passo de configuração e publicação manual. docs/SEGURANCA_PENDENTE.md registra limites, incluindo ausência de rate limiting e validação remota pendente.

Arquivos de runtime alterados nesta etapa: backend/config.py e backend/http_security.py. O modo demo deixou de ser aceito na configuração; Production/local usam ifix e Preview continua isolado em ifix_test. As ferramentas de diagnóstico/manutenção do schema foram preservadas por serem independentes da suíte. O banco existente não deve ser inicializado novamente.

Não houve conexão ao Aiven, DDL/DML remoto, alteração de variáveis Vercel, commit, push ou deploy. O vercel.json foi apenas inspecionado nesta etapa. Os testes locais não aprovam automaticamente a implantação, as integrações externas ou a concorrência real desta versão.

Guia para apresentação: [../README.md](../README.md). Guia para implantação: [PRODUCAO.md](PRODUCAO.md).

Verificação final após a limpeza: sintaxe Python e JSON válida, schema correspondente aos 14 modelos, git diff --check sem erros e startup com configuração Production sem Redis aprovado localmente. Login HTML, CSS, JavaScript e /api/csrf responderam 200; escrita sem token respondeu 403. A rede estava bloqueada e nenhuma conexão foi tentada. A suíte removida não foi recriada.

Correção posterior: as fotos do problema voltaram ao payload de solicitações e detalhes para técnicos convidados, pois são necessárias para elaborar o orçamento. O endpoint autenticado das fotos aceita o mesmo convite válido enquanto o chamado está aberto e sem responsável escolhido; recusa, cancelamento ou escolha de outro profissional revogam esse acesso. O proprietário e o responsável mantêm acesso. Nenhum contato privado, coordenada, laudo ou orçamento alheio foi acrescentado à projeção do convidado. A interface já renderizava a coleção fotos, portanto não exigiu alteração. Verificação em memória, sem arquivos de teste: lista/detalhes com fotos corretas, isolamento entre chamados, acesso do dono/convidado/responsável e bloqueio de anônimos/estranhos/convites revogados. SQLite em memória, transporte Cloudinary simulado e rede bloqueada; nenhum acesso ao Aiven ou deploy.


## Revisão para estudo e quebra de texto do perfil

A especialização sem espaços ultrapassava a largura do modal. dashboard.css agora usa overflow-wrap:anywhere, min-width:0 e colunas minmax(0,1fr), com uma coluna no breakpoint estreito. Especializações e experiências usam white-space:pre-wrap, preservando Enter sem perder o escape HTML. Não houve truncamento nem alteração de dado/coluna SQL.

Foram acrescentados cabeçalhos explicativos a módulos Python, comentários nas telas/arquivos JavaScript e finalidade de cada rotina SQL. A documentação de logout foi alinhada ao POST com CSRF. Os nomes abreviados pp… no componente de perfil foram substituídos por formatar/renderizar…PerfilPublico; variáveis de fragmento HTML foram esclarecidas. Em transactions.py, KEY passou a TRANSACTION_STATE_KEY; em sql_routines.py, nomes locais passaram a result_sets, column_names e dbapi_connection. Interfaces externas, rotas, tabelas, nomes das rotinas e chaves JSON foram preservados.

O novo GUIA_COMPLETO_DO_PROJETO.md possui mais de 6 mil linhas e cataloga 204 arquivos de projeto, 67 declarações de rota, 14 modelos com colunas/relações e 23 rotinas SQL. Inclui fluxo completo de cada funcionalidade, inventário de funções/métodos, glossário, roteiro de estudo e perguntas/respostas. Metadados, dependências, segredos e uploads pessoais não foram enumerados internamente nem lidos. README principal e frontend/readme.md apontam para esse guia; créditos da equipe foram preservados.

Verificações concluídas:

- Chrome headless com arquivos temporários locais: o controle sem correção ultrapassou 11 mil pixels; com a correção o conteúdo ficou limitado ao modal. Larguras efetivas aproximadas de viewport: 1084 e 500 pixels; a execução estreita foi limitada pelo próprio navegador, sem alegação de teste em celular físico. Confirmados pre-wrap e grade estreita de uma coluna.
- 138 arquivos Python com AST válido e 21 JavaScript aprovados por node --check.
- Renderização em Node com texto longo, Enter e tentativa de HTML: conteúdo preservado e escapado, nomes novos funcionando.
- 204 entradas únicas no catálogo e 285 links de arquivo locais conferidos.
- Startup/CSRF, commit/rollback de transações aninhadas e callbacks em SQLite em memória; fuso America/Sao_Paulo conferido com instante conhecido.
- CALL com cursor simulado: result sets drenados e conexão da sessão não fechada/confirmada pelo helper.
- Parser offline continua reconhecendo as 23 rotinas depois dos comentários; gerar_schema.py --check confirmou correspondência dos 14 modelos. Nenhum SQL foi enviado ao Aiven.
- git diff --check sem erros. Sem novos arquivos de suíte, acesso remoto, DDL/DML remoto, alteração Vercel, commit, push ou deploy.
