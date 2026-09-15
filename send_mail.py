import os
import smtplib
import ssl
from pathlib import Path
from email.message import EmailMessage

from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
caminho_env = Path(__file__).parent / '.env'
load_dotenv(caminho_env)

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', "465")) # Porta padrão do SMTP over SSL

if not SMTP_HOST:
    raise ValueError("Defina SMTP_HOST no arquivo .env")

# ========================
# Função para enviar e-mail
# ========================

def enviar_email(mensagem, remetente, senha):

    # Configura o contexto SSL
    context = ssl.create_default_context()

    # Conecta ao servidor SMTP do Gmail e envia o e-mail
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30) as server:
        server.login(remetente, senha)
        server.send_message(mensagem)