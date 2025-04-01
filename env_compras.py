import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuração SMTP exclusiva do env_compras.py
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL = "unidadegoias036@gmail.com"
EMAIL_PASSWORD = "ihymnbwykqscvfgq"
DESTINATARIO = "softworktech1995ef@gmail.com"

def enviar_email_compras(filial, nome_solicitante, descricao_item, quantidade, motivo, email_solicitante, local_entrega, link_produto, codigo_solicitacao, protocolo, anexo=None):
    """
    Função para enviar e-mail com os dados da solicitação de compra da Holding, incluindo código e protocolo.
    """
    try:
        # Criar o objeto da mensagem
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = DESTINATARIO  # Envia para o destinatário principal
        msg['Cc'] = email_solicitante if email_solicitante != EMAIL else ""  # Copia para o e-mail do solicitante
        msg['Subject'] = f"Solicitação de compra - {filial}"

        # Corpo do e-mail com rótulos em negrito, incluindo código e protocolo
        corpo_email = f"""
Nova solicitação de compra.

Código: {codigo_solicitacao}
Protocolo: {protocolo}
Filial: {filial}
Nome do solicitante: {nome_solicitante}
Item:** {descricao_item}
Quantidade: {quantidade}
Motivo:{motivo}
E-mail do solicitante: {email_solicitante}
Local de entrega: {local_entrega}
Link do produto: {link_produto}
"""

        # Adicionar o corpo ao e-mail
        msg.attach(MIMEText(corpo_email, 'plain'))

        # Adicionar anexo, se houver
        if anexo and anexo.filename:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(anexo.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{anexo.filename}"')
            msg.attach(part)

        # Conectar ao servidor SMTP e enviar usando as configurações locais
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"E-mail enviado para {DESTINATARIO} com cópia para {email_solicitante}")
        return True

    except Exception as e:
        print(f"Erro ao enviar o e-mail de compras: {e}")
        return False