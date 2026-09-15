# iFix

Aplicação web para conexão entre clientes e técnicos de assistência técnica
(cadastro, login, abertura e acompanhamento de chamados, painel do técnico
com solicitações, aceite/recusa, atualização de status e histórico).

## Arquitetura

Backend em **Monólito Modular** (MVC + Services + Model no padrão Active
Record + Repository), separado em módulos de domínio — cada um com sua
própria camada de rotas, controllers, services, models e (quando precisa
de consultas com JOIN) repositories:

```
backend/
  app.py            # application factory: registra os módulos e cria o banco
  config.py, database.py, exceptions.py, utils.py, constants.py
  decorators.py      # @apenas_tecnico — autorização por papel, aplicada nos Controllers
  page_routes.py     # rotas de página HTML (login, cadastro, home de cliente/técnico...)

  services/           # Services compartilhados entre módulos (não pertencem a um domínio só)
    email_service.py    # envio de e-mail transacional via Brevo (API REST, sem SDK)

  database/
    procedures.sql     # procedures/functions em SQL chamadas pelas Repositories

  modules/
    usuarios/         # Usuario, PerfilTecnico, Diploma — cadastro, login, perfil técnico
    servicos/          # Servico (chamado), SolicitacaoTecnico, HistoricoServico,
                       # SolicitacaoAprovacao (custo adicional), AcionamentoGarantia
    atendimentos/       # Atendimento (orçamento), Avaliacao (avaliação mútua)
```

Erro de domínio levantado por um Service vira resposta HTTP pelo
`@app.errorhandler(DominioError)` registrado em `app.py` — Controllers novos
não precisam repetir `try/except DominioError`.

Fluxo padrão de uma requisição: `Route → Controller → Service.executar() →
Model` (CRUD simples) ou `→ Repository → procedure (SQL)` (consulta com
JOIN entre tabelas — a Repository só chama a procedure/function definida
em `backend/database/procedures.sql` via `db.session.execute(text(...))`,
nunca Model ou `db.session.query` diretamente).

`frontend/` é HTML/CSS/JavaScript puro (sem framework/build step), servido
diretamente pelo Flask como estático.

## Requisitos

- Python 3.10+
- pip
- Navegador moderno

## Como executar

### 1. Entrar na pasta do projeto

```bash
cd Ifix-main
```

### 2. Criar e ativar ambiente virtual

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências do backend

```bash
cd backend
pip install -r requirements.txt
```

### 4. Iniciar a API

```bash
python app.py
```

O projeto usa Postgres (Neon) como único banco — defina `DATABASE_URL` com a
connection string do Neon antes de rodar (`.venv` não sobe sem ela). Tabelas
e procedures são criadas/atualizadas automaticamente a cada início do app —
não precisa rodar nada à parte para isso.

A API ficará disponível em:

```text
http://127.0.0.1:5000
```

### 5. Abrir o frontend

O Flask já serve o frontend como estático — não precisa de outro servidor.
Acesse direto:

```text
http://127.0.0.1:5000
```

## Funcionalidades principais

- Cadastro de clientes e técnicos, com login/sessão (Flask-Login).
- **Seleção automática de técnicos**: ao abrir um chamado, o sistema calcula
  a distância (fórmula de Haversine, Python puro — sem PostGIS, IA ou
  serviço externo de geolocalização) entre o chamado e cada técnico
  cadastrado, combina isso com a avaliação média e o preço médio do
  técnico num score único, e já notifica os 2-3 melhores automaticamente
  (expandindo o raio de busca se não houver técnicos suficientes por
  perto, pra nunca deixar um chamado sem nenhum técnico notificado).
- **Geolocalização**: cadastro, conversão para técnico e abertura de
  chamado capturam a localização via `navigator.geolocation` do próprio
  navegador — usada só pro ranking acima, nunca enviada a serviço externo.
