from flask import Blueprint, render_template, session, abort
from datetime import datetime
import os
import math
from functools import wraps

painel_bp = Blueprint('painel', __name__, template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session or session.get('role') != 'admin':
            abort(403)  # Retorna erro 403 se não for admin
        return f(*args, **kwargs)
    return decorated_function

def calcular_metricas(pasta):
    metricas = {
        'total_abertos': 0,
        'total_concluidos': 0,
        'tempos_resolucao': [],
        'sla_violados': 0,
        'sla_atendido': 0
    }
    
    for arquivo in os.listdir(pasta):
        if arquivo.endswith(".txt"):
            caminho = os.path.join(pasta, arquivo)
            with open(caminho, 'r') as f:
                dados = {}
                for linha in f:
                    if ':' in linha:
                        chave, valor = linha.split(':', 1)
                        dados[chave.strip()] = valor.strip()

                is_solicitacao = (pasta == 'solicitacoes')
                
                data_abertura_str = dados.get('Data de Abertura') or dados.get('Data de abertura')
                data_atualizacao_str = dados.get('Data Atualização', data_abertura_str)
                
                if not data_abertura_str:
                    continue
                
                data_abertura = datetime.strptime(data_abertura_str, '%d/%m/%Y %H:%M')
                data_conclusao = datetime.strptime(data_atualizacao_str, '%d/%m/%Y %H:%M') if data_atualizacao_str else data_abertura
                
                status = dados.get('Status', '').lower()
                status_final = (
                    (status in ['concluído', 'concluido']) or 
                    (is_solicitacao and status == 'aprovado')
                )

                if status_final:
                    tempo_resolucao = (data_conclusao - data_abertura).total_seconds() / 3600
                    metricas['tempos_resolucao'].append(tempo_resolucao)
                    metricas['total_concluidos'] += 1
                    
                    limite_sla = 3
                    if tempo_resolucao > limite_sla:
                        metricas['sla_violados'] += 1
                else:
                    metricas['total_abertos'] += 1

    if metricas['total_concluidos'] > 0:
        metricas['sla_atendido'] = round(
            ((metricas['total_concluidos'] - metricas['sla_violados']) / 
             metricas['total_concluidos']) * 100, 1
        )
    
    return metricas

def listar_solicitacoes_recentes():
    solicitacoes = []
    for filename in os.listdir("solicitacoes"):
        if filename.endswith(".txt"):
            caminho = os.path.join("solicitacoes", filename)
            with open(caminho, 'r') as f:
                dados = {}
                for linha in f:
                    if ':' in linha:
                        chave, valor = linha.split(':', 1)
                        dados[chave.strip()] = valor.strip()
                try:
                    dados['data_abertura'] = datetime.strptime(dados['Data de abertura'], '%d/%m/%Y %H:%M')
                    solicitacoes.append(dados)
                except:
                    continue
    return sorted(solicitacoes, key=lambda x: x['data_abertura'], reverse=True)[:5]

@painel_bp.route('/painel-metricas')
@admin_required
def painel_metricas():
    metricas_chamados = calcular_metricas('chamados')
    metricas_solicitacoes = calcular_metricas('solicitacoes')
    
    dados_grafico = {
        'labels': ['Abertos', 'Concluídos', 'SLA Violado'],
        'chamados': [
            metricas_chamados['total_abertos'],
            metricas_chamados['total_concluidos'],
            metricas_chamados['sla_violados']
        ],
        'solicitacoes': [
            metricas_solicitacoes['total_abertos'],
            metricas_solicitacoes['total_concluidos'],
            metricas_solicitacoes['sla_violados']
        ]
    }
    
    solicitacoes = listar_solicitacoes_recentes()
    
    return render_template('painel/painel.html',
                         metricas_chamados=metricas_chamados,
                         metricas_solicitacoes=metricas_solicitacoes,
                         dados_grafico=dados_grafico,
                         solicitacoes=solicitacoes,
                         now=datetime.now())