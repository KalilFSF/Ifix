# Produção — Flask na Vercel e MySQL no Aiven

O código usa MySQL, sem Redis ou serviço adicional de rate limiting. O banco ifix já tem as tabelas/rotinas; não executar inicializador, seed, reset ou cópia de ifix_test. O frontend e o backend são entregues pela mesma aplicação Flask.

## 1. Configurar variáveis no painel Vercel

Abra o projeto ifix-main → Settings → Environment Variables. Para cada valor de produção, selecione **Production**.

| Variável | Valor |
|---|---|
| DATABASE_URL | `mysql+pymysql://avnadmin:SENHA_CODIFICADA@mysql-2a716d16-ifixsolucoesltdaprojeto.f.aivencloud.com:27931/ifix` |
| MYSQL_SSL_CA_PEM | Certificado CA completo do Aiven com BEGIN/END e quebras de linha reais |
| SECRET_KEY | Novo segredo aleatório de pelo menos 32 caracteres, diferente do usado com Neon |
| CLOUDINARY_CLOUD_NAME | Nome da conta Cloudinary |
| CLOUDINARY_API_KEY | Chave da API Cloudinary |
| CLOUDINARY_API_SECRET | Segredo da API Cloudinary |
| BREVO_API_KEY | Chave de envio Brevo |
| BREVO_SENDER_EMAIL | E-mail do remetente verificado |
| BREVO_SENDER_NOME | Nome de exibição do remetente; opcional, padrão iFix |
| BUSINESS_TIMEZONE | Opcional: America/Sao_Paulo já é o padrão |

Na URL, o usuário é avnadmin e o banco é ifix, não defaultdb. Codifique apenas a senha, uma vez, para caracteres especiais; não cole marcadores CLICK_TO:REVEAL_PASSWORD. Não acrescente ?ssl-mode=REQUIRED: TLS é configurado pelo código com CA e hostname.

Com MYSQL_SSL_CA_PEM, deixe MYSQL_SSL_CA ausente. Cole o PEM sem aspas/crases, mantenha as quebras internas e remova somente linhas vazias/espaços externos. O certificado CA é público; a senha e SECRET_KEY são privadas. Não incluí-las no repositório, logs ou apresentação.

Se quiser gerar SECRET_KEY no seu terminal local, execute e copie o resultado exclusivamente para o campo secreto do painel:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Não reutilize a chave Neon; os usuários precisarão entrar novamente. Não há fallback para a chave antiga. Nenhuma variável RATE_LIMIT_* ou IFIX_LOCAL_NO_RATE_LIMIT é necessária. IFIX_DEMO_MODE não é usado pelo código atual.

Se usar Preview, configure DATABASE_URL separadamente terminando em /ifix_test, CA e outro SECRET_KEY. O código recusa /ifix em Preview e /ifix_test em Production. Não marcar a mesma URL como Production and Preview. VERCEL_ENV e as URLs da implantação são fornecidas pela plataforma.

## 2. Conferir o projeto e enviar o código

A configuração existente em vercel.json usa backend/app.py como entrada Python e encaminha todas as rotas para Flask. Frontend, SQL e CA pública opcional estão incluídos. A fonte de dependências é backend/requirements.txt. Mantenha a raiz do projeto onde está vercel.json; não configurar apenas frontend como site estático.

As variáveis precisam ser publicadas junto com **esta versão MySQL do código**. Não apontar o deployment antigo PostgreSQL para a nova URL antes da troca de código. Na raiz do projeto, revise localmente:

```powershell
git status --short
git diff --check
```

Depois de revisar o que será enviado, faça o commit e o push pelo controle de versão do VS Code, na branch Production configurada no projeto Vercel. Essas ações são manuais: não foram feitas pelo agente. Não selecionar arquivos com senhas, .env, .venv ou uploads pessoais.

Com Git conectado, acompanhar a implantação criada pelo push na aba Deployments. Se o envio automático estiver desativado, inicie a implantação manualmente usando o commit novo. Um Redeploy de commit antigo só reaplica aquele código; não envia arquivos que estão apenas no VS Code.