- **Orçamento**: em vez de aceitar um chamado direto, o técnico vê todos os
  detalhes (descrição, fotos, dados do cliente) e decide entre recusar ou
  enviar um orçamento (valor + prazo estimado + observações). Vários
  técnicos podem orçar o mesmo chamado.
- **Escolha do orçamento** (cliente): compara os orçamentos recebidos
  (técnico, valor, prazo, avaliação média) e escolhe um — isso atribui o
  técnico ao chamado, avança o status e recusa automaticamente os demais
  orçamentos/solicitações do mesmo chamado.
- **Painel do técnico**: solicitações pendentes com detalhe completo antes
  de decidir, lista dos próprios chamados com filtro por status e busca,
  barra de progresso animada, atualização de status e histórico — só o
  técnico escolhido pelo cliente tem acesso a essa ação.
- **Notificação por e-mail** (via Brevo): o cliente recebe um e-mail toda
  vez que o técnico atualiza o status do chamado, além da atualização
  aparecer no site.
- **Avaliação mútua**, com critérios diferentes por direção — cliente avalia
  o técnico por tempo de atendimento, honestidade e preço justo (alimenta
  o ranking automático acima); técnico avalia o comportamento e a
  colaboração do cliente durante o atendimento. Nota baixa de
  comportamento acumulada em 3 chamados diferentes suspende a conta do
  cliente automaticamente (não pode mais abrir chamados novos).
- **Abrir chamado** (cliente): formulário com tipo, categoria, modelo,
  título, descrição, limite máximo de gasto e até 5 fotos (5 MB cada).
- **Limite de gasto + autorização remota**: o valor informado na abertura é
  um teto de verdade (`servicos.valor_maximo_aprovado`), guardado separado
  do `preco_estimado` porque este último recebe o acréscimo da garantia.
  Achou um problema novo no meio do reparo, o técnico não executa por conta
  própria: abre um pedido com descrição e valor, e o cliente autoriza ou
  recusa de onde estiver. Aprovar soma o valor ao teto, então o limite
  continua valendo pro que vier depois. Só um pedido pendente por vez, e o
  chamado não pode ser finalizado enquanto houver pedido sem resposta.
- **Relatório técnico**: antes de finalizar, o técnico registra a causa do
  defeito (catálogo fechado em `constants.CAUSAS_DEFEITO`, pra permitir
  agregar reincidência depois), a explicação em linguagem de cliente e o
  que foi feito. O chamado não fecha sem isso.
- **Restrição de horário**: cliente e técnico definem a faixa do dia em que
  aceitam ser acionados. Fora dela o e-mail de aviso é suprimido, mas a
  solicitação continua sendo criada e aparecendo no painel — bloquear
  deixaria o chamado sem técnico por um motivo que é do técnico.
- **Acompanhar chamado** (cliente): lista dos próprios chamados, orçamentos
  recebidos, histórico de status e avaliação — tudo atualizado por polling.
- **Modos Cliente | Técnico** na mesma conta: técnico continua podendo abrir
  e acompanhar chamados como cliente.
- **Conversão de conta cliente → técnico**, com confirmação antes de abrir o
  formulário e checagem de e-mail já cadastrado.
- **Garantia** opcional na abertura do chamado (+7% sobre o valor, 10 dias):
  o prazo corre a partir de `servicos.finalizado_em`, gravado na primeira
  vez que o chamado é finalizado. Dentro dele, o cliente aciona a garantia
  escolhendo entre reembolso ou novo atendimento — neste caso um chamado
  novo é aberto na hora, gratuito e já atribuído ao mesmo técnico (sem
  passar de novo por seleção e orçamento). O chamado de garantia não tem
  garantia própria, senão ela se renovaria pra sempre.

> **Pagamento**: ponto de extensão já marcado no código (comentário em
> `constants.py`, antes de `STATUS_FINALIZADO`), mas a lógica de pagamento
> em si não foi implementada.

