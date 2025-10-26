# ======================================================================
# ARQUIVO: protocolo.py
# FUNÇÃO: Define o formato da mensagem e as funções de empacotamento/
#         desempacotamento usando bitwise, conforme especificado.
# ======================================================================

import struct
import datetime

# --- 1. CONSTANTES DO PROTOCOLO (Tamanho em Bits) ---
# Total de 457 bits (57.125 Bytes), arredondado para 58 bytes para comunicação.

# A. Cabeçalho de Controle (20 bits)
TAM_TIPO_MSG = 1     # 0=Acesso, 1=Cadastro 
TAM_PORTA = 4        # Identificação da porta 
TAM_AUTORIZACAO = 1  # 0=Negado, 1=Autorizado (apenas servidor preenche) 
TAM_CREDENCIAL = 14  # 1000 a 9999 (14 bits > 9999) 

# B. Data e Hora (37 bits)
# Definimos os tamanhos com base nos valores máximos:
TAM_DIA = 5          # 0-31
TAM_MES = 4          # 0-12
TAM_ANO = 11         # Permite anos até 2048 (iremos armazenar 'Ano - 2000') 
TAM_HORA = 5         # 0-23
TAM_MINUTO = 6       # 0-59
TAM_SEGUNDO = 6      # 0-59

# C. Nome do Usuário (50 caracteres)
TAM_NOME_BYTES = 50  # 50 caracteres * 1 byte/char (ASCII) 

# D. Tamanho Total da Mensagem
TAM_CABECALHO_E_DATA_BYTES = 8 # Arredondando 57 bits para 8 bytes
TAM_MSG_TOTAL = TAM_CABECALHO_E_DATA_BYTES + TAM_NOME_BYTES # 58 bytes

# --- 2. FUNÇÕES DE EMPACOTAMENTO ---

def empacotar_requisicao_cliente(tipo_msg, porta, nome_usuario, credencial):
    """
    Empacota os dados da requisição do cliente em uma sequência de 58 bytes.
    A autorização é sempre 0 (NEGADO) na requisição do cliente.
    """
    
    # 1. Obter a Data e Hora atual
    agora = datetime.datetime.now()
    dia, mes, ano = agora.day, agora.month, agora.year
    hora, minuto, segundo = agora.hour, agora.hour, agora.second

    # --- 1. Montagem dos 20 bits do Cabeçalho de Controle ---
    # Ordem: Tipo(1) | Porta(4) | Autorizacao(1) | Credencial(14)
    
    cabecalho = 0
    # Tipo de Mensagem
    cabecalho = (cabecalho | tipo_msg) << TAM_PORTA
    # ID da Porta
    cabecalho = (cabecalho | porta) << TAM_AUTORIZACAO
    # Autorização (sempre 0 na requisição)
    cabecalho = (cabecalho | 0) << TAM_CREDENCIAL
    # Credencial
    cabecalho = (cabecalho | credencial)

    print(cabecalho)

    # --- 2. Montagem dos 37 bits de Data e Hora ---
    # Ordem: Ano(11) | Mes(4) | Dia(5) | Hora(5) | Minuto(6) | Segundo(6)
    
    data_hora = 0
    # Ano (somente o offset)
    data_hora = (data_hora | (ano - 2000)) << TAM_MES
    # Mês
    data_hora = (data_hora | mes) << TAM_DIA
    # Dia
    data_hora = (data_hora | dia) << TAM_HORA
    # Hora
    data_hora = (data_hora | hora) << TAM_MINUTO
    # Minuto
    data_hora = (data_hora | minuto) << TAM_SEGUNDO
    # Segundo
    data_hora = (data_hora | segundo)

    print(data_hora)

    # --- 3. Serialização para Bytes (8 bytes) ---
    # Usamos 3 bytes para o cabeçalho e 5 bytes para data/hora (total de 8)
    
    # 3 bytes para o cabeçalho (24 bits) - Big Endian
    dados_controle = cabecalho.to_bytes(3, 'big')
    # 5 bytes para data/hora (40 bits) - Big Endian
    dados_data_hora = data_hora.to_bytes(5, 'big')
    
    # --- 4. Empacotamento do Nome (50 bytes) ---
    # Formato '50s' (string de 50 bytes, preenchida com nulos)
    nome_bytes = struct.pack(f'{TAM_NOME_BYTES}s', nome_usuario.encode('ascii'))
    
    # --- 5. Mensagem Final (58 bytes) ---
    mensagem_bytes = dados_controle + dados_data_hora + nome_bytes
    
    return mensagem_bytes