Mudanças de variáveis passam a valer em uma nova implantação. Conferir o ambiente **Production**, commit correto e build completo. [Variáveis na Vercel](https://vercel.com/docs/environment-variables).

## 3. Validar o site após a implantação manual

1. Abrir a URL Production e conferir login, CSS, scripts e imagens. Em seguida entrar com sessão nova; cookies antigos não devem autenticar.
2. Validar o fluxo com contas autorizadas: cadastro/login, abrir chamado, convite/proposta, comparação/escolha, chat, laudo/custo adicional, conclusão, avaliação, notificações e histórico. Isso grava dados reais: usar apenas contas e operações que você queira manter, sem seed ou suíte automática em ifix.
3. Testar as dez funcionalidades descritas no README. Conferir horário de e-mail, urgência, modalidade e disponibilidade.
4. Conferir upload pequeno de foto/avatar/certificado; fotos de chamado devem exigir sessão de participante. Certificados e fotos de perfil são públicos: ocultar dados privados dos documentos.
5. Conferir logs sem compartilhar segredos. Se houver erro de CA, autenticação MySQL, build ou Cloudinary, interromper a validação e corrigir a causa antes da apresentação. O backend retorna erros da API em JSON; respostas de plataforma podem ser HTML.

O agente não validou este deployment nem abriu conexão remota nesta entrega. A remoção de testes do repositório não equivale a aprovação dos fluxos em produção.

## Limites de execução

Pool por instância: 2 conexões, overflow 0, pre_ping, recycle 240 s, espera 10 s; conexão 10 s e leitura/escrita 20 s. Instâncias simultâneas multiplicam conexões: conferir o limite do plano Aiven, sem aumentar o pool por tentativa.

Upload total: 4 MiB incluindo campos e todos os arquivos. O frontend reserva margem para multipart. Arquivos vão ao Cloudinary, não ao disco temporário da Vercel. Validar a entrega authenticated das fotos no Cloudinary e o remetente Brevo. E-mails são enviados depois do commit; falha no envio não reverte a operação SQL.

Não há DDL/seed durante startup ou deploy. SQL em backend/database é referência/manutenção, não um arquivo a executar na publicação. A rotina legada fn_listar_tecnicos_com_perfil do servidor não foi alterada nesta entrega; o app usa a rotina pública fn_listar_tecnicos_diretorio já instalada.

## Recuperação em caso de falha

Guardar a identificação do deployment e a configuração correspondente de forma segura. Se precisar voltar, retornar a código/configuração compatíveis entre si, preservando o banco e os registros. Não restaurar código PostgreSQL apontando para MySQL nem mudar a URL para Neon enquanto o backend é MySQL.

Depois de novas gravações em ifix, retornar ao Neon não transfere esses dados. Nesse caso, conter novas escritas e decidir recuperação antes de qualquer troca. Não executar DROP, reset, seed ou inicializador como rollback. Nenhuma ação remota foi realizada automaticamente.


## Diagnosticar erro de banco em login/cadastro

A resposta genérica HTTP 500 não identifica a causa. Os logs novos registram somente a classe, código MySQL e categoria fixa, por exemplo `Falha de banco (OperationalError; codigo=1045; categoria=autenticacao).` Não registram mensagem original, SQL, parâmetros, URL ou senha.

Após publicar o código com esse diagnóstico, reproduzir uma vez e consultar o log da requisição. 1045 aponta falha de autenticação (conferir usuário/senha e codificação da senha na URL); 1044/1142, permissões; 1049, banco; 1146/1054, tabela/coluna; 2003, conexão (host, porta, DNS, rede e possível TLS); categoria certificado_tls, validação de certificado; 1305, rotina ausente. A categoria orienta investigação, não comprova a correção nem autoriza DDL. Não recriar o banco ou reexecutar inicializador para tratar genericamente esses erros.
