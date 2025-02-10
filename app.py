import os
import math
import smtplib
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders

# Cria o app sem alterar o template_folder (o Flask usará "templates" por padrão)
app = Flask(__name__)
app.secret_key = "supersecretkey"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL = "unidadegoias036@gmail.com"
EMAIL_PASSWORD = "ihymnbwykqscvfgq"
DESTINATARIO = "emerson.silva@academiaevoque.com.br"

# Certifica que as pastas existem
os.makedirs("chamados", exist_ok=True)
os.makedirs("relatorios", exist_ok=True)
os.makedirs("solicitacoes", exist_ok=True)  # Pasta para armazenar solicitações de compra

def gerar_codigo_chamado():
    return "EVQ-" + ''.join(random.choices(string.digits, k=4))

def gerar_protocolo():
    return str(random.randint(100000, 999999)) + '-' + str(random.randint(1, 9))

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
        print(f"Email enviado para {destinatario}")
    except Exception as e:
        print(f"Erro ao enviar o e-mail: {e}")

def enviar_email_confirmacao(nome_solicitante, codigo_chamado, protocolo_chamado, 
                              prioridade, cargo, email_solicitante, telefone, 
                              problema_reportado, descricao, visita_tecnica):
    try:
        assunto = f"Confirmação de Chamado - {codigo_chamado}"
        corpo_email = f"""
Seu chamado foi registrado com sucesso! Aqui estão os detalhes:

Chamado: {codigo_chamado}
Protocolo: {protocolo_chamado}
Prioridade: {prioridade}
Nome do solicitante: {nome_solicitante}
Cargo: {cargo}
E-mail: {email_solicitante}
Telefone: {telefone}
Problema reportado: {problema_reportado}
Descrição: {descricao}
Visita técnica: {visita_tecnica if visita_tecnica else 'Não requisitada'}

⚠️ Caso precise acompanhar o status do chamado, utilize o código acima.

Atenciosamente,
Suporte Evoque!

Por favor, não responda este e-mail, essa é uma mensagem automática!
        """
        enviar_email(assunto, corpo_email, email_solicitante)
        enviar_email(assunto, corpo_email, DESTINATARIO)
    except Exception as e:
        print(f"Erro ao enviar o e-mail de confirmação: {e}")

def gerar_pdf(codigo_chamado, nome_solicitante, descricao, problema_reportado, prioridade, data_abertura, visita_tecnica, status, cargo):
    # Definindo o caminho onde o PDF será salvo
    file_path = f"relatorios/{codigo_chamado}.pdf"
    
    # Caminho da imagem no diretório static/images
    image_path = os.path.join("static", "images", "logo.png")
    
    # Criando o arquivo PDF
    c = canvas.Canvas(file_path, pagesize=letter)
    
    # Adicionando a imagem no PDF
    c.drawImage(image_path, 100, 600, width=400, height=100)
    
    # Reduzindo o tamanho da fonte
    c.setFont("Helvetica", 8)
    
    # Adicionando o texto no PDF
    c.drawString(100, 570, "Olá! Sua cópia foi gerada com sucesso, consulte os dados do seu chamado abaixo.")
    
    # Ajustando o espaçamento e a posição do texto
    y_position = 550
    c.drawString(100, y_position, f"CHAMADO: {codigo_chamado}")
    y_position -= 15
    c.drawString(100, y_position, f"PROTOCOLO: {gerar_protocolo()}")
    y_position -= 15
    c.drawString(100, y_position, f"NOME DO SOLICITANTE: {nome_solicitante}")
    y_position -= 15
    c.drawString(100, y_position, f"CARGO: {cargo}")
    y_position -= 15
    c.drawString(100, y_position, f"DESCRIÇÃO: {descricao}")
    y_position -= 15
    c.drawString(100, y_position, f"PROBLEMA REPORTADO: {problema_reportado}")
    y_position -= 15
    c.drawString(100, y_position, f"PRIORIDADE: {prioridade}")
    y_position -= 15
    c.drawString(100, y_position, f"DATA DE ABERTURA: {data_abertura}")
    y_position -= 15
    c.drawString(100, y_position, f"VISITA TÉCNICA: {visita_tecnica if visita_tecnica else 'Não requisitada'}")
    y_position -= 15
    c.drawString(100, y_position, f"STATUS: {status}")
    
    c.save()
    
    return file_path

