"""Verificação TLS compartilhada pelo Flask e pelas ferramentas manuais."""
import os
import ssl
from pathlib import Path

def tls_context(ca_path=None, ca_pem=None):
    if ca_path is None and ca_pem is None:
        ca_path = os.environ.get("MYSQL_SSL_CA")
        ca_pem = os.environ.get("MYSQL_SSL_CA_PEM")
    if bool(ca_path) == bool(ca_pem):
        raise ValueError("Forneça exatamente uma CA: MYSQL_SSL_CA ou MYSQL_SSL_CA_PEM.")
    if ca_path:
        path = Path(ca_path)
        ca_path = str(path if path.is_absolute() else Path(__file__).resolve().parents[1] / path)
    context = ssl.create_default_context(cafile=ca_path, cadata=ca_pem)
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context
