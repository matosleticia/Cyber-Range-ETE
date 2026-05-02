"""
Modbus TCP Sniffer - Script Espião (Fase de Reconhecimento)
============================================================
Projeto: Simulador Virtual de ETE para Análise de Segurança Cibernética
Autora:  Leticia dos Santos Matos (PIBIT/UNIFEI 2025)
Fonte:   Testes Man-in-the-Middle (dez/2025)

Descrição:
    Script inicial de reconhecimento que apenas escuta o tráfego Modbus
    na porta TCP 502 e imprime os payloads brutos (Raw Data).
    NÃO realiza modificações — usado para identificar assinaturas de
    comando (Write Coil FC05) e status (Read Coil FC02).

    Pré-requisito: ARP Poisoning ativo + NFQUEUE configurado:
        iptables -I FORWARD -j NFQUEUE --queue-num 0

Dependências: pip install scapy netfilterqueue
"""

from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw


def process_packet(packet):
    scapy_packet = IP(packet.get_payload())

    if scapy_packet.haslayer(TCP) and scapy_packet.haslayer(Raw):
        payload = bytes(scapy_packet[Raw].load)
        src = scapy_packet[IP].src
        dst = scapy_packet[IP].dst
        sport = scapy_packet[TCP].sport
        dport = scapy_packet[TCP].dport

        # Filtra apenas tráfego Modbus (porta 502)
        if sport == 502 or dport == 502:
            direction = "PLC -> SCADA" if sport == 502 else "SCADA -> PLC"
            print(f"[{direction}] {src}:{sport} -> {dst}:{dport}")
            print(f"  HEX: {payload.hex()}")
            print(f"  RAW: {payload}")
            print()

    packet.accept()


queue = NetfilterQueue()
queue.bind(0, process_packet)
print("[*] Modbus Sniffer ativo. Capturando na porta 502...")
print("    Pressione Ctrl+C para encerrar.")

try:
    queue.run()
except KeyboardInterrupt:
    print("\n[*] Sniffer encerrado.")
finally:
    queue.unbind()