def buscar_chamado(codigo_chamado):
    arquivo_chamado = os.path.join('chamados', f'{codigo_chamado}.txt')
    if os.path.exists(arquivo_chamado):
        dados = {}
        with open(arquivo_chamado, 'r') as file:
            for linha in file:
                if ":" in linha:
                    chave, valor = linha.split(":", 1)
                    dados[chave.strip()] = valor.strip()
        chamado = {
            'codigo_chamado': dados.get('Chamado', ''),
            'protocolo': dados.get('Protocolo', ''),
            'prioridade': dados.get('Prioridade', ''),
            'status': dados.get('Status', ''),
            'nome_solicitante': dados.get('Nome do Solicitante', ''),
            'cargo': dados.get('Cargo', ''),
            'problema_reportado': dados.get('Problema Reportado', ''),
            'data_abertura': dados.get('Data de Abertura', ''),
            'visita_tecnica': dados.get('Visita Técnica', 'Não requisitada'),
            'descricao': dados.get('Descricao', '')
        }
        return chamado
    return None

def buscar_chamados_recentes():
    chamados = []
    # Obter todos os arquivos da pasta chamados
    for filename in os.listdir("chamados"):
        if filename.endswith(".txt"):
            codigo_chamado = filename.split('.')[0]
            chamado = buscar_chamado(codigo_chamado)
            if chamado:
                try:
                    if chamado['data_abertura']:
                        chamado['data_abertura'] = datetime.strptime(chamado['data_abertura'], '%d/%m/%Y %H:%M')
                        chamados.append(chamado)
                except ValueError:
                    print(f"Data de abertura inválida para o chamado {codigo_chamado}, ignorando...")
                    continue
    chamados.sort(key=lambda x: x['data_abertura'], reverse=True)
    return chamados[:5]  # Retorna os 5 mais recentes

def contar_chamados():
    total_concluidos = 0
    total_andamento = 0
    total_pendentes = 0
    for filename in os.listdir("chamados"):
        if filename.endswith(".txt"):
            codigo = filename.split('.')[0]
            chamado = buscar_chamado(codigo)
            if chamado:
                status = chamado['status'].strip().lower()
                if status == "concluído":
                    total_concluidos += 1
                elif status == "em andamento":
                    total_andamento += 1
                else:
                    total_pendentes += 1
    return total_concluidos, total_andamento, total_pendentes

