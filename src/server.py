# ======================================================================
# ARQUIVO: servidor.py
# FUNÇÃO: Aplicação central de controle de acesso. Ouve por conexões,
#         processa requisições de acesso/cadastro e gerencia dados.
# ======================================================================

import socket
import threading
import sys
from datetime import datetime

# Importa os módulos criados nas etapas anteriores
import protocol
import server_data

# --- Configurações de Rede ---
HOST = '127.0.0.1'  # Servidor rodando na própria máquina (localhost)
PORT = 65432        # Porta arbitrária (pode ser qualquer uma acima de 1024)
MAX_CONEXOES = 5    # Número máximo de clientes esperando na fila

# Inicializa o banco de dados (arquivos TXT)
server_data.carregar_credenciais()

def processar_requisicao(conexao, endereco):
    """
    Função principal que lida com a requisição de um cliente específico.
    """
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Conexão estabelecida com {endereco}")

    # Garante que a conexão será encerrada ao final
    try:
        # 1. RECEBER OS DADOS
        # O servidor espera exatamente o tamanho da mensagem definida (58 bytes)
        dados_recebidos = conexao.recv(protocol.TAM_MSG_TOTAL)
        
        if len(dados_recebidos) != protocol.TAM_MSG_TOTAL:
            print(f"[{endereco}] Erro: Tamanho de mensagem inválido ({len(dados_recebidos)} bytes). Encerrando.")
            return

        # 2. DESEMPACOTAR A MENSAGEM
        dados = protocol.desempacotar_mensagem(dados_recebidos)
        
        tipo = dados['tipo_msg']
        porta_id = dados['porta']
        credencial = dados['credencial']
        nome_usuario = dados['nome_usuario']
        data_hora_log = dados['data_hora']
        
        resultado_autorizacao = 0 # Assume negado inicialmente
        
        # 3. PROCESSAR A REQUISIÇÃO (ACESSO ou CADASTRO)
        
        if tipo == 0: # REQUISIÇÃO DE ACESSO
            
            # Carrega a lista de credenciais
            credenciais = server_data.carregar_credenciais()
            
            # Verifica o acesso
            resultado_autorizacao, motivo = server_data.verificar_acesso(
                credenciais, porta_id, credencial
            )
            
            print(f"[{endereco} - P{porta_id}] ACESSO {nome_usuario} ({credencial}): {'AUTORIZADO' if resultado_autorizacao else 'NEGADO'} - {motivo}")
            
            # A credencial de resposta é a mesma credencial de acesso
            credencial_resposta = credencial 

        elif tipo == 1: # REQUISIÇÃO DE CADASTRO
            
            # Porta onde o cadastro foi feito define o Nível de Acesso (Ex: P3 = Nível 3)
            nivel_cadastro = porta_id 
            
            # Gera a nova credencial e atualiza o nome
            nova_credencial, msg = server_data.gerar_nova_credencial(nivel_cadastro)
            
            if nova_credencial:
                # Atualiza o nome do novo usuário no arquivo
                server_data.adicionar_nova_credencial(nova_credencial, nome_usuario, nivel_cadastro)
                
                resultado_autorizacao = 1 # Cadastro realizado com sucesso
                credencial_resposta = nova_credencial
                motivo = f"Cadastro OK. Credencial: {nova_credencial}, Nível: {nivel_cadastro}"
            else:
                resultado_autorizacao = 0 # Falha no cadastro
                credencial_resposta = 0
                motivo = f"Falha no cadastro: {msg}"
                
            print(f"[{endereco} - P{porta_id}] CADASTRO {nome_usuario}: {'SUCESSO' if resultado_autorizacao else 'FALHA'} - {motivo}")
            
        # 4. REGISTRAR A TENTATIVA DE ACESSO/CADASTRO
        server_data.registrar_acesso(
            data_hora_log,
            f"P{porta_id}",
            credencial_resposta if tipo == 1 else credencial, # Loga a credencial gerada no cadastro
            resultado_autorizacao
        )

        # 5. ENVIAR A RESPOSTA
        resposta_bytes = protocol.empacotar_resposta_servidor(
            dados_recebidos, 
            resultado_autorizacao, 
            credencial_resposta
        )
        conexao.sendall(resposta_bytes)

    except Exception as e:
        print(f"[{endereco}] Erro no processamento da requisição: {e}")
        # Comportamento em caso de perda de conexão (como solicitado na especificação): 
        # Simplesmente encerra a thread para esta conexão.
        
    finally:
        # 6. ENCERRAR CONEXÃO
        print(f"[{endereco}] Conexão encerrada.")
        conexao.close() # Conexões são encerradas após a troca de mensagens[cite: 74].

def iniciar_servidor():
    """
    Configura e inicia o servidor TCP, ouvindo por conexões.
    """
    
    # 1. Configura o socket
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_CONEXOES)
    except Exception as e:
        print(f"ERRO FATAL: Falha ao iniciar o servidor. Certifique-se de que a porta {PORT} não está em uso. Erro: {e}")
        sys.exit(1)

    print("-" * 50)
    print(f"Servidor de Controle de Acesso rodando em TCP {HOST}:{PORT}")
    print(f"Aguardando conexões de clientes...")
    print("-" * 50)

    # 2. Loop principal de aceitação de conexões
    while True:
        try:
            # Aceita uma nova conexão
            conexao, endereco = server_socket.accept()
            
            # Cria uma nova thread para lidar com o cliente, permitindo que o servidor aceite outros
            cliente_thread = threading.Thread(
                target=processar_requisicao, 
                args=(conexao, endereco)
            )
            cliente_thread.start()
            
        except KeyboardInterrupt:
            # Captura CTRL+C para encerrar
            print("\nServidor encerrado por comando do usuário (Ctrl+C).")
            server_socket.close()
            break
        except Exception as e:
            print(f"Erro ao aceitar conexão: {e}")
            
if __name__ == '__main__':
    iniciar_servidor()