# IFix — assistência técnica

O IFix conecta clientes e técnicos: o cliente abre um chamado, o sistema seleciona profissionais compatíveis, os técnicos enviam propostas e o cliente escolhe quem fará o reparo. A aplicação acompanha status, laudo, custos adicionais, garantia, avaliações, mensagens e notificações.

O backend usa Python, Flask e SQLAlchemy; o frontend usa HTML, CSS e JavaScript. A aplicação é hospedada na Vercel, os dados ficam no MySQL 8.4 do Aiven, os arquivos no Cloudinary e os e-mails são enviados pela Brevo. Não há dependência de Redis.

## Como explicar a arquitetura

É um monólito modular: uma aplicação Flask, organizada por assunto. As telas e a API usam o mesmo domínio, e o JavaScript conversa com a API por HTTP/JSON.

```text
Navegador: página HTML + JavaScript
    → frontend/js/api.js: envia a requisição e o token CSRF
    → routes.py: escolhe a rota e o método HTTP
    → controllers/: recebe os dados e monta a resposta
    → services/: valida permissão e aplica a regra de negócio
    → models/: representa e persiste os dados via SQLAlchemy
      ou repositories/: executa consultas com rotinas MySQL
    → Aiven MySQL: guarda os registros
    → serializers: convertem os dados em JSON explícito
    → JavaScript: atualiza a tela
```

Modelos tratam o CRUD pelo padrão Active Record: o objeto representa uma tabela e possui operações de persistência. Repositories concentram consultas SQL mais complexas, inclusive CALL de procedures. Services coordenam essas operações numa transação de negócio.

## Mapa de pastas

| Pasta | Responsabilidade | O que mostrar na apresentação |
|---|---|---|
| `backend/` | Aplicação Python, configuração e componentes compartilhados | `app.py` monta o Flask; `config.py` lê as variáveis da Vercel |
| `backend/modules/` | Módulos organizados por domínio | Cada módulo reúne suas rotas, controllers, services, models e repositories quando necessário |
| `backend/modules/usuarios/` | Cadastro, autenticação, conta, técnicos, diretório e disponibilidade | Login e perfil; distinção entre dados próprios e públicos |
| `backend/modules/servicos/` | Chamados, seleção de técnicos, solicitações, status, laudo, custos, garantia e histórico | Abertura de chamado e acompanhamento do reparo |
| `backend/modules/atendimentos/` | Propostas/orçamentos, escolha e avaliações | Comparação de até três propostas e avaliação após conclusão |
| `backend/modules/chat/` | Mensagens entre participantes do chamado | Autorização por participante e marcação de leitura |
| `backend/modules/notificacoes/` | Avisos internos e contagem de não lidos | Notificação criada junto com a operação de negócio |
| `backend/services/` | Integrações compartilhadas entre módulos | `email_service.py` envia e-mail pela Brevo depois do commit |
| `backend/database/` | Arquivos SQL da estrutura e das rotinas MySQL | `schema_mysql.sql` documenta 14 tabelas; `procedures.sql` contém 23 rotinas |
| `backend/certs/` | Local opcional para a CA pública | Na Vercel, a opção recomendada é MYSQL_SSL_CA_PEM, sem arquivo |
| `frontend/` | Interface entregue pelo Flask | `index.html` é a tela de entrada atual |
| `frontend/pages/` | Telas completas em HTML | Cadastro, cliente, técnico, perfil e diretório |
| `frontend/js/` | Interação das telas e comunicação com a API | `api.js`, `cliente-abrir-chamado.js`, `cliente-chamados.js` e `tecnico-home.js` |
| `frontend/css/` | Layout, componentes e temas | Arquivos de estilo do login/cadastro e dos painéis |
| `frontend/assets/` | Logotipo, ícones e imagens da interface | Recursos visuais estáticos, sem registros do banco |
| `frontend/uploads/` | Diretórios locais de apoio ao upload, ignorados no Git | Na implantação, os arquivos são enviados ao Cloudinary; a pasta não é armazenamento persistente |
| `frontend/views/` | HTML/CSS legados existentes no projeto | Não é a estrutura de templates usada pelo fluxo atual; as páginas atuais ficam em frontend/pages e frontend/index.html |
| `scripts/` | Ferramentas manuais de manutenção do schema e diagnóstico | Não são executadas no startup nem no deploy; não usar inicializador em banco já criado |
| `.vscode/` | Preferências locais do editor | Não contém a lógica do site |
| `.venv/` | Ambiente virtual local com dependências Python | Não é enviado ao Git; a Vercel instala backend/requirements.txt |
| `.git/` | Histórico e controle de versão local | Não é componente da aplicação em execução |

Dentro de cada módulo, `routes.py` registra URLs; `controllers/` traduz HTTP para chamadas de serviço; `services/` implementa casos de uso; `models/` define tabelas e relações; `repositories/` concentra consultas complexas. Arquivos `__init__.py` identificam os pacotes Python.

## Arquivos importantes do backend

