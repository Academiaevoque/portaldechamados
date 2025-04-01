import os
from datetime import datetime

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

def atualizar_status_solicitacao(codigo, novo_status):
    caminho_arquivo = os.path.join('solicitacoes', f'{codigo}.txt')
    if os.path.exists(caminho_arquivo):
        dados = {}
        with open(caminho_arquivo, 'r') as file:
            for linha in file:
                if ":" in linha:
                    chave, valor = linha.split(":", 1)
                    dados[chave.strip()] = valor.strip()
        with open(caminho_arquivo, 'w') as file:
            for chave, valor in dados.items():
                if chave == "Status":
                    file.write(f"Status: {novo_status}\n")
                else:
                    file.write(f"{chave}: {valor}\n")
        return True
    return False

def excluir_solicitacao(codigo):
    caminho_arquivo = os.path.join('solicitacoes', f'{codigo}.txt')
    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)
        return True
    return False

def gerar_codigo_sequencial(pasta="solicitacoes", prefixo="EVQ-"):
    seq = 1
    if os.path.exists(pasta):
        for filename in os.listdir(pasta):
            if filename.startswith(prefixo) and filename.endswith(".txt"):
                try:
                    numero = int(filename[len(prefixo):-4])
                    seq = max(seq, numero + 1)
                except ValueError:
                    pass
    return f"{prefixo}{seq:04d}"

def gerar_protocolo():
    import random
    return str(random.randint(100000, 999999)) + '-' + str(random.randint(1, 9))