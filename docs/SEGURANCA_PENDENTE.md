# Segurança e limites operacionais

## Proteções mantidas

- Autorização por chamado/atendimento; dono e responsável recebem dados autorizados, convidados recebem recorte reduzido com as fotos do problema para orçar e estranhos são bloqueados. O acesso do convidado às fotos exige convite válido, chamado aberto e ausência de responsável definido.
- Diretório e perfil públicos têm projeções explícitas sem CPF, e-mail privado, telefone, hash ou coordenadas precisas.
- Sessões com vínculo de versão e cookies separados por ambiente; SECRET_KEY nova deve ser aplicada no release.
- CSRF para escritas JSON/multipart e logout; verificação de Origin quando presente, cabeçalhos de segurança e respostas API sem traceback.
- TLS MySQL com CA e verificação de hostname, SQL parametrizado e transações por caso de uso com rollback/locks.
- Validação de tipo/MIME/conteúdo/tamanho de uploads, imagens regravadas sem EXIF e fotos novas de chamado autenticadas.
- Escape do texto interpolado nos e-mails e fuso America/Sao_Paulo configurável.
- Exclusão ORM de contas bloqueada para preservar vínculos e histórico.

## Alteração solicitada

Redis e o limitador de tentativas foram removidos por decisão do responsável. Não há armazenamento em memória substituindo esse serviço, nem exigência de variáveis Redis no startup. **O backend não limita automaticamente tentativas de login/cadastro ou escritas.** CSRF protege contra requisições forjadas, mas não substitui proteção contra abuso automatizado.

A suíte local, runners de integração e seed demonstrativo foram removidos a pedido. Antes da remoção, 182 verificações locais passaram com o código sem Redis. Isso não é prova de execução desta versão no Aiven/Vercel; a validação remota continua manual, sem autorização implícita para o agente.

## Limites e decisões pendentes

- Validar build Vercel, CA/hostname reais, comportamento InnoDB sob concorrência, Cloudinary authenticated, Brevo e os fluxos visuais. Nenhuma dessas integrações foi acionada remotamente nesta entrega.
- E-mail é best-effort após commit; não há outbox durável. Falha de transporte pode exigir reenvio administrado, sem repetir a operação de negócio.
- Em rollback, limpeza do novo asset Cloudinary é compensação best-effort. Falha requer reconciliação; não apaga arquivos antigos automaticamente.
- Avatar e certificados são públicos por funcionalidade; avisar o titular e ocultar dados sensíveis no próprio documento. Validação de arquivo não é antivírus nem remoção automática de informação pessoal visível.
- Fotos antigas públicas não se tornam privadas retroativamente. Nenhum dado Neon foi copiado para o MySQL.
- FKs CASCADE existentes não mudaram. O bloqueio ORM não impede DELETE SQL direto/bulk de administrador. Desativação/anonimização e prazo de retenção dependem de decisão; não habilitar exclusão destrutiva de contas.
- A rotina legada fn_listar_tecnicos_com_perfil instalada pode retornar dados pessoais a usuários SQL com EXECUTE; a aplicação não a utiliza. Não reaplicar procedures.sql para atualizá-la. Qualquer mudança exige revisão/autorização separada.
- Upload total de 4 MiB, pool de 2 conexões por instância e limites do plano precisam ser respeitados. Deadlock pode retornar 409; não há repetição automática.

Não declarar implantação comprovada apenas porque o código está preparado. Instruções operacionais: [PRODUCAO.md](PRODUCAO.md).