| Arquivo | Função |
|---|---|
| `app.py` | Factory create_app, Flask-Login, blueprints, erros HTTP/JSON e arquivos estáticos; não cria tabelas |
| `page_routes.py` | Serve páginas e redireciona conforme a sessão/papel; logout protegido |
| `config.py` | DATABASE_URL, banco por ambiente, segredo, cookies, pool e tamanho máximo da requisição |
| `database.py` | Instância SQLAlchemy compartilhada pelos modelos |
| `database_errors.py` | Extrai código MySQL/categoria para logs sem expor SQL, senha ou URL |
| `model_registry.py` | Importa os 14 modelos para registrar os metadados |
| `mysql_tls.py` | Carrega CA e exige TLS com verificação de certificado e hostname |
| `serialization.py` | Normalização de Decimal/datas e contratos explícitos dos modelos para JSON |
| `query_serializers.py` | Projeta linhas das procedures nos formatos consumidos pelas telas |
| `sql_routines.py` | Executa CALL parametrizado usando a conexão da sessão e esgota os result sets |
| `transactions.py` | Uma transação por operação, rollback e locks FOR UPDATE |
| `access.py` | Verifica participantes antes de expor detalhes privados e reduz dados dos convidados |
| `http_security.py` | CSRF, isolamento de sessões e cabeçalhos HTTP; não usa serviço de rate limiting |
| `retention.py` | Bloqueia exclusão ORM de contas para preservar o histórico relacionado |
| `uploads.py` | Verifica extensão/MIME/conteúdo/tamanho e gera links protegidos de fotos de chamado |
| `business_time.py` | Obtém o horário no fuso de negócio configurável |
| `money.py` | Trabalha com Decimal para valores financeiros |
| `constants.py` | Centraliza status, modalidades, limites e percentuais do negócio |
| `decorators.py` | Restrições de papel em operações específicas |
| `exceptions.py` | Erros de negócio convertidos em respostas HTTP |
| `utils.py` | Validações e integração de upload com Cloudinary |
| `requirements.txt` | Dependências de execução do backend |
| `create_db.py` | Entrada legada para inicialização manual; não executar no banco existente |

Na raiz, `vercel.json` encaminha as requisições para backend/app.py e inclui os arquivos necessários. O `index.html` da raiz é um arquivo legado; a página servida por `/` é **frontend/index.html**, escolhida em backend/page_routes.py. `.gitignore` impede versionar ambiente virtual, segredos e uploads locais.

## Relações principais do banco

Existem 14 tabelas: usuarios, perfis_tecnicos, diplomas, janelas_disponibilidade, servicos, fotos_servicos, solicitacoes_tecnicos, historico_servicos, solicitacoes_aprovacao, acionamentos_garantia, atendimentos, avaliacoes, mensagens_chamado e notificacoes.

- Usuario é a conta. Pode abrir chamados como cliente e, quando técnico, possuir PerfilTecnico, diplomas e janelas de disponibilidade.
- Servico é o chamado: pertence ao cliente, pode ter técnico responsável, fotos, solicitações, propostas, histórico, mensagens, aprovações e acionamentos de garantia.
- Atendimento representa uma proposta/orçamento associado ao chamado e aos participantes.
- Avaliacao vincula chamado, autor e avaliado; a combinação serviço/autor é única.
- Notificacao pertence ao destinatário e pode apontar para um chamado.

As relações concretas estão nos arquivos models/ de cada módulo. As 23 rotinas MySQL são 11 funções escalares e 12 procedures para consultas, métricas e regras compartilhadas; elas retornam dados tabulares e a serialização JSON fica no Python.

## Roteiro para apresentar o código

### 1. Entrada e login

Mostre `frontend/index.html`, `frontend/js/login.js` e `frontend/js/api.js`. Depois abra `backend/modules/usuarios/routes.py`, `controllers/auth_controller.py` e `services/autenticar_usuario_service.py`. Explique que a senha é comparada ao hash, o Flask-Login mantém a sessão e o navegador recebe JSON com o destino do painel. Não mostre senhas/variáveis reais na apresentação.

### 2. Abrir um chamado

Mostre `frontend/pages/cliente-abrir-chamado.html` e seu JavaScript; siga para `backend/modules/servicos/routes.py`, `controllers/servico_controller.py` e `services/criar_servico_service.py`. Mostre o modelo `models/servico.py`. Explique validação, persistência e transação antes de falar do ranking.

### 3. Selecionar profissionais

Abra `backend/modules/servicos/services/selecionar_tecnicos_service.py`. O ranking usa distância Haversine, nota, preço e bônus de disponível agora; também respeita modalidade. Os dados vêm de `backend/modules/usuarios/repositories/usuario_repository.py`, que chama rotina em `backend/database/procedures.sql`. A seleção entrega IDs de técnicos, sem divulgar coordenadas privadas na resposta pública.

### 4. Comparar e escolher proposta

