# Guia de testes — funcionalidades novas

> ## Por que este roteiro existe (e o que ainda não foi verificado)
>
> As funcionalidades foram implementadas e testadas **por código** — testes de
> Service (regras de negócio, permissões e travas) e testes HTTP contra os
> endpoints, com login real de sessão, confirmando os status corretos
> (401/403/400/201/200). Isso tudo passou.
>
> O que **não** foi possível executar aqui: **a aplicação nunca subiu de verdade**,
> porque faltaram três coisas no ambiente:
>
> | Faltou | Consequência |
> |---|---|
> | `DATABASE_URL` (Neon) não definida, e sem arquivo `.env` | `config.py` levanta `KeyError` no start — o app não sobe |
> | Nenhum Postgres local instalado | Sem banco alternativo para rodar a aplicação |
> | Docker indisponível (`command not found`) | Não deu para subir um Postgres temporário |
>
> Os testes automatizados rodaram em **SQLite em memória**, que cobre Models,
> Services, rotas e validações — mas **não executa as 9 funções SQL** de
> `backend/database/procedures.sql`, que são específicas de Postgres. Elas foram
> validadas de outra forma: sintaxe conferida com parser no dialeto `postgres`, e
> cada referência `tabela.coluna` checada contra o schema real que o SQLAlchemy
> gera. É uma verificação forte, mas **não substitui executá-las**.
>
> **Portanto, ao rodar este roteiro, os pontos de maior risco são os que dependem
> de procedure** — ou seja, toda tela que **lista** dados:
>
> - `/cliente/chamados` e `/tecnico/home` (listagem de chamados —
>   `fn_listar_servicos_participante`, alterada para trazer teto, laudo e garantia)
> - O bloco **Custos adicionais** (`fn_listar_aprovacoes_por_servico`, nova)
> - Os campos `garantia_ativa` e `garantia_dias_restantes`, calculados em SQL
>   (`fn_garantia_expira_em`, nova) e que precisam bater com o que o Python calcula
>
> Se alguma lista vier vazia ou o terminal acusar erro de função inexistente,
> reinicie o app: as procedures são reinstaladas a cada start.

Roteiro de verificação manual pelo navegador das funcionalidades **2, 6, 7, 8 e 9**.
Cada seção diz em que tela a funcionalidade aparece, o que fazer e o que precisa
acontecer — incluindo os casos que **devem falhar**, que são a parte que realmente
prova a regra.

As funcionalidades **3 e 4** (avaliação mútua) já existiam e não foram alteradas;
estão no fim, como checagem de regressão.

---

## Antes de começar

**Subir a aplicação:**

```bash
cd backend
python app.py           # http://127.0.0.1:5000
```

`DATABASE_URL` (Postgres/Neon) precisa estar definida — sem ela o app não sobe.
As colunas e procedures novas são criadas sozinhas no start: **não apague o banco**,
basta reiniciar.

`BREVO_API_KEY` é opcional. Sem ela os e-mails são pulados com aviso no terminal e
nada quebra — mas, para conferir as notificações, vale configurá-la.

**Contas necessárias** — duas, em janelas separadas (uma normal e uma anônima), já
que a sessão é por cookie:

| Papel | Onde criar | Atenção |
|---|---|---|
| Técnico | `/cadastro` → "Técnico" | **Permita a localização** quando o navegador pedir |
| Cliente | `/cadastro` → "Cliente" | Idem — sem isso a seleção automática não acha ninguém |

**Mapa rápido de telas:**

| Rota | Tela |
|---|---|
| `/cliente/home` | Home do cliente |
| `/cliente/abrir-chamado` | Abertura de chamado |
| `/cliente/chamados` | Meus chamados (modal de detalhe) |
| `/tecnico/home` | Painel do técnico (modal de detalhe) |

---

## Funcionalidade 9 — Restrição de horário

> *"definir restrições de horário para evitar atendimentos em períodos específicos"*

**Telas:** `/cliente/home` (seção **Restrições de horário**) e `/tecnico/home`
(seção **Meu horário de atendimento**) · `/tecnico/home` → modal do chamado → card
**Cliente**

**Endpoint:** `PUT /api/me/horario-atendimento`

### Como testar

1. Em `/cliente/home`, role até **Restrições de horário**. Os campos devem vir
   preenchidos com o padrão **08:00 – 18:00**.
2. Mude para uma faixa qualquer e clique em **Salvar horário** → toast de confirmação.
3. Recarregue a página: os valores salvos devem persistir.
4. Em `/tecnico/home`, repita em **Meu horário de atendimento**.
5. Abra um chamado como cliente e, no painel do técnico, abra o modal do chamado:
   no card **Cliente** deve aparecer *"Atende das HH:MM às HH:MM"*.

### O que deve falhar

| Ação | Resultado esperado |
|---|---|
| Início e término iguais | Toast: *"O horário de início e o de término não podem ser iguais."* |
| Deixar um campo vazio | Toast: *"Preencha os dois horários."* |

### Efeito da regra (opcional, exige Brevo)