## Como testar o fluxo pelo navegador

1. Cadastre um técnico em `/cadastro` — **permita o acesso à localização**
   quando o navegador pedir (sem isso a conta fica de fora da seleção
   automática de técnicos).
2. Cadastre um cliente (outro navegador/aba anônima), também permitindo
   localização, e faça login.
3. Em **Abrir chamado**, preencha o formulário e envie — o chamado é
   criado com status `aberto` e a seleção automática já dispara sozinha,
   notificando os melhores técnicos por perto (sem precisar de nenhuma
   chamada manual à API).
4. No painel do técnico (`/tecnico/home`), a solicitação aparece em
   **Solicitações pendentes** — clique pra ver os detalhes completos do
   chamado e envie um orçamento (valor + prazo) ou recuse.
5. De volta como cliente, abra o chamado em **Meus chamados** — os
   orçamentos recebidos aparecem ali, com técnico, valor, prazo e
   avaliação; escolha um.
6. Como técnico, avance o status do chamado (só o técnico escolhido tem
   essa opção) — o cliente recebe um e-mail a cada atualização (se
   `BREVO_API_KEY` estiver configurada). A partir de **Em análise** aparecem
   dois cards novos no modal:
   - **Custo adicional**: peça autorização de um valor a mais. Volte como
     cliente (o card aparece em destaque no topo do chamado, em até 7s pelo
     polling) e autorize ou recuse — tentar finalizar antes disso é
     bloqueado.
   - **Relatório técnico**: escolha a causa do defeito e explique o que
     houve. Sem isso o chamado também não finaliza.
   Com os dois resolvidos, marque como **Finalizado**.
7. Com o chamado finalizado, cliente e técnico já podem se avaliar
   mutuamente pelos respectivos painéis. Se o chamado foi aberto com
   garantia, o cliente também vê o bloco **Garantia iFix** com os dias
   restantes e o botão de acionar (reembolso ou novo atendimento — este
   abre na hora um chamado gratuito no painel do mesmo técnico).
   Pra testar a expiração, mude `finalizado_em` do chamado no banco pra
   mais de 10 dias atrás: o acionamento passa a ser recusado.
8. Em **Restrições de horário** (home do cliente e painel do técnico),
   ajuste a faixa de atendimento — fora dela o e-mail de aviso de nova
   solicitação deixa de ser enviado, mas a solicitação continua aparecendo
   no painel.
9. Quem é técnico continua podendo abrir `/cliente/home` pelo chip **Cliente**
   e abrir chamados normalmente na mesma conta.

## Observações

- O backend usa Postgres (Neon) — defina a variável de ambiente
  `DATABASE_URL` com a connection string antes de rodar.
- Não há Alembic/Flask-Migrate configurado — mas `app.py` tem uma
  "migration leve" que roda a cada início do app: `db.create_all()` cria
  tabelas novas, duas funções (`_garantir_colunas_novas`/
  `_garantir_cascade_exclusao`) rodam `ALTER TABLE` pra colunas/constraints
  novas em tabelas que já existiam, e `_instalar_procedures()` aplica
  `backend/database/procedures.sql` (`CREATE OR REPLACE FUNCTION`,
  idempotente). Não precisa apagar o banco pra pegar uma Model ou procedure
  nova — só reiniciar o app.
- Upload de fotos (perfil, diplomas, chamados) usa Cloudinary — defina
  `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` e `CLOUDINARY_API_SECRET`.
- Notificação por e-mail (Brevo) é opcional: sem `BREVO_API_KEY` definida,
  o envio é pulado (com aviso no log), sem quebrar nada. Pra ativar,
  defina também `BREVO_SENDER_EMAIL` (precisa estar verificado na Brevo) e,
  opcionalmente, `BREVO_SENDER_NOME`.
- Para parar a aplicação, pressione Ctrl + C no terminal onde o servidor
  está rodando.