def atualizar_status_chamado(codigo_chamado, novo_status):
    """
    Atualiza o status do chamado armazenado em 'chamados/{codigo_chamado}.txt'
    """
    file_path = os.path.join('chamados', f'{codigo_chamado}.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        new_lines = []
        status_atualizado = False
        dados = {}
        for line in lines:
            if line.startswith("Status:"):
                new_lines.append(f"Status: {novo_status}\n")
                status_atualizado = True
            else:
                new_lines.append(line)
            if ":" in line:
                chave, valor = line.split(":", 1)
                dados[chave.strip()] = valor.strip()
        
        if not status_atualizado:
            new_lines.append(f"Status: {novo_status}\n")
        
        with open(file_path, 'w') as f:
            f.writelines(new_lines)

        # Enviar e-mail de notificação
        try:
            assunto = f"Status Atualizado - Chamado {codigo_chamado}"
            corpo_email = f"""
O status do seu chamado foi atualizado:

Código: {codigo_chamado}
Novo status: {novo_status}

Atenciosamente,
Suporte Evoque
            """
            enviar_email(assunto, corpo_email, dados.get('E-mail', ''))
        except Exception as e:
            print(f"Erro ao enviar e-mail de notificação: {e}")

        return True
    return False

def excluir_chamado(codigo_chamado):
    """
    Exclui o chamado armazenado em 'chamados/{codigo_chamado}.txt'
    """
    file_path = os.path.join('chamados', f'{codigo_chamado}.txt')
    if os.path.exists(file_path):
        os.remove(file_path)  # Remove o arquivo do sistema
        return True
    return False

def listar_solicitacoes():
    solicitacoes = []
    pasta_solicitacoes = 'solicitacoes'
    
    for filename in os.listdir(pasta_solicitacoes):
        if filename.endswith('.txt'):
            caminho_arquivo = os.path.join(pasta_solicitacoes, filename)
            with open(caminho_arquivo, 'r') as file:
                dados = {}
                for linha in file:
                    if ":" in linha:
                        chave, valor = linha.split(":", 1)
                        dados[chave.strip()] = valor.strip()
                solicitacoes.append(dados)
    
    return solicitacoes

@app.route('/painel-administrativo')
def painel_administrativo():
    solicitacoes = listar_solicitacoes()  # Obtém todas as solicitações de compras
    return render_template('painel_administrativo.html', solicitacoes=solicitacoes)


@app.route('/')
def index():
    chamados_recentes = buscar_chamados_recentes()  # Obtém os últimos 5 chamados
    concluidos, andamento, pendentes = contar_chamados()  # Conta os chamados por status
    return render_template('index.html', chamados_recentes=chamados_recentes, 
                           concluidos=concluidos, andamento=andamento, pendentes=pendentes)

@app.route('/abrir-chamado', methods=['GET', 'POST'])
def abrir_chamado():
    if request.method == 'POST':
        try:
            nome_solicitante = request.form['nome_solicitante']
            descricao = request.form.get('descricao', '')
            email_solicitante = request.form.get('email')
            telefone_solicitante = request.form.get('telefone')
            problema_reportado = request.form.get('problema')
            internet_item = request.form.get('internet_item', '')
            problema_completo = f"{problema_reportado} - {internet_item}" if internet_item else problema_reportado
            cargo = request.form.get('cargo')
            visita_tecnica = request.form.get('data_visita', '')
            prioridade = "Média"

            problemas_urgentes = ['Catraca', 'Antenas (WI-FI)', 'Teclado', 'Mouse', 'Webcam (Logitech C920)']
            if problema_reportado in problemas_urgentes:
                prioridade = 'Urgente'

            codigo_chamado = gerar_codigo_chamado()
            protocolo_chamado = gerar_protocolo()
            data_abertura = datetime.now().strftime('%d/%m/%Y %H:%M')

            with open(f"chamados/{codigo_chamado}.txt", "w") as file:
                file.write(f"Chamado: {codigo_chamado}\n")
                file.write(f"Protocolo: {protocolo_chamado}\n")
                file.write(f"Prioridade: {prioridade}\n")
                file.write(f"Nome do Solicitante: {nome_solicitante}\n")
                file.write(f"Cargo: {cargo}\n")
                file.write(f"E-mail: {email_solicitante}\n")
                file.write(f"Telefone: {telefone_solicitante}\n")
                file.write(f"Problema Reportado: {problema_completo}\n")
                file.write(f"Data de Abertura: {data_abertura}\n")
                file.write(f"Visita Técnica: {visita_tecnica if visita_tecnica else 'Não requisitada'}\n")
                file.write(f"Descricao: {descricao}\n")
                file.write("Status: Aguardando\n")

            enviar_email_confirmacao(nome_solicitante, codigo_chamado, protocolo_chamado, prioridade,
                                     cargo, email_solicitante, telefone_solicitante, problema_completo,
                                     descricao, visita_tecnica)

            return jsonify({'status': 'success', 'codigo_chamado': codigo_chamado, 'protocolo_chamado': protocolo_chamado})

        except Exception as e:
            print(f"Erro ao abrir o chamado: {e}")
            return jsonify({'status': 'error', 'message': 'Erro ao abrir o chamado'})

    return render_template('abrir_chamado.html')

@app.route('/enviar-ticket', methods=['GET', 'POST'])
def enviar_ticket():
    if request.method == 'POST':
        try:
            # Capturar dados do formulário
            assunto = request.form.get('assunto')
            email_destino = request.form.get('email_destinatario')
            mensagem_html = request.form.get('mensagem', '')  # Garante valor padrão
            
            # Log para depuração
            print(f"Conteúdo HTML recebido: {mensagem_html[:100]}...")  # Exibe os primeiros 100 caracteres

            # Criar mensagem MIME multipart
            msg = MIMEMultipart('alternative')
            msg['From'] = EMAIL
            msg['To'] = email_destino
            msg['Subject'] = assunto

            # Criar versão plain text (fallback)
            texto_simples = "Seu cliente de e-mail não suporta HTML. Mensagem original disponível como anexo."
            parte_texto = MIMEText(texto_simples, 'plain')

            # Criar versão HTML com estrutura básica
            html_formatado = f"""
            <html>
              <head>
                <meta charset="utf-8">
                <style>
                  body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                  .ql-editor {{ white-space: normal !important; }}
                </style>
              </head>
              <body>
                {mensagem_html}
              </body>
            </html>
            """
            parte_html = MIMEText(html_formatado, 'html')

            # Anexar ambas as versões
            msg.attach(parte_texto)
            msg.attach(parte_html)

            # Processar anexos
            anexos = request.files.getlist('arquivos')
            for anexo in anexos:
                if anexo.filename != '':
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(anexo.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{anexo.filename}"'
                    )
                    msg.attach(part)

            # Enviar e-mail com tratamento de erros SMTP
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL, EMAIL_PASSWORD)
                server.send_message(msg)
                print(f"E-mail enviado para {email_destino}")

            return jsonify({
                'status': 'success',
                'message': 'Ticket enviado com sucesso!',
                'destinatario': email_destino
            })
        
        except Exception as e:
            error_msg = f"Erro ao enviar ticket: {str(e)}"
            print(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'detalhes': str(e)
            }), 500

    return render_template('enviar_ticket.html')

