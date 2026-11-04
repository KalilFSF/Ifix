# Frontend IFix

HTML, CSS e JavaScript entregues pelo Flask; o frontend chama a API do próprio domínio.

- index.html: login atual; a página index.html da raiz do repositório é legada.
- pages/: telas do cliente, técnico, cadastro, conta e diretório.
- js/: comportamento das telas e componentes compartilhados; api.js centraliza HTTP/CSRF.
- css/: tema, formulários, painéis e responsividade.
- assets/: logotipo e ícones.
- uploads/: apoio local ignorado no Git; produção usa Cloudinary.
- views/: arquivos legados, fora do fluxo principal atual.

Backend: Python, Flask, SQLAlchemy e MySQL no Aiven. Não há IA/n8n executando o ranking nesta versão: a seleção é calculada em Python. Hospedagem: Vercel.

Guia detalhado para estudo: [../docs/GUIA_COMPLETO_DO_PROJETO.md](../docs/GUIA_COMPLETO_DO_PROJETO.md). Visão geral: [../README.md](../README.md).

## Equipe

- Nome completo dos integrantes da equipe:
  Victor Oliveira Fagundes de Almeida,
  Matheus Miranda Gomes,
  Lucas Henrique de Almeida Cordoval,
  Samara Marcelina Ramos,
  Theo Andrade Silva,
  Kalil Felipe Silva Fernandes.
