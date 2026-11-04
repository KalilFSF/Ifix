# MySQL no Aiven

A migração já foi implementada e o usuário validou as 14 tabelas/23 rotinas em MySQL 8.4.11. O banco definitivo é ifix e deve ser preservado. Não importar registros Neon ou dados fictícios, nem reexecutar inicializador.

Runtime: Flask/SQLAlchemy/PyMySQL com TLS, CA e hostname verificados. A Vercel usa DATABASE_URL e MYSQL_SSL_CA_PEM; não há dependência de Redis. SQL não monta JSON: serializers Python mantêm contratos explícitos.

Estrutura e apresentação: [README.md](README.md). Configuração e publicação manual: [docs/PRODUCAO.md](docs/PRODUCAO.md). Limites: [docs/SEGURANCA_PENDENTE.md](docs/SEGURANCA_PENDENTE.md).