Defina no **técnico** uma faixa que não contenha o horário atual (ex.: `03:00–03:01`)
e abra um chamado como cliente.

- A solicitação **continua aparecendo** em *Solicitações pendentes* no painel dele.
- O **e-mail de aviso não é enviado**.

Isso é intencional: bloquear a solicitação deixaria o cliente sem atendimento por um
motivo que é do técnico. A restrição silencia o aviso, não o trabalho.

---

## Funcionalidade 8 — Relatório técnico da causa do defeito

> *"receber um relatório técnico simplificado explicando a causa do defeito"*

**Telas:** `/tecnico/home` → modal → card **Relatório técnico** (preenche) ·
`/cliente/chamados` → modal → bloco **Relatório técnico** (lê)

**Endpoint:** `PUT /api/servicos/<id>/laudo`

### Como testar

1. Leve um chamado até **Em análise** (o card só aparece a partir daí — não faz
   sentido explicar a causa de algo que nem foi aberto).
2. Preencha **Causa do defeito** (lista fechada), **O que causou o problema** e,
   opcionalmente, **O que foi feito**. Clique em **Salvar relatório**.
3. Como cliente, abra o mesmo chamado em `/cliente/chamados`: o bloco
   **Relatório técnico** deve mostrar a causa e o texto.
4. Volte como técnico e edite o relatório — o botão passa a dizer
   **Atualizar relatório** e o texto novo deve aparecer para o cliente.

### O que deve falhar

| Ação | Resultado esperado |
|---|---|
| Salvar sem escolher a causa | Toast: *"Selecione a causa do defeito."* |
| Explicação com menos de 20 caracteres | Toast pedindo pelo menos 20 caracteres |
| **Finalizar sem relatório** | Erro: *"Registre o laudo técnico antes de finalizar o chamado."* |

A última linha é o coração da funcionalidade: **nenhum chamado pode ser encerrado sem
explicação**. Depois de finalizado, os campos ficam somente leitura.

---

## Funcionalidades 6 e 7 — Teto de gasto e autorização remota

> 6: *"limite máximo de gasto para que nenhum reparo adicional seja executado sem aprovação"*
> 7: *"autorizar remotamente a continuidade do serviço caso o técnico identifique novos problemas"*

São o mesmo fluxo visto dos dois lados e devem ser testadas juntas: o teto (6) é o
limite, a autorização (7) é como ele é ultrapassado com consentimento.

**Telas:** `/cliente/abrir-chamado` (define o teto) · `/tecnico/home` → modal → card
**Custo adicional** (pede) · `/cliente/chamados` → modal, bloco no topo
**Autorização necessária** (responde)

**Endpoints:** `POST` e `GET /api/servicos/<id>/aprovacoes` · `PATCH /api/aprovacoes/<id>`

### Como testar

1. Em `/cliente/abrir-chamado`, preencha **Limite máximo de gasto** com `1000`,
   marque **Garantia iFix** (vamos reaproveitar este chamado na funcionalidade 2) e
   envie.
2. Abra o chamado em `/cliente/chamados`. No grid devem aparecer:
   - **Teto de gasto:** `R$ 1.000,00`
   - **Garantia:** `Sim (+7% · 10 dias)`

   > O teto fica em 1000 mesmo com garantia marcada. O acréscimo de 7% incide sobre o
   > valor de referência, não sobre o limite — o teto é o que você aceita gastar em
   > **reparo**, não na taxa da garantia. Antes desta entrega os dois eram o mesmo
   > campo, e por isso o limite não limitava nada.
3. Como técnico, envie um orçamento de `900` e, como cliente, escolha-o.
4. Avance o chamado para **Em análise** → aparece o card **Custo adicional**, exibindo
   o teto autorizado.
5. Descreva um problema novo, informe `300` e clique em **Solicitar autorização**.
6. Como cliente (aguarde até 7s, o polling atualiza sozinho): o bloco **Autorização
   necessária** aparece **no topo** do modal, em destaque — é ação bloqueante.
7. Clique em **Autorizar** e confirme. O **Teto de gasto** deve passar para
   `R$ 1.300,00`.

   > O teto sobe em vez de sumir: o limite continua valendo para o que vier depois, em
   > vez de virar cheque em branco na primeira autorização.

### O que deve falhar

| Ação | Resultado esperado |
|---|---|
| Descrição com menos de 15 caracteres | Toast pedindo pelo menos 15 caracteres |
| Valor zero ou negativo | Toast: *"Informe um custo adicional maior que zero."* |
| Pedir uma segunda autorização com uma pendente | *"Já existe uma autorização aguardando resposta do cliente."* |
| **Finalizar com autorização pendente** | *"Existe uma autorização de custo aguardando resposta do cliente."* |
| Responder a mesma autorização duas vezes | *"Esta autorização já foi respondida."* |

### Testar a recusa

Peça outra autorização e **recuse** (dá para informar o motivo). Confirme que:

