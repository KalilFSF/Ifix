# Diagnóstico do default servicos.preco_estimado

## Causa identificada no código

A validação anterior comparava representações textuais:

```python
str(actual["COLUMN_DEFAULT"]).lower() != expected_default.lower()
```

O modelo `Servico.preco_estimado` define `Numeric(10, 2), nullable=False, default=0`. O SQL gerado define `NUMERIC(10, 2) NOT NULL DEFAULT 0`. Esses dois contratos estão alinhados: o preço padrão é zero, com duas casas na coluna.

Para uma representação MySQL `COLUMN_DEFAULT='0.00'`, o validador comparava `'0.00'` com `'0'` e lançava ValueError, apesar de ambos representarem exatamente o mesmo número. Esse falso positivo foi reproduzido nos testes locais. A falha era do validador que preparei, não uma razão para recriar tabelas ou mudar a regra financeira.

O erro original não registrava o valor observado. Não houve nova conexão ao Aiven nesta investigação; portanto, o retorno literal do banco do usuário precisa ser confirmado pelo diagnóstico abaixo. Se ele mostrar `0.00`, `0` ou outra representação numérica equivalente a zero, não existe divergência real de default nessa coluna e nenhum ALTER é necessário. Se mostrar NULL, 1.00 ou outro valor não equivalente, há divergência real e ela não será ignorada.

O MySQL documenta que COLUMN_DEFAULT contém o valor padrão e retorna SQL NULL tanto para DEFAULT NULL quanto para ausência de cláusula DEFAULT. O diagnóstico não confunde esse NULL com zero nem com o texto 'NULL'.

## Correção local

O helper `scripts/mysql_defaults.py` compara defaults por tipo:

- Numeric/Integer/Float/Boolean: converte literais em Decimal, sem float ou arredondamento. Zero e 0.00 são equivalentes; 0.01 e zero são diferentes. Não avalia expressões SQL.
- Textos: comparação exata, preservando caixa e espaços; '0' em VARCHAR não é '0.00'.
- Timestamps: aceita grafia equivalente de CURRENT_TIMESTAMP/NOW, mas exige a mesma precisão. CURRENT_TIMESTAMP(3) não equivale a CURRENT_TIMESTAMP(6).
- Nulo/sem default: deve continuar nulo; não vira zero ou string vazia.

A função `validate_objects` usa esse helper em todas as colunas e informa esperado, observado e tipo ao detectar divergência. A recusa do inicializador para bancos não vazios permanece intacta. O relatório também passa a distinguir falha durante DDL de criação concluída com validação reprovada, para não confundir um falso positivo final com criação incompleta.

O modelo e `schema_mysql.sql` **não foram alterados**. Nenhum valor financeiro, tabela, dado, índice, FK ou rotina foi modificado.

## Revisão das outras colunas

No schema atual, `servicos.preco_estimado` é a única coluna Numeric com default escalar. Os outros campos financeiros e `perfis_tecnicos.nota_media` não têm default de preenchimento e continuam opcionais, conforme seus modelos.

O mesmo erro de comparação textual poderia atingir defaults numéricos futuros, inteiros/booleanos representados numericamente e diferenças de grafia das expressões temporais. Foram revisados os contadores, flags, textos de status/modalidade/horário e eventos DATETIME(6). A correção é por tipo para todo o schema, sem substituir indiscriminadamente '.00' em textos ou omitir verificações.