@app.route('/admin-painel_zAPBZhw-E77iAFwJO.html', methods=['GET', 'POST'])
def administrar_chamados():
    if request.method == 'POST':
        codigo_chamado = request.form.get('codigo_chamado')
        novo_status = request.form.get('novo_status')
        atualizar_status_chamado(codigo_chamado, novo_status)
        return redirect(url_for('administrar_chamados'))
    
    # Coleta os chamados
    chamados = []
    for filename in os.listdir("chamados"):
        if filename.endswith(".txt"):
            codigo = filename.split('.')[0]
            chamado = buscar_chamado(codigo)
            if chamado and chamado.get('codigo_chamado', '').strip():
                chamados.append(chamado)
    
    # Ordena os chamados
    try:
        chamados = sorted(chamados, 
                         key=lambda x: datetime.strptime(x['data_abertura'], '%d/%m/%Y %H:%M'),
                         reverse=True)
    except Exception as e:
        print(f"Erro ao ordenar chamados: {e}")
    
    # Paginação para chamados
    per_page = 5
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    total = len(chamados)
    total_pages = math.ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    chamados_paginated = chamados[start:end]
    
    # Coleta as solicitações de compra
    solicitacoes = listar_solicitacoes()
    
    return render_template('admin-painel_zAPBZhw-E77iAFwJO.html', 
                         chamados=chamados_paginated, 
                         page=page, 
                         total_pages=total_pages,
                         solicitacoes=solicitacoes)  # Adicionando as solicitações ao template
