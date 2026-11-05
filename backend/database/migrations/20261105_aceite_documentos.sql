-- Executar UMA VEZ no schema escolhido, ANTES de implantar o novo backend.
-- Somente adiciona colunas anuláveis; preserva usuários e histórico existentes.
-- Não executar schema_mysql.sql nem inicializadores em banco existente.
ALTER TABLE usuarios
    ADD COLUMN termos_versao VARCHAR(32) NULL,
    ADD COLUMN privacidade_versao VARCHAR(32) NULL,
    ADD COLUMN termos_aceitos_em DATETIME(6) NULL;
-- Contas anteriores permanecem NULL: não inventar aceite retroativo.
