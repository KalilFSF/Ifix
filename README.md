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
  page_routes.py     # rotas de página HTML (login, cadastro, home de cliente/técnico...)

  modules/
    usuarios/         # Usuario, PerfilTecnico, Diploma — cadastro, login, perfil técnico
    servicos/          # Servico (chamado), SolicitacaoTecnico, HistoricoServico
    atendimentos/       # Atendimento (orçamento ligado a um chamado)
```

Fluxo padrão de uma requisição: `Route → Controller → Service.executar() →
Model` (CRUD simples) ou `→ Repository → Model` (consulta com JOIN entre
tabelas). Os materiais de referência da disciplina usados como base para essa
arquitetura estão em [`arquitetura/`](arquitetura/).

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

O banco SQLite (`backend/database/ifix.db`) é criado automaticamente na
primeira execução — não precisa rodar nada à parte para isso.

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
- **Painel do técnico**: solicitações pendentes (aceitar/recusar), lista dos
  próprios chamados com filtro por status e busca, detalhe do chamado com
  barra de progresso animada, atualização de status e histórico.
- **Acompanhar chamado** (cliente): lista dos próprios chamados e histórico
  de status, atualizado por polling.
- **Conversão de conta cliente → técnico**, com confirmação antes de abrir o
  formulário e checagem de e-mail já cadastrado.
- Registro de atendimentos (orçamento) ligados a um chamado.

> A abertura de chamado pelo cliente (formulário "Abrir chamado") e a
> distribuição automática para técnicos (via n8n/IA) ainda não têm UI —
> ficam para uma etapa futura. Por enquanto, um chamado é criado e ofertado
> a um técnico diretamente pela API (`POST /api/servicos` e
> `POST /api/servicos/<id>/solicitar-tecnicos`).

## Como testar o fluxo pelo navegador

1. Acesse `/cadastro`, escolha **Cliente**, preencha os dados e cadastre.
2. Faça login com esse cliente e você cai na home (`/cliente/home`).
3. Abra `/cadastro` de novo, escolha **Técnico** e cadastre outra conta.
4. Faça login com o técnico — você cai no painel (`/tecnico/home`), que
   começa vazio (sem chamado nenhum ainda).
5. Como a abertura de chamado pelo cliente ainda não tem tela, crie um
   chamado e ofereça a esse técnico diretamente pela API (autenticado como
   o cliente):

   ```bash
   curl -X POST http://127.0.0.1:5000/api/servicos \
     -H "Content-Type: application/json" \
     --cookie "session=<cookie do cliente logado>" \
     -d '{"titulo":"Notebook não liga","descricao":"...","categoria":"Hardware","preco_estimado":300}'

   curl -X POST http://127.0.0.1:5000/api/servicos/<id>/solicitar-tecnicos \
     -H "Content-Type: application/json" \
     --cookie "session=<cookie do cliente logado>" \
     -d '{"tecnico_ids":[<id do técnico>]}'
   ```

6. No navegador logado como técnico, o chamado aparece em "Solicitações
   pendentes" — aceite, avance o status pelas etapas (Aguardando → Em
   análise → Em reparo → Finalizado) e acompanhe a barra de progresso e o
   histórico atualizando.
7. Logado como o cliente em "Meus chamados", a mesma atualização de status
   aparece (via polling), com o histórico completo.

## Observações

- O backend usa SQLite por padrão; a connection string pode ser trocada
  via a variável de ambiente `DATABASE_URL`.
- O banco é criado automaticamente na pasta `backend/database/`.
- Não há uma ferramenta de migration (Alembic/Flask-Migrate) configurada —
  ao mudar uma Model, apague `backend/database/ifix.db` e deixe o app
  recriar do zero, ou rode o `ALTER TABLE` manualmente.
- Para parar a aplicação, pressione Ctrl + C no terminal onde o servidor
  está rodando.
