# Cadastro com aceite de documentos

Foram adaptados os modelos fornecidos para Termos de Uso e Aviso de Privacidade, versão 2026-11-05.1. O modelo de consentimento genérico não é exigido como um segundo aceite obrigatório. Geolocalização mantém permissão separada no navegador.

Os modelos citavam pagamentos/Pix, dois fatores, conformidade ISO, ausência de compartilhamento e controles de menores que não correspondem ao código. Esses trechos foram ajustados, sem prometer certificações ou recursos inexistentes. CPF e telefone pessoal do responsável não foram reproduzidos; foi mantido o contato de e-mail indicado nos documentos. A identificação/canal e as regras jurídicas devem ser conferidos pelo responsável antes de publicação; não há promessa de conformidade integral apenas pela implementação da caixa.

## Implantação em banco existente

1. Aplicar uma única vez backend/database/migrations/20261105_aceite_documentos.sql em cada banco utilizado, antes de publicar o novo backend. Fazer a alteração no schema correto (ifix ou ifix_test). Não executar o inicializador nem recriar tabelas.
2. Implantar frontend e backend da mesma versão. O cadastro exige aceite_termos=1 e versões iguais às publicadas em backend/legal.py; dados ausentes, false, 0 ou versões antigas são rejeitados antes de criar usuários ou enviar uploads.
3. Conferir que novos usuários têm termos_versao, privacidade_versao e termos_aceitos_em. A data é UTC e gerada pelo servidor. Usuários existentes continuam NULL e não são bloqueados no login. Conversão de uma conta existente em técnico não cria nem sobrescreve o aceite original.
4. Testar cadastro de ambos os papéis, erro sem aceite, leitura em nova aba, persistência e rollback de falha no cadastro técnico.

Não foi executada alteração remota no banco nem deploy. O schema_mysql.sql é a referência para instalações vazias, não uma migração de produção.

## Arquivos e versões

- backend/legal.py: validação e versões atuais.
- backend/page_routes.py: páginas públicas /termos e /privacidade.
- frontend/pages/legal/2026-11-05.1/: textos versionados, acessíveis sem login.
- frontend/pages/cadastro.html, frontend/js/cadastro.js, frontend/css/cadastro.css: checkbox e links de ambos os cadastros.
- backend/modules/usuarios/controllers/usuario_controller.py: leitura explícita dos campos.
- backend/modules/usuarios/services/cadastrar_*_service.py: rejeição antes de qualquer efeito externo.
- backend/modules/usuarios/models/usuario.py: registro na mesma transação da conta; campos fora de CAMPOS_EDITAVEIS para impedir alteração via PATCH /api/me.

Para mudar o texto, criar uma nova pasta de versão, atualizar as constantes e os campos/links do cadastro no mesmo deploy. Não editar os textos de uma versão já aceita. Os registros não são expostos no diretório público. Registros de IP/user-agent adicionais não foram introduzidos.

## Referência legal consultada

LGPD, arts. 7 e 8: execução de contrato e outras bases não se confundem com consentimento; consentimento deve ter finalidades determinadas e não pode ser uma autorização genérica. Fonte: https://www2.camara.leg.br/legin/fed/lei/2018/lei-13709-14-agosto-2018-787077-normaatualizada-pl.html