@app.route('/gerar-relatorio', methods=['GET', 'POST'])
def gerar_relatorio():
    if request.method == 'POST':
        codigo_chamado = request.form.get('codigo_chamado')
        chamado = buscar_chamado(codigo_chamado)
        if chamado:
            # Gera o PDF com os dados do chamado
            file_path = gerar_pdf(
                chamado['codigo_chamado'],
                chamado['nome_solicitante'],
                chamado['descricao'],
                chamado['problema_reportado'],
                chamado['prioridade'],
                chamado['data_abertura'],
                chamado['visita_tecnica'],
                chamado['status'],
                chamado['cargo']
            )
            return send_file(file_path, as_attachment=True)
        else:
            return render_template('gerar_relatorio.html', erro="Chamado não encontrado!")
    return render_template('gerar_relatorio.html')

@app.route('/ver-meus-chamados', methods=['GET', 'POST'])
def ver_meus_chamados():
    chamado = None
    if request.method == 'POST':
        codigo_chamado = request.form.get('codigo_chamado')
        chamado = buscar_chamado(codigo_chamado)
    return render_template('ver_meus_chamados.html', chamado=chamado)

@app.route('/solicitacao-compra', methods=['GET', 'POST'])
def solicitacao_compra():
    if request.method == 'POST':
        # ... (código existente para coletar dados)
        categoria_produto = request.form.get('categoria_produto', '')
        produto = request.form.get('produto', categoria_produto)  # Mantenha esta lógicaf
        # Coleta dos dados do formulário
        cargo = request.form['cargo']
        nome_solicitante = request.form['nome_solicitante']
        unidade = request.form['unidade']
        categoria_produto = request.form.get('categoria_produto', '')
        produto = request.form.get('produto', categoria_produto)
        motivo = request.form['motivo']
        email = request.form['email']
        telefone = request.form['telefone']

        codigo_solicitacao = gerar_codigo_chamado()
        protocolo = gerar_protocolo()
        data_abertura = datetime.now().strftime('%d/%m/%Y %H:%M')

        with open(f"solicitacoes/{codigo_solicitacao}.txt", "w") as file:
            file.write(f"Código solicitação: {codigo_solicitacao}\n")
            file.write(f"Protocolo: {protocolo}\n")
            file.write(f"Data de abertura: {data_abertura}\n")
            file.write(f"Cargo: {cargo}\n")
            file.write(f"Nome do solicitante: {nome_solicitante}\n")
            file.write(f"Unidade: {unidade}\n")
            file.write(f"Produto: {produto}\n")
            file.write(f"Motivo: {motivo}\n")
            file.write(f"E-mail: {email}\n")
            file.write(f"Telefone: {telefone}\n")
            file.write("Status: Aguardando\n")

        # Envio dos e-mails
        try:
            assunto = f"Solicitação de Compra - {codigo_solicitacao}"
            corpo_email = f"""
Solicitação de compra registrada!

Detalhes da solicitação: 
Código: {codigo_solicitacao}
Protocolo: {protocolo}
Data de abertura: {data_abertura}

Informações do solicitante:
Cargo: {cargo}
Nome solicitante: {nome_solicitante}
Unidade: {unidade}
E-mail: {email}
Telefone: {telefone}

Detalhes:
Produto: {produto}
Motivo da solicitação: {motivo}

Status: Aguardando processamento.

Atenciosamente,
Suporte Evoque!
"""
            enviar_email(assunto, corpo_email, email)
            enviar_email(assunto, corpo_email, DESTINATARIO)
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

        # Retorne o JSON com os dados que o JS espera
        return jsonify({
            'status': 'success',
            'codigo_solicitacao': codigo_solicitacao,
            'protocolo': protocolo,
            'data_abertura': data_abertura
        })

    return render_template('solicitacao_compra.html')

