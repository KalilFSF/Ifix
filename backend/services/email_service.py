# Envio de e-mail transacional via Brevo (ex-Sendinblue) — mesmo padrão do
# Cloudinary em utils.py: credenciais via variável de ambiente, sem SDK
# pesado, só a API REST deles com `requests`.
#
# Configuração necessária (Vercel > Settings > Environment Variables, mesma
# tela onde já estão CLOUDINARY_*/DATABASE_URL):
#   BREVO_API_KEY      — obrigatória; sem ela o envio é pulado (log, sem erro)
#   BREVO_SENDER_EMAIL — remetente, precisa estar verificado na Brevo
#   BREVO_SENDER_NOME  — nome de exibição do remetente (opcional)

import os

import requests

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "naoresponda@ifix.app")
BREVO_SENDER_NOME = os.environ.get("BREVO_SENDER_NOME", "iFix")


class EmailService:
    """Serviço de envio de e-mail transacional — usado por Services de outros
    módulos (ex: AtualizarStatusServicoService) sempre que uma ação do
    sistema precisa notificar um usuário por e-mail."""

    @staticmethod
    def enviar_email(destinatario_email, destinatario_nome, assunto, corpo_html):
        """Envia um e-mail transacional via Brevo. Nunca levanta exceção pra
        quem chamou — e-mail é um efeito colateral best-effort, uma falha aqui
        (API key ausente, Brevo fora do ar, etc.) não pode derrubar a operação
        principal que disparou o envio (ex: atualização de status do chamado).
        Retorna True/False só pra quem quiser logar/testar."""
        if not BREVO_API_KEY:
            print("[email] BREVO_API_KEY não configurada — e-mail não enviado.")
            return False
        if not destinatario_email:
            return False

        payload = {
            "sender": {"name": BREVO_SENDER_NOME, "email": BREVO_SENDER_EMAIL},
            "to": [{"email": destinatario_email, "name": destinatario_nome or destinatario_email}],
            "subject": assunto,
            "htmlContent": corpo_html,
        }
        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            resposta = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=8)
        except requests.RequestException as erro:
            print(f"[email] Falha ao chamar a API da Brevo: {erro}")
            return False

        if resposta.status_code >= 300:
            print(f"[email] Brevo respondeu {resposta.status_code}: {resposta.text}")
            return False
        return True
