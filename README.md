# iFix

Aplicação web para conexão entre clientes e técnicos de assistência técnica.

## Estrutura do projeto

- backend/: API Flask com autenticação, cadastro, serviços e atendimentos
- frontend/: interface web em HTML/CSS/JavaScript

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

### 4. Criar o banco de dados

```bash
python create_db.py
```

### 5. Iniciar a API

```bash
python app.py
```

A API ficará disponível em:

```text
http://127.0.0.1:5000
```

### 6. Abrir o frontend

Abra o arquivo abaixo no navegador:

```text
frontend/index.html
```

Ou, se preferir servir os arquivos estáticos por um servidor local, pode usar:

```bash
cd frontend
python -m http.server 8000
```

Depois acesse:

```text
http://127.0.0.1:8000
```

## Funcionalidades principais

- Cadastro de clientes e técnicos
- Login no sistema
- Criação e visualização de serviços
- Aceite de serviços por técnicos
- Visualização de atendimentos

## Como testar o fluxo completo

### 1. Cadastrar um cliente

- Acesse a página de cadastro em frontend/pages/cadastro.html.
- Selecione a opção Cliente.
- Preencha os dados obrigatórios e clique em Cadastrar.
- O sistema deve criar o usuário e redirecionar para a tela de login.

### 2. Fazer login como cliente

- Acesse frontend/index.html.
- Informe o email e a senha cadastrados.
- Após o login, você será direcionado para a home do cliente.

### 3. Criar um serviço

- Na home do cliente, preencha os campos do formulário de serviço.
- Clique em Criar serviço.
- O serviço deve aparecer na lista de serviços do cliente.

### 4. Cadastrar um técnico

- Abra novamente a página de cadastro.
- Selecione a opção Técnico.
- Preencha os dados obrigatórios e cadastre a conta.

### 5. Fazer login como técnico

- Faça login com o email e senha do técnico.
- Após o login, você será direcionado para a home do técnico.

### 6. Aceitar um serviço

- Na home do técnico, verifique os serviços abertos.
- Clique em Aceitar para assumir um serviço.
- O status do serviço deve mudar para aceito.

### 7. Verificar atendimentos

- Volte para a home do cliente ou do técnico.
- Confira a lista de atendimentos para validar o fluxo completo.

## Observações

- O backend usa SQLite por padrão.
- O banco é criado automaticamente na pasta backend/database/.
- Para parar a aplicação, pressione Ctrl + C no terminal onde o servidor está rodando.