@app.route('/atualizar-status-solicitacao', methods=['POST'])
def atualizar_status_solicitacao():
    codigo = request.form.get('codigo')
    novo_status = request.form.get('novo_status')
    caminho_arquivo = os.path.join('solicitacoes', f'{codigo}.txt')
    
    if os.path.exists(caminho_arquivo):
        dados = {}
        with open(caminho_arquivo, 'r') as file:
            for linha in file:
                if ":" in linha:
                    chave, valor = linha.split(":", 1)
                    dados[chave.strip()] = valor.strip()

        # Atualizar o status no arquivo
        with open(caminho_arquivo, 'w') as file:
            for chave, valor in dados.items():
                if chave == "Status":
                    file.write(f"Status: {novo_status}\n")
                else:
                    file.write(f"{chave}: {valor}\n")

        # Enviar e-mail de notificação
        try:
            assunto = f"Status Atualizado - Solicitação {codigo}"
            corpo_email = f"""
Sua solicitação de compra foi atualizada:

Código: {codigo}
Novo Status: {novo_status}

Atenciosamente,
Suporte Evoque
            """
            enviar_email(assunto, corpo_email, dados.get('E-mail', ''))
        except Exception as e:
            print(f"Erro ao enviar e-mail de notificação: {e}")

    return redirect(url_for('administrar_chamados'))

# Rota de exclusão de solicitações (garantir correspondência de nomes)
@app.route('/excluir-solicitacao', methods=['POST'])
def excluir_solicitacao():
    codigo = request.form.get('codigo')  # Nome deve bater com o formulário
    caminho_arquivo = os.path.join('solicitacoes', f'{codigo}.txt')
    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)
    return redirect(url_for('administrar_chamados'))

@app.route('/enviar-ticket-solicitacao', methods=['POST'])
def enviar_ticket_solicitacao():
    if request.method == 'POST':
        try:
            assunto = request.form.get('assunto')
            email_destino = request.form.get('email_destinatario')
            mensagem_html = request.form.get('mensagem', '')

            # Criar mensagem MIME multipart
            msg = MIMEMultipart('alternative')
            msg['From'] = EMAIL
            msg['To'] = email_destino
            msg['Subject'] = assunto

            # Criar versão plain text
            texto_simples = "Seu cliente de e-mail não suporta HTML. Mensagem original disponível como anexo."
            parte_texto = MIMEText(texto_simples, 'plain')

            # Criar versão HTML
            html_formatado = f"""
            <html>
              <head>
                <meta charset="utf-8">
                <style>
                  body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                </style>
              </head>
              <body>
                {mensagem_html}
              </body>
            </html>
            """
            parte_html = MIMEText(html_formatado, 'html')

            # Anexar ambas as versões
            msg.attach(parte_texto)
            msg.attach(parte_html)

            # Enviar e-mail
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL, EMAIL_PASSWORD)
                server.send_message(msg)

            return jsonify({
                'status': 'success',
                'message': 'Ticket enviado com sucesso!',
                'destinatario': email_destino
            })
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"Erro ao enviar ticket: {str(e)}"
            }), 500

@app.route('/excluir-chamado', methods=['POST'])
def excluir():
    codigo_chamado = request.form.get('codigo_chamado')
    if excluir_chamado(codigo_chamado):  # Chama a função de exclusão
        print(f"Chamado {codigo_chamado} excluído com sucesso.")
    else:
        print(f"Erro ao excluir chamado {codigo_chamado}.")
    return redirect(url_for('administrar_chamados'))

# Atualizar status do chamado
@app.route('/atualizar-status-chamado', methods=['POST'])
def atualizar_status():
    codigo_chamado = request.form.get('codigo_chamado')
    novo_status = request.form.get('novo_status')
    atualizar_status_chamado(codigo_chamado, novo_status)
    return redirect(url_for('administrar_chamados'))

if __name__ == '__main__':
    app.run(debug=True)