Mostre `backend/modules/atendimentos/services/enviar_orcamento_service.py`, `listar_orcamentos_service.py` e `escolher_orcamento_service.py`, junto de `frontend/js/cliente-chamados.js`. Explique o limite de três propostas, escolha pelo proprietário e transação com lock do chamado para evitar escolhas simultâneas.

### 5. Acompanhar e concluir

Mostre os serviços de status, laudo e aprovação em `backend/modules/servicos/services/`. O chamado só pode ser concluído conforme os requisitos de estado, laudo e custos autorizados. Mostre o histórico e a criação de notificações na mesma transação.

### 6. Avaliações, privacidade e integridade

Abra `backend/modules/atendimentos/models/avaliacao.py`, `services/avaliar_service.py`, `backend/access.py`, `backend/serialization.py` e `backend/transactions.py`. Explique avaliação única por autor, projeção pública mínima, autorização por recurso e rollback quando uma etapa falha.

### 7. Hospedagem

Finalize mostrando `vercel.json`, `backend/config.py`, `backend/mysql_tls.py` e as variáveis de ambiente usadas pela configuração. A Vercel executa Flask, que conecta ao Aiven com TLS; nenhum banco é criado ao iniciar.

## Funcionalidades e regras preservadas

| Funcionalidade | Como funciona |
|---|---|
| Cadastro e login | Contas com senha em hash e sessão protegida; o cliente pode acrescentar um perfil técnico à própria conta. |
| Abertura de chamado | O cliente descreve o problema, informa equipamento, modalidade e valor de referência e pode enviar fotos. |
| Seleção de técnicos | Ranking em Python combina distância, nota, preço e disponibilidade, respeitando modalidade; os selecionados recebem convites. |
| Fotos e propostas | O técnico convidado pode analisar as imagens e enviar valor/prazo. O cliente compara até três propostas e escolhe o responsável. |
| Urgência | Prazo de duas horas começa na escolha do técnico; adicional de 20% é informado, sem cobrança automática. |
| Modalidades | Loja, visita domiciliar ou suporte remoto, conforme a escolha do cliente e as opções atendidas pelo profissional. |
| Diretório e perfil público | Busca/filtros, dados profissionais, certificados e métricas; campos pessoais privados ficam fora da projeção pública. |
| Disponibilidade | Janelas semanais informativas e estado disponível agora válido por quatro horas. Não há agendamento automático. |
| Selo de especialista | Requer ao menos cinco chamados concluídos, nota média >=4,5 e certificado cadastrado. |
| Reparo e custos adicionais | O responsável registra status/laudo; custos extras precisam de aprovação do proprietário antes de elevar o teto. |
| Chat e notificações | Participantes conversam pelo chamado; avisos internos acompanham eventos e podem ser marcados como lidos. E-mail usa Brevo. |
| Histórico e reincidência | Linha do tempo do chamado e consulta de reparos do mesmo aparelho por cliente; uma causa repetida em dois registros gera o indicativo de reincidência. |
| Garantia e avaliações | Garantia opcional por dez dias após conclusão; avaliações entre os participantes atualizam métricas e alertas conforme os critérios do sistema. |

Garantia contratada dura dez dias após a conclusão. Pagamentos, gorjetas e reembolsos não possuem processamento financeiro automático; não apresentar o registro como cobrança efetivada. O selo usa critérios do sistema, sem auditoria documental externa.

## Colocar na Vercel

Configuração necessária no ambiente de Production:

1. Conferir DATABASE_URL de Production terminando em `/ifix` e MYSQL_SSL_CA_PEM completo, sem MYSQL_SSL_CA simultâneo.
2. Configurar SECRET_KEY nova de pelo menos 32 caracteres e preservar as credenciais Cloudinary/Brevo.
3. Enviar esta versão do código para a branch de produção do repositório conectado à Vercel, quando decidir publicar. Reimplantar um commit antigo não inclui estas alterações locais.
4. Conferir o build e validar login/cadastro, chamado/propostas, upload, notificações e histórico no site.

Não é necessário arquivo .env, Redis, seed ou inicializador. Os bancos já estão criados e devem ser preservados. Preview, se utilizado, exige configuração própria apontando a ifix_test; nunca compartilhe a URL Production com Preview.

## Manutenção e limites conhecidos

`python -m pip install -r backend/requirements.txt` instala as dependências locais. `scripts/gerar_schema.py --check` compara modelos e SQL offline, sem conectar ao Aiven. `scripts/validar_mysql.py` é diagnóstico manual somente leitura; não é executado automaticamente.

As suítes, os runners e os dados fictícios de demonstração foram removidos do projeto a pedido. Antes da remoção, a regressão local passou com 182 casos após retirar o limitador externo. Isso não comprova implantação ou concorrência real desta versão no Aiven; nenhum acesso remoto foi realizado nesta entrega.

Sem Redis, não há limitação automática de tentativas no backend. As proteções de autorização, CSRF, sessão, TLS, uploads e transações permanecem. O total de upload é 4 MiB por requisição. E-mail é best-effort depois do commit; foto de chamado usa Cloudinary authenticated, enquanto avatar/certificados são públicos.
