from flask import Blueprint, request, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL, EMAIL_PASSWORD

email_bp = Blueprint('email', __name__)

def enviar_email(assunto, corpo_email, destinatario):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo_email, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, destinatario, msg.as_string())
        server.quit()

        print(f"E-mail enviado com sucesso para {destinatario}")
        return True
    except Exception as e:
        print(f"Erro ao enviar o e-mail: {e}")
        return False

@email_bp.route('/enviar-ticket', methods=['POST'])
def enviar_ticket():
    data = request.json
    assunto = data.get('assunto')
    corpo_email = data.get('corpo_email')
    destinatario = data.get('destinatario')

    if enviar_email(assunto, corpo_email, destinatario):
        return jsonify({"message": "Ticket enviado com sucesso!", "status": "success"})
    else:
        return jsonify({"message": "Falha ao enviar o ticket.", "status": "error"}), 500
