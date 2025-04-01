from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import os
import shutil

# Criar um Blueprint para administração
admin_bp = Blueprint('admin', __name__, template_folder='administracao')

# Pasta para armazenar backups
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# Dados fictícios de usuários (simulando um banco de dados)
usuarios = ["admin", "suporte"]

# 🔹 Rota: Painel de Backup
@admin_bp.route('/backup', methods=['GET'])
def backup():
    return render_template('backup.html')

# 🔹 Rota: Gerar Backup (simplesmente copia os arquivos de chamados)
@admin_bp.route('/backup', methods=['POST'])
def gerar_backup():
    backup_path = os.path.join(BACKUP_DIR, 'backup.zip')
    try:
        shutil.make_archive(backup_path.replace('.zip', ''), 'zip', 'chamados')
        return jsonify({"status": "success", "mensagem": "Backup gerado com sucesso!"})
    except Exception as e:
        return jsonify({"status": "error", "mensagem": f"Erro ao gerar backup: {str(e)}"})

# 🔹 Rota: Restaurar Backup
@admin_bp.route('/restaurar', methods=['GET'])
def restaurar_backup():
    return render_template('restaurar_backup.html')

# 🔹 Rota: Upload do Backup Restaurado
@admin_bp.route('/restaurar', methods=['POST'])
def upload_backup():
    file = request.files.get('file')
    if file:
        try:
            file.save(os.path.join(BACKUP_DIR, file.filename))
            return jsonify({"status": "success", "mensagem": "Backup restaurado com sucesso!"})
        except Exception as e:
            return jsonify({"status": "error", "mensagem": f"Erro ao restaurar backup: {str(e)}"})
    return jsonify({"status": "error", "mensagem": "Erro ao restaurar backup."})

# 🔹 Rota: Gerenciar Usuários
@admin_bp.route('/usuarios', methods=['GET'])
def usuarios_pagina():
    return render_template('usuarios.html', usuarios=usuarios)

# 🔹 Rota: Adicionar Usuário
@admin_bp.route('/usuarios', methods=['POST'])
def adicionar_usuario():
    nome = request.form.get('nome')
    if nome:
        usuarios.append(nome)
        return jsonify({"status": "success", "mensagem": "Usuário adicionado!", "usuario": nome})
    return jsonify({"status": "error", "mensagem": "Erro ao adicionar usuário."})

# 🔹 Rota: Autenticação
@admin_bp.route('/autenticacao', methods=['GET'])
def autenticacao():
    return render_template('autenticacao.html')

# 🔹 Rota: Verificar Senha
@admin_bp.route('/autenticacao', methods=['POST'])
def verificar_senha():
    data = request.form  # Usando request.form, pois estamos lidando com formulário HTML
    senha_correta = "EVOQUESUPPORT"
    if data and data.get("senha") == senha_correta:
        return jsonify({"status": "success", "mensagem": "Autenticação bem-sucedida!"})
    return jsonify({"status": "error", "mensagem": "Senha incorreta."})
