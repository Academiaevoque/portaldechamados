from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta
import os
from utils import listar_solicitacoes, atualizar_status_solicitacao, excluir_solicitacao, gerar_codigo_sequencial, gerar_protocolo
from app import login_required

compras_bp = Blueprint('compras', __name__, url_prefix='/compras')

def contar_solicitacoes_por_status(solicitacoes):
    concluidas = sum(1 for s in solicitacoes if s.get('Status', '').lower() == 'concluído')
    pendentes = sum(1 for s in solicitacoes if s.get('Status', '').lower() == 'pendente')
    canceladas = sum(1 for s in solicitacoes if s.get('Status', '').lower() == 'cancelado')
    return concluidas, pendentes, canceladas

def filtrar_solicitacoes(solicitacoes, filtro, valor):
    if not solicitacoes:
        return []
    
    if filtro == 'dia':
        data_ref = datetime.now().date()
        return [s for s in solicitacoes if datetime.strptime(s.get('Data', ''), '%d/%m/%Y %H:%M').date() == data_ref]
    elif filtro == 'semana':
        data_ref = datetime.now().date()
        inicio_semana = data_ref - timedelta(days=data_ref.weekday())
        return [s for s in solicitacoes if datetime.strptime(s.get('Data', ''), '%d/%m/%Y %H:%M').date().isocalendar()[1] == data_ref.isocalendar()[1]]
    elif filtro == 'mes':
        data_ref = datetime.now().date()
        return [s for s in solicitacoes if datetime.strptime(s.get('Data', ''), '%d/%m/%Y %H:%M').month == data_ref.month]
    elif filtro == 'nome':
        return [s for s in solicitacoes if valor.lower() in s.get('Nome do solicitante', '').lower()]
    elif filtro == 'codigo':
        return [s for s in solicitacoes if valor.lower() in s.get('Código', '').lower()]
    elif filtro == 'email':
        return [s for s in solicitacoes if valor.lower() in s.get('E-mail', '').lower()]
    return solicitacoes

@compras_bp.route('/painel', methods=['GET', 'POST'])
@login_required
def painel_compras():
    solicitacoes = listar_solicitacoes()
    concluidas, pendentes, canceladas = contar_solicitacoes_por_status(solicitacoes)

    if request.method == 'POST':
        filtro = request.form.get('filtro')
        valor = request.form.get('valor', '').strip()
        if filtro:
            solicitacoes_filtradas = filtrar_solicitacoes(solicitacoes, filtro, valor)
        else:
            solicitacoes_filtradas = solicitacoes
    else:
        solicitacoes_filtradas = solicitacoes

    per_page = 5
    page = int(request.args.get('page', 1))
    total = len(solicitacoes_filtradas)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    solicitacoes_paginated = solicitacoes_filtradas[start:end]

    return render_template('compras_painel.html',
                          solicitacoes=solicitacoes_paginated,
                          concluidas=concluidas,
                          pendentes=pendentes,
                          canceladas=canceladas,
                          page=page,
                          total_pages=total_pages)

@compras_bp.route('/atualizar-status', methods=['POST'])
@login_required
def atualizar_status():
    codigo = request.form.get('codigo')
    novo_status = request.form.get('novo_status')
    atualizar_status_solicitacao(codigo, novo_status)
    return redirect(url_for('compras.painel_compras'))

@compras_bp.route('/excluir', methods=['POST'])
@login_required
def excluir():
    codigo = request.form.get('codigo')
    excluir_solicitacao(codigo)
    return redirect(url_for('compras.painel_compras'))