"""Impede exclusão ORM de contas para preservar vínculos; não altera FKs nem impede SQL administrativo."""
from sqlalchemy import event
from sqlalchemy.orm import Session
from exceptions import PermissaoNegadaError

@event.listens_for(Session,"before_flush")
def prevent_account_deletion(session,flush_context,instances):
    from modules.usuarios.models.usuario import Usuario
    if any(isinstance(value,Usuario) for value in session.deleted):
        raise PermissaoNegadaError("Exclusão de conta desabilitada para preservar o histórico. Solicite desativação/anonimização administrada.")
