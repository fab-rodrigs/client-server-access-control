# client-server-access-control
Projeto da Disciplina de Redes de Computadores.

# DOCUMENTAÇÃO DO PROTOCOLO DE CONTROLE DE ACESSO (RCP22108)

## [cite_start]1. Formato da Mensagem (Serialização Bitwise) [cite: 75]

A mensagem possui um tamanho fixo de **58 bytes** (464 bits) e é serializada usando operações bitwise e struct (para o campo de Nome).

### 1.1 Estrutura do Cabeçalho e Data/Hora (8 bytes)

Os primeiros 8 bytes (64 bits) contêm o cabeçalho de controle (20 bits) e o timestamp (37 bits). Os bits não utilizados são preenchidos por '0'.

| Campo | Tamanho (bits) | Posição (Exemplo) | Notas |
| :--- | :--- | :--- | :--- |
| Tipo de Mensagem | 1 | Mais significativo | [cite_start]0 = Acesso, 1 = Cadastro [cite: 78] |
| Identificação da Porta | 4 | | [cite_start]Porta P1 a P5 (1 a 5) [cite: 79] |
| Autorização | 1 | | 1 = SIM (Autorizado), 0 = NÃO (Negado). [cite_start]Preenchido APENAS pelo Servidor[cite: 82]. |
| Credencial| 14 | | 4 dígitos (1000-9999). [cite_start]Cliente envia a senha, Servidor envia a nova senha (no cadastro)[cite: 84]. |
| Ano | 11 | | Armazena (Ano - 2000). |
| Mês | 4 | | |
| Dia | 5 | | |
| Hora| 5 | | |
| Minuto | 6 | | |
| Segundo | 6 | Menos significativo | |

### 1.2 Campo de Nome (50 bytes)

[cite_start]O campo 'Nome do usuário' [cite: 83] ocupa os últimos 50 bytes da mensagem (50 caracteres ASCII, preenchidos com nulos se o nome for menor).

## 2. Descrição das Trocas de Mensagem (Fluxo de Comunicação)

O sistema utiliza comunicação TCP/IP, onde cada requisição e resposta ocorre em uma conexão dedicada, que é encerrada após a conclusão da transação.

| Ação | Cliente Envia | Servidor Responde |
| :--- | :--- | :--- |
| **ACESSO** | Tipo=0, Porta, Nome, Credencial | [cite_start]Tipo=0, Porta, Nome, Credencial, **Autorização (1 ou 0)** [cite: 32, 41] |
| **CADASTRO** | Tipo=1, Porta, Nome, Credencial=0 | [cite_start]Tipo=1, Porta, Nome, Autorização=1, **Credencial (Nova gerada)** [cite: 85] |

## 3. Tratamento de Erros de Comunicação

O sistema implementa tratamento de erros em dois níveis:

| Erro | Comportamento do Cliente | Comportamento do Servidor |
| :--- | :--- | :--- |
| **Perda de Conexão** | Tenta conectar uma vez e, se falhar, informa o erro e encerra. | Se houver exceção no `recv()` ou `send()`, a thread do cliente é encerrada imediatamente. |
| **Mensagem Inválida** | Não há tratamento específico; o `recv()` espera um tamanho fixo. | Se o tamanho do pacote recebido for diferente de 58 bytes, o Servidor loga o erro e encerra a conexão. |
| **Encerramento** | A conexão é encerrada imediatamente após receber a resposta do servidor. | A conexão é encerrada pela thread após processar e enviar a resposta. |

---

# MINITUTORIAL: FUNCIONAMENTO DO SISTEMA (Artefato 3)

Este tutorial descreve como iniciar e testar o sistema Cliente/Servidor de controle de acesso.

## Pré-requisitos
* Python 3.x instalado.
* Os arquivos `servidor.py`, `cliente.py`, `protocolo.py`, e `dados_servidor.py` devem estar no mesmo diretório.

## 1. Configuração e Inicialização

### Passo 1: Iniciar o Servidor
Abra o **primeiro terminal** e execute o servidor:
```bash
python servidor.py
