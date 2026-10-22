# Configurações centrais do Flask/SQLAlchemy. Tudo aqui pode ser sobrescrito
# por variável de ambiente (útil pra produção, sem mexer no código).

import os

from sqlalchemy.engine import make_url

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")


class Config:
    # Usada pelo Flask para assinar cookies de sessão e mensagens flash.
    # Em produção, defina a variável de ambiente SECRET_KEY com um valor
    # aleatório e secreto — nunca deixe o valor padrão abaixo.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-troque-em-producao")

    # Banco Postgres (Neon), único ambiente suportado — sem fallback local
    # em SQLite: as Repositories chamam procedures/functions definidas em
    # backend/database/procedures.sql, recurso que o SQLite não tem. Defina
    # DATABASE_URL com a connection string do Neon (Vercel > Settings >
    # Environment Variables).
    # SQLAlchemy 2.1 passou a usar psycopg 3 para postgresql://, mas o
    # projeto usa psycopg2-binary. Fixe o driver sem alterar credenciais,
    # parâmetros SSL ou URLs que já especificam um driver explicitamente.
    SQLALCHEMY_DATABASE_URI = make_url(os.environ["DATABASE_URL"])
    if SQLALCHEMY_DATABASE_URI.drivername in {"postgres", "postgresql"}:
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.set(
            drivername="postgresql+psycopg2"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads de foto de perfil e diplomas do técnico ficam dentro de
    # frontend/uploads/ — o Flask serve TODO o frontend/ como estático
    # (ver app.py), então esses arquivos saem direto em /uploads/... sem
    # precisar de uma rota própria pra servir arquivo.
    UPLOAD_FOLDER = os.path.join(FRONTEND_DIR, "uploads")
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024  # 30 MB por request (até 5 fotos de 5 MB, ver constants.MAX_BYTES_FOTO_CHAMADO)
