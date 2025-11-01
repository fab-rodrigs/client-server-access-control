# ======================================================================
# ARQUIVO: cliente.py
# FUNÇÃO: Simula o terminal de acesso em uma porta (P1 a P5).
#         Recebe entrada do usuário, envia requisição e imprime resposta.
# ======================================================================

import socket
import sys

import protocol
from server_data import ARQUIVO_CREDENCIAS

# rede
HOST = '127.0.0.1'  # mesmo endereço do servidor
PORT = 65432        # mesma porta do servidor

def obter_identificacao_porta():
    while True:
        try:
            porta_str = input("Simulando qual Porta (P1 a P5)? Digite o número (1 a 5): ")
            porta_id = int(porta_str)
            if 1 <= porta_id <= 5:
                return porta_id
            else:
                print("ID de porta inválido. Por favor, digite um número entre 1 e 5.")
        except ValueError:
            print("Entrada inválida. Digite apenas o número da porta.")

def obter_dados_usuario(porta_id):
    nome = input("Digite seu Nome: ").strip()
    
    while len(nome) > protocol.TAM_NOME_BYTES or not nome:
        print(f"Nome inválido. Máximo de {protocol.TAM_NOME_BYTES} caracteres e não pode ser vazio.")
        nome = input("Digite seu Nome: ").strip()
        
    while True:
        acao = input("Deseja (A)cessar ou (C)adastrar-se? [A/C]: ").upper()
        if acao == 'A':
            tipo_msg = 0 # ACESSO
            try:
                credencial = int(input("Digite sua Credencial (4 dígitos): "))
                if 1000 <= credencial <= 9999:
                    return tipo_msg, nome, credencial
                else:
                    print("Credencial deve ser um número entre 1000 e 9999.")
            except ValueError:
                print("Entrada inválida para credencial.")
        elif acao == 'C':
            print(f"Atenção: Seu nível de acesso será definido pela Porta P{porta_id}.")
            tipo_msg = 1 # CADASTRO
            credencial = 0
            return tipo_msg, nome, credencial
        else:
            print("Opção inválida. Escolha 'A' para Acessar ou 'C' para Cadastrar-se.")

def iniciar_cliente():    
    # 1. OBTER DADOS INICIAIS
    porta_id = obter_identificacao_porta()
    tipo_msg, nome, credencial_envio = obter_dados_usuario(porta_id)

    print("-" * 40)
    print(f"Conectando ao servidor...")

    # 2. CONFIGURAR E CONECTAR O SOCKET
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # SOCK_STREAM (TCP)
        client_socket.connect((HOST, PORT))
    except Exception as e:
        print(f"ERRO: Não foi possível conectar ao servidor em {HOST}:{PORT}. Certifique-se de que o servidor está rodando.")
        print(f"Detalhe do erro: {e}")
        return

    # 3. EMPACOTAR E ENVIAR DADOS
    try:
        # criando pacote de 58 bytes
        requisicao_bytes = protocol.empacotar_requisicao_cliente(
            tipo_msg, porta_id, nome, credencial_envio
        )
        
        client_socket.sendall(requisicao_bytes)
        
        # 4. RECEBER A RESPOSTA
        # cliente espera a mesma quantidade de bytes (58)
        resposta_bytes = client_socket.recv(protocol.TAM_MSG_TOTAL)
        
        if len(resposta_bytes) != protocol.TAM_MSG_TOTAL:
            print("ERRO: Resposta incompleta ou inválida recebida do servidor.")
            return

        # 5. DESEMPACOTAR E IMPRIMIR RESPOSTA
        resposta_dados = protocol.desempacotar_mensagem(resposta_bytes)
        
        print("-" * 40)
        
        if tipo_msg == 0: # ACESSO
            if resposta_dados['autorizacao'] == 1:
                print(f"✅ ACESSO AUTORIZADO! Porta P{porta_id} aberta.")
            else:
                print("❌ ACESSO NEGADO! Credencial ou nível insuficiente.")
                
        elif tipo_msg == 1: # CADASTRO
            if resposta_dados['autorizacao'] == 1:
                nova_credencial = resposta_dados['credencial']
                print(f"✅ CADASTRO REALIZADO COM SUCESSO na Porta P{porta_id}!")
                print(f"Sua nova Credencial é: {nova_credencial}")
                print(f"(Seu Nível de Acesso é {porta_id}). Use esta credencial para acessar.")
            else:
                print("❌ CADASTRO NEGADO. Motivo desconhecido ou falha do servidor.")

    except Exception as e:
        print(f"Erro durante a comunicação: {e}")
        
    finally:
        # 6. ENCERRAR CONEXÃO
        client_socket.close()
        print("-" * 40)
        print("Conexão encerrada.")

if __name__ == '__main__':
    iniciar_cliente()