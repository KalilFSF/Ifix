# Instância única do SQLAlchemy, compartilhada por todo o projeto.
#
# Fica no seu próprio arquivo (em vez de dentro de app.py ou models.py) pra
# evitar import circular: tanto app.py quanto models.py e routes.py precisam
# importar `db`, e se ela vivesse em um desses arquivos os outros dois
# acabariam se importando um ao outro.

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