def empacotar_resposta_servidor(req_bytes, autorizacao, nova_credencial=0):
    """
    Modifica a mensagem de requisição (req_bytes) para criar uma resposta.
    Apenas modifica o campo Autorização e (opcionalmente) a Credencial.
    """
    
    # 1. Desempacota os 3 bytes de controle para acesso
    cabecalho = int.from_bytes(req_bytes[:3], 'big')
    
    # 2. Zera os campos Autorização e Credencial (para garantir que só a nova info seja usada)
    
    # Máscara para limpar 1 bit de Autorizacao e 14 bits de Credencial
    mascara_limpeza = ~(((1 << 1) - 1) << TAM_CREDENCIAL | ((1 << TAM_CREDENCIAL) - 1))
    
    # Aplica a limpeza
    novo_cabecalho = cabecalho & mascara_limpeza

    # 3. Adiciona a nova Autorização e Credencial (se houver)
    
    # Posição da Autorização (shift)
    shift_autorizacao = TAM_CREDENCIAL
    
    # Posição da Credencial (shift)
    shift_credencial = 0
    
    # Adiciona a Autorização (1 bit)
    novo_cabecalho |= (autorizacao << shift_autorizacao)
    
    # Adiciona a Nova Credencial (14 bits)
    novo_cabecalho |= (nova_credencial << shift_credencial)

    # 4. Reconstrói a mensagem
    dados_controle_resposta = novo_cabecalho.to_bytes(3, 'big')
    
    # A resposta é a nova parte de controle + o resto da mensagem original (data/hora + nome)
    mensagem_bytes_resposta = dados_controle_resposta + req_bytes[3:]
    
    return mensagem_bytes_resposta


# --- 3. FUNÇÃO DE DESEMPACOTAMENTO ---

def desempacotar_mensagem(mensagem_bytes):
    """
    Desempacota uma sequência de 58 bytes e retorna um dicionário de dados.
    """
    
    # --- 1. Desempacota o Nome do Usuário (50 bytes) ---
    # Da posição 8 até o final
    nome_bytes = mensagem_bytes[TAM_CABECALHO_E_DATA_BYTES:]
    # Desempacota e remove caracteres nulos de preenchimento
    nome_usuario = struct.unpack(f'{TAM_NOME_BYTES}s', nome_bytes)[0].decode('ascii').strip('\x00')
    
    # --- 2. Extrai os 8 bytes de Controle e Data/Hora ---
    cabecalho_data_bytes = mensagem_bytes[:TAM_CABECALHO_E_DATA_BYTES]
    
    # Extrai os dois inteiros (3 e 5 bytes, preenchidos) - Big Endian
    cabecalho = int.from_bytes(cabecalho_data_bytes[:3], 'big') # 3 bytes (Controle)
    data_hora = int.from_bytes(cabecalho_data_bytes[3:], 'big') # 5 bytes (Data/Hora)
    
    # --- 3. Extrai os campos do Cabeçalho (do MENOS significativo para o MAIS) ---
    
    # Credencial (14 bits)
    credencial = cabecalho & ((1 << TAM_CREDENCIAL) - 1)
    cabecalho >>= TAM_CREDENCIAL
    
    # Autorização (1 bit)
    autorizacao = cabecalho & ((1 << TAM_AUTORIZACAO) - 1)
    cabecalho >>= TAM_AUTORIZACAO
    
    # Porta (4 bits)
    porta = cabecalho & ((1 << TAM_PORTA) - 1)
    cabecalho >>= TAM_PORTA
    
    # Tipo de Mensagem (1 bit)
    tipo_msg = cabecalho & ((1 << TAM_TIPO_MSG) - 1)
    
    # --- 4. Extrai os campos de Data/Hora (do MENOS significativo para o MAIS) ---
    
    # Segundo (6 bits)
    segundo = data_hora & ((1 << TAM_SEGUNDO) - 1)
    data_hora >>= TAM_SEGUNDO
    
    # Minuto (6 bits)
    minuto = data_hora & ((1 << TAM_MINUTO) - 1)
    data_hora >>= TAM_MINUTO
    
    # Hora (5 bits)
    hora = data_hora & ((1 << TAM_HORA) - 1)
    data_hora >>= TAM_HORA
    
    # Dia (5 bits)
    dia = data_hora & ((1 << TAM_DIA) - 1)
    data_hora >>= TAM_DIA
    
    # Mês (4 bits)
    mes = data_hora & ((1 << TAM_MES) - 1)
    data_hora >>= TAM_MES
    
    # Ano (11 bits) - Adiciona o offset
    ano = (data_hora & ((1 << TAM_ANO) - 1)) + 2000
    
    # --- 5. Retorna os dados ---
    return {
        "tipo_msg": tipo_msg, # 0 para Acesso, 1 para Cadastro
        "porta": porta,
        "autorizacao": autorizacao, # 0 para Negado, 1 para Autorizado
        "credencial": credencial,
        "nome_usuario": nome_usuario,
        "data_hora": f"{dia:02d}/{mes:02d}/{ano} {hora:02d}:{minuto:02d}:{segundo:02d}"
    }
