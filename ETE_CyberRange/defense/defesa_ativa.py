"""
Defesa Ativa ARP Bidirecional - IPS Camada 2
==============================================
Projeto: Simulador Virtual de ETE para Análise de Segurança Cibernética
Autora:  Leticia dos Santos Matos (PIBIT/UNIFEI 2025)
Fonte:   Relatório de Mitigação (fev-mar/2026)

Descrição:
    Sistema de Prevenção de Intrusão (IPS) baseado em Gratuitous ARP.
    Envia continuamente pacotes ARP legítimos para a IHM (FUXA) e para
    o Gateway, "vacinando" as tabelas ARP e impedindo que um atacante
    MitM redirecione o tráfego Modbus TCP.

    Resultado experimental: FUXA manteve leitura estável mesmo sob
    ARP Spoofing duplo + DROP de pacotes Modbus via iptables.

    Executar com: sudo python3 defesa_ativa.py

Dependências: pip install scapy
"""

from scapy.all import sendp, ARP, Ether, getmacbyip
import time

# --- CONFIGURAÇÕES DE REDE ---
IP_GATEWAY = "172.17.0.1"   # Gateway da rede Docker
IP_FUXA    = "172.17.0.3"   # Container IHM/SCADA (FUXA)
INTERVALO  = 0.5             # Frequência de envio dos pacotes (segundos)

print("[*] Lendo a rede para descobrir os MACs reais...")
MAC_GATEWAY_REAL = getmacbyip(IP_GATEWAY)
MAC_FUXA_REAL    = getmacbyip(IP_FUXA)

if not MAC_GATEWAY_REAL or not MAC_FUXA_REAL:
    print("[!] Erro: Não consegui achar os MACs. Verifique a conectividade.")
    exit(1)

print(f"[+] Gateway ({IP_GATEWAY}) MAC Real: {MAC_GATEWAY_REAL}")
print(f"[+] Fuxa    ({IP_FUXA})    MAC Real: {MAC_FUXA_REAL}")

# --- CONSTRUÇÃO DOS ESCUDOS ARP ---
# Escudo 1: Diz para o FUXA qual é o MAC verdadeiro do GATEWAY
escudo_fuxa = (
    Ether(dst=MAC_FUXA_REAL)
    / ARP(
        op=2,                       # ARP Reply (Gratuitous)
        psrc=IP_GATEWAY,
        hwsrc=MAC_GATEWAY_REAL,
        pdst=IP_FUXA,
        hwdst=MAC_FUXA_REAL,
    )
)

# Escudo 2: Diz para o GATEWAY qual é o MAC verdadeiro do FUXA
escudo_gateway = (
    Ether(dst=MAC_GATEWAY_REAL)
    / ARP(
        op=2,
        psrc=IP_FUXA,
        hwsrc=MAC_FUXA_REAL,
        pdst=IP_GATEWAY,
        hwdst=MAC_GATEWAY_REAL,
    )
)

print("[*] Iniciando o Escudo ARP Bidirecional (Defesa Total)...")
print(f"    Frequência: 1 pacote a cada {INTERVALO}s por direção.")
print("    Pressione Ctrl+C para desativar.")

try:
    while True:
        sendp(escudo_fuxa,    verbose=0)
        sendp(escudo_gateway, verbose=0)
        time.sleep(INTERVALO)
except KeyboardInterrupt:
    print("\n[*] Escudo desativado.")