## Validar somente a estrutura existente pelo VS Code

Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe scripts/validar_mysql.py
```

Informe host DNS Aiven, porta, usuário, banco `ifix`, senha oculta e caminho da CA, como fez no inicializador. Não precisa de `.env`.

O diagnóstico usa TLS com verificação de CA/hostname. Aceita tabelas e rotinas já existentes. Não chama o inicializador, não exige banco vazio, não instala rotinas, não executa CALL e não lê registros das tabelas de negócio. Os comandos enviados pelo diagnóstico são somente SELECT de metadados e SHOW da sessão; uma barreira de código recusa DDL/DML/CALL. A conexão compartilhada configura apenas a própria sessão (timezone/charset), sem alterar schema ou dados.

Ele mostra esperado/observado de todos os defaults definidos, lista divergências de default e reaproveita a validação completa de tipos, nullability, engine/collation, PK, AUTO_INCREMENT, UNIQUEs, índices, FKs e nomes/tipos das rotinas. Se houver outro problema estrutural, a checagem compartilhada informa o primeiro; todos os defaults são examinados antes dela. É necessário acesso de leitura aos metadados de todas as tabelas/rotinas; falta de visibilidade de objetos pode ser reportada como ausência.

Exemplo de resultado correto:

```text
servicos.preco_estimado: 0 | '0.00' | OK
Estrutura validada: 14 tabelas e 23 rotinas; ...
VALIDAÇÃO APROVADA. Nenhuma alteração executada. Não reexecute o inicializador.
```

Código de saída 0 significa validado; 1 significa divergência, erro de conexão ou diagnóstico interrompido. Essa validação verifica metadados, não a execução funcional do corpo de todas as rotinas.

**Não rode `inicializar_mysql.py` novamente contra ifix.** O banco informado pelo usuário já tem as 14 tabelas e 23 rotinas e deve ser preservado.

## Somente se houver divergência real

Para pedir uma sugestão SQL no relatório, sem executá-la:

```powershell
.\.venv\Scripts\python.exe scripts/validar_mysql.py --mostrar-sql-correcao
```

Se `preco_estimado` continuar DECIMAL(10,2) NOT NULL, mas o default realmente estiver ausente ou diferente de zero, será exibido apenas:

```sql
ALTER TABLE `ifix`.`servicos`
    ALTER COLUMN `preco_estimado` SET DEFAULT 0.00;
```

Efeito: apenas INSERTs futuros que omitam a coluna passam a usar zero. Não atualiza preços existentes, não muda tipo, nullability, dados, FKs ou procedures. O comando DDL pode aguardar metadata lock e faz commit implícito; ele não é executado pelo diagnóstico.

Se o default for equivalente, o script não sugere correção. Se tipo ou nullability também divergirem, não sugere esse ALTER como solução suficiente. Sem confirmação de divergência real no diagnóstico, **não existe correção remota indicada**.

Para aplicar manualmente somente esse SQL, caso realmente indicado, é possível usar no terminal VS Code uma sessão Python com as dependências do projeto, preservando senha oculta/TLS:

```powershell
.\.venv\Scripts\python.exe
```

Depois digite, sem reutilizar o inicializador:

```python
import sys
sys.path.insert(0, "scripts")
from inicializar_mysql import prompt_connection
from validar_mysql import diagnose
conn = prompt_connection("ifix")
diagnose(conn, show_correction=True)  # Leia os valores e a sugestão antes de qualquer alteração.
# Somente se o diagnóstico confirmar divergência REAL e você decidir aplicar:
confirmacao = input("Digite CORRIGIR DEFAULT ifix.servicos.preco_estimado: ")
if confirmacao == "CORRIGIR DEFAULT ifix.servicos.preco_estimado":
    with conn.cursor() as cursor:
        cursor.execute("ALTER TABLE `ifix`.`servicos` ALTER COLUMN `preco_estimado` SET DEFAULT 0.00")

# Linha em branco encerra o bloco no terminal interativo.
diagnose(conn)  # Revalidar sem recriar objetos.
conn.close()
```

Esse bloco é uma instrução manual condicional, não um script executado nesta entrega. Não aplique o ALTER se a única diferença for '0' versus '0.00'.

## Testes e arquivos desta correção

Os testes de `tests/test_mysql_defaults.py` reproduzem a escala Decimal, verificam diferenças reais, todos os tipos de default, a validação completa com metadados simulados das 14 tabelas e a proteção somente leitura. Suíte completa após a correção: **115 testes passaram e 1 integração MySQL real permaneceu ignorada**. O verificador do schema também passou; modelo e SQL permanecem correspondentes. Não foi executado MySQL remoto.

Arquivos criados: `scripts/mysql_defaults.py`, `scripts/validar_mysql.py`, `tests/test_mysql_defaults.py`, este documento. Arquivos atualizados: `scripts/inicializar_mysql.py`, `MIGRACAO_MYSQL.md`, `RELATORIO_MIGRACAO.md`.

Referências: [MySQL 8.4 — information_schema.COLUMNS](https://dev.mysql.com/doc/refman/8.4/en/information-schema-columns-table.html), [MySQL 8.4 — defaults](https://dev.mysql.com/doc/refman/8.4/en/data-type-defaults.html).
