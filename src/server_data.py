# ======================================================================
# ARQUIVO: dados_servidor.py
# FUNÇÃO: Gerencia a leitura, escrita e atualização dos arquivos de dados
#         do servidor (Credenciais e Registro).
# ======================================================================

import os
from datetime import datetime

# --- Configuração de Arquivos ---
ARQUIVO_CREDENCIAS = 'credentials.txt'
ARQUIVO_REGISTRO = 'register_acess.txt'

def carregar_credenciais():
    credenciais = {}
    try:
        with open(ARQUIVO_CREDENCIAS, 'r') as f:
            for linha in f:
                linha = linha.strip()
                if not linha: continue
                
                partes = [p.strip() for p in linha.split(',')]
                if len(partes) == 3:
                    codigo, nome, nivel = partes
                    # Armazena usando o código (credencial) como chave
                    credenciais[int(codigo)] = {
                        'nome': nome,
                        'nivel_acesso': int(nivel)
                    }
    except FileNotFoundError:
        return carregar_credenciais() # Tenta carregar novamente
        
    return credenciais

def adicionar_nova_credencial(codigo, nome, nivel_acesso):
    with open(ARQUIVO_CREDENCIAS, 'a') as f:
        linha = f"{codigo},{nome},{nivel_acesso}\n"
        f.write(linha)

def gerar_nova_credencial(nivel_cadastro):
    credenciais_atuais = carregar_credenciais()
    
    # Simplesmente pega a próxima credencial disponível ou gera uma aleatória
    # Implementação básica: procura o maior código e adiciona 1.
    if credenciais_atuais:
        novo_codigo = max(credenciais_atuais.keys()) + 1
    else:
        novo_codigo = 1000 # Primeiro código
        
    if novo_codigo > 9999:
        return None, "Limite de credenciais atingido"
        
    # O nome será preenchido pelo cliente na próxima requisição (aqui é só placeholder)
    novo_nome = "NOVO USUARIO" 

    adicionar_nova_credencial(novo_codigo, novo_nome, nivel_cadastro)
    
    return novo_codigo, novo_nome

# --- 2. GESTÃO DE REGISTRO ---

def registrar_acesso(data_hora, porta_id, codigo_usuario, resultado):
    # Ajusta o resultado para 'autorizado' ou 'negado'
    resultado_str = "autorizado" if resultado == 1 else "negado"
    
    # Formato do log 
    log_line = f"{data_hora}, {porta_id}, {codigo_usuario}, {resultado_str}\n"
    
    with open(ARQUIVO_REGISTRO, 'a') as f:
        f.write(log_line)

# --- 3. FUNÇÃO AUXILIAR DE VERIFICAÇÃO DE ACESSO ---

def verificar_acesso(credenciais, porta_id, codigo_usuario):
    """
    Verifica se o usuário tem permissão para acessar a sala.
    O nível de acesso é retroativo.
    """
    # Nível de acesso da sala é igual ao ID da Porta (P1=1, P2=2, etc.)
    nivel_requerido = porta_id
    
    if codigo_usuario not in credenciais:
        return 0, "Usuário não cadastrado" # Negado (0)

    usuario = credenciais[codigo_usuario]
    nivel_usuario = usuario['nivel_acesso']
    
    # O usuário pode abrir a porta se o seu nível de acesso for MAIOR ou IGUAL ao nível da porta [cite: 19, 51]
    if nivel_usuario >= nivel_requerido:
        return 1, "Acesso autorizado" # Autorizado (1)
    else:
        return 0, f"Nível de acesso ({nivel_usuario}) insuficiente para a porta {porta_id}" # Negado (0)