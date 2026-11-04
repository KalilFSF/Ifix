"""Uma transação por caso de uso; serviços aninhados compartilham a unidade."""
from functools import wraps
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from database import db
from exceptions import ValidacaoError

TRANSACTION_STATE_KEY = "ifix_uow"

def persist():
    """Dentro de @atomic faz flush; fora dele preserva o commit das chamadas isoladas."""
    if TRANSACTION_STATE_KEY in db.session.info:
        db.session.flush()
    else:
        db.session.commit()


def after_commit(callback):
    state = db.session.info.get(TRANSACTION_STATE_KEY)
    if state is None:
        return callback()
    state["commit"].append(callback)
    return True


def after_rollback(callback):
    state = db.session.info.get(TRANSACTION_STATE_KEY)
    if state is not None:
        state["rollback"].append(callback)


def _callbacks(callbacks):
    import logging
    for callback in callbacks:
        try:
            callback()
        except Exception:
            logging.getLogger(__name__).warning("Efeito externo não concluído; requer reconciliação.")


def atomic(function):
    """Compartilha a transação entre serviços aninhados e confirma uma única vez."""
    @wraps(function)
    def execute(*args,**kwargs):
        if TRANSACTION_STATE_KEY in db.session.info:
            return function(*args,**kwargs)
        state = {"commit":[],"rollback":[]}
        db.session.info[TRANSACTION_STATE_KEY] = state
        try:
            result = function(*args,**kwargs)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            db.session.info.pop(TRANSACTION_STATE_KEY,None)
            _callbacks(reversed(state["rollback"]))
            if isinstance(error,IntegrityError):
                # Não transformar toda IntegrityError em "avaliação duplicada".
                from exceptions import ConflitoError
                raise ConflitoError("Os dados conflitam com um registro existente.") from None
            raise
        else:
            db.session.info.pop(TRANSACTION_STATE_KEY,None)
            _callbacks(state["commit"])
            return result
    return execute


def lock_model(model,identifier):
    """Relê a linha com FOR UPDATE, evitando decidir usando estado ORM antigo."""
    return db.session.execute(select(model).where(model.id==identifier)
        .with_for_update().execution_options(populate_existing=True)).scalar_one_or_none()


def lock_child(model,identifier,parent_field="servico_id"):
    """Bloqueia primeiro o chamado e depois o filho, na mesma ordem entre operações."""
    from modules.servicos.models.servico import Servico
    parent_id = db.session.execute(select(getattr(model,parent_field)).where(model.id==identifier)).scalar_one_or_none()
    if parent_id is None:
        return None
    lock_model(Servico,parent_id) # Ordem global: chamado antes de seus filhos.
    return lock_model(model,identifier)