- O teto **não muda**.
- O item aparece em **Custos adicionais** marcado como *Recusado*.
- O técnico recebe e-mail orientando a **não executar** o serviço.

### Orçamento acima do teto

Com um chamado de teto `1000`, envie um orçamento de `1500`. Ele **não é bloqueado** —
fica registrado como *"Orçamento acima do teto"*.

Recusar deixaria um chamado de teto baixo sem nenhum orçamento; quem decide se o valor
vale a pena é o cliente, na hora de escolher.

---

## Funcionalidade 2 — Acionamento da garantia

> *"acionar garantia caso o problema retorne em até 10 dias, com reembolso ou novo atendimento"*

**Telas:** `/cliente/abrir-chamado` (contrata) · `/cliente/chamados` → modal → bloco
**Garantia iFix** (aciona) · `/tecnico/home` (recebe o chamado gerado)

**Endpoints:** `POST` e `GET /api/servicos/<id>/garantia`

### Como testar

1. Use o chamado da seção anterior (aberto **com garantia**) e leve-o até
   **Finalizado** — lembrando que ele exige relatório técnico e nenhuma autorização
   pendente.
2. Como cliente, abra o chamado: o bloco **Garantia iFix** mostra os **dias restantes**
   de cobertura e o botão **Acionar garantia**.
3. Clique nele: abre o formulário com a descrição do problema e duas opções —
   **Novo atendimento** (pré-selecionada) e **Reembolso**.
4. Descreva o que voltou a acontecer, mantenha **Novo atendimento** e confirme.
5. O toast informa o código do chamado gerado. Verifique que ele:
   - aparece em **Meus chamados** com o título prefixado por `[Garantia]`;
   - está com valor **R$ 0,00**;
   - já está atribuído ao **mesmo técnico**, sem passar por orçamento de novo.
6. No painel do técnico, abra esse chamado: deve exibir
   *"Atendimento em garantia — sem custo para o cliente."*

> O chamado de garantia **não tem garantia própria** — ela já foi paga e consumida no
> original. Renová-la a cada acionamento daria garantia perpétua.

### O que deve falhar

| Ação | Resultado esperado |
|---|---|
| Acionar em chamado **sem** garantia | Bloco não aparece · API: *"Este chamado não possui garantia contratada."* |
| Acionar antes de finalizar | Bloco não aparece · API: *"A garantia só pode ser acionada em um chamado finalizado."* |
| Descrição com menos de 15 caracteres | Toast pedindo pelo menos 15 caracteres |
| Acionar de novo com um acionamento em andamento | *"Já existe um acionamento de garantia em andamento para este chamado."* |

### Testar a expiração do prazo

Este é o caso que não dá para reproduzir esperando. No SQL editor do Neon:

```sql
UPDATE servicos
SET finalizado_em = NOW() - INTERVAL '11 days'
WHERE id = <id do chamado>;
```

Recarregue `/cliente/chamados`. O bloco deve passar a dizer que o prazo de 10 dias
expirou, **sem** o botão de acionar. Forçando a chamada da API, a resposta é
*"O prazo de garantia de 10 dias após a finalização já expirou."*

---

## Regressão — o que não pode ter quebrado

Percorra o fluxo original inteiro e confirme que segue funcionando:

| # | Item | Onde |
|---|---|---|
| 1 | Cadastro de cliente e de técnico | `/cadastro` |
| 2 | Login e os chips **Cliente / Técnico** na mesma conta | Sidebar |
| 3 | Seleção automática de técnicos por proximidade | Abrir chamado → painel do técnico |
| 4 | Envio e escolha de orçamento | Ambos os painéis |
| 5 | Avanço de status e e-mail a cada mudança | `/tecnico/home` |
| 6 | **Avaliação do técnico** (tempo, honestidade, preço justo) — func. 3 | `/cliente/chamados`, chamado finalizado |
| 7 | **Avaliação do cliente** (comportamento, colaboração) — func. 4 | `/tecnico/home`, chamado finalizado |
| 8 | Suspensão após 3 notas baixas de comportamento | Tentar abrir chamado com a conta suspensa |
| 9 | Cancelar e excluir chamado | `/cliente/chamados` |
| 10 | Upload de até 5 fotos (5 MB cada) | `/cliente/abrir-chamado` |

Durante tudo isso, mantenha abertos:

- **Console do navegador** — não deve haver erro de `.json()` nem de JS.
- **Terminal do Flask** — não deve haver nenhum **500**. Erros de regra de negócio
  aparecem como 400/403/404/409, que é o comportamento correto.

---

## Ordem sugerida

Um único chamado cobre quase tudo, na sequência natural do fluxo:

```
abrir com teto + garantia   → funcionalidade 6
   ↓
orçamento e escolha          (regressão)
   ↓
em análise → custo adicional → funcionalidade 7
   ↓
relatório técnico            → funcionalidade 8
   ↓
finalizado → acionar garantia → funcionalidade 2
   ↓
avaliação mútua              (regressão das funcionalidades 3 e 4)
```

A funcionalidade 9 é independente e pode ser testada a qualquer momento.
