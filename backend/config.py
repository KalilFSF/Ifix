# Configurações centrais do Flask/SQLAlchemy. Tudo aqui pode ser sobrescrito
# por variável de ambiente (útil pra produção, sem mexer no código).

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
DATABASE_DIR = os.path.join(BASE_DIR, "database")


class Config:
    # Usada pelo Flask para assinar cookies de sessão e mensagens flash.
    # Em produção, defina a variável de ambiente SECRET_KEY com um valor
    # aleatório e secreto — nunca deixe o valor padrão abaixo.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-troque-em-producao")

    # Banco SQLite local, salvo em backend/database/ifix.db.
    # Pra trocar por outro banco (Postgres, MySQL...) no futuro, basta setar
    # a variável de ambiente DATABASE_URL com a connection string.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(DATABASE_DIR, 'ifix.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads de foto de perfil e diplomas do técnico ficam dentro de
    # frontend/uploads/ — o Flask serve TODO o frontend/ como estático
    # (ver app.py), então esses arquivos saem direto em /uploads/... sem
    # precisar de uma rota própria pra servir arquivo.
    UPLOAD_FOLDER = os.path.join(FRONTEND_DIR, "uploads")
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024  # 30 MB por request (até 5 fotos de 5 MB, ver constants.MAX_BYTES_FOTO_CHAMADO)
