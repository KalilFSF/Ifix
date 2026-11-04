"""Horário de negócio independente do fuso do servidor da Vercel."""
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from flask import current_app

def business_now(now=None):
    """Converte um instante para BUSINESS_TIMEZONE, padrão America/Sao_Paulo.

    Recebe opcionalmente um datetime com fuso. A persistência continua em UTC;
    este horário serve às decisões de negócio, como a faixa de envio de e-mail.
    """
    instante = now or datetime.now(timezone.utc)
    fuso_negocio = ZoneInfo(current_app.config.get("BUSINESS_TIMEZONE","America/Sao_Paulo"))
    return instante.astimezone(fuso_negocio)
