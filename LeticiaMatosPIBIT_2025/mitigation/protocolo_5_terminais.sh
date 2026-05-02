#!/usr/bin/env bash
# =============================================================================
# Protocolo de Validação da Defesa Ativa - 5 Terminais
# =============================================================================
# Projeto: Simulador Virtual de ETE para Análise de Segurança Cibernética
# Autora:  Leticia dos Santos Matos (PIBIT/UNIFEI 2025)
# Fonte:   Relatório de Mitigação (fev-mar/2026)
#
# Descrição:
#   Documenta a sequência exata de execução para validação experimental.
#   A Defesa Ativa (Terminal 2) deve ser acionada ANTES dos ataques.
#
# Resultado esperado:
#   FUXA mantém leitura estável mesmo sob ARP Spoofing duplo (T3+T4)
#   e DROP de pacotes Modbus via iptables (T5). A defesa vence a corrida
#   pela atualização das tabelas ARP dos nós legítimos.
#
# IPs do ambiente Docker (ajustar conforme necessário):
#   Gateway: 172.17.0.1
#   FUXA:    172.17.0.3
#   OpenPLC: 172.17.0.2 (ou host Windows em 192.168.0.85)
#   Atacante: container kali-rolling
# =============================================================================

echo ""
echo "============================================================"
echo " PROTOCOLO DE VALIDAÇÃO DA DEFESA ATIVA (5 TERMINAIS)"
echo "============================================================"
echo ""
echo "PREPARAÇÃO (no nó atacante) - Limpeza obrigatória:"
echo "---------------------------------------------------"
echo "  iptables -F"
echo "  iptables -X"
echo "  echo 1 > /proc/sys/net/ipv4/ip_forward"
echo ""
echo "TERMINAL 1 - Sistema de Detecção (IDS) - monitoramento passivo"
echo "  python3 detect_mitm.py"
echo "  -> Fica em escuta aguardando anomalias ARP."
echo ""
echo "TERMINAL 2 - DEFESA ATIVA (ativar ANTES do ataque!)"
echo "  sudo python3 defesa_ativa.py"
echo "  -> Imprime MACs reais e inicia Gratuitous ARP a cada 0.5s."
echo ""
echo "TERMINAL 3 - Envenenamento ARP Ida (IHM -> Atacante)"
echo "  arpspoof -i eth0 -t 172.17.0.3 172.17.0.1"
echo "  -> Faz a IHM acreditar que o atacante é o Gateway."
echo ""
echo "TERMINAL 4 - Envenenamento ARP Volta (Gateway -> Atacante)"
echo "  arpspoof -i eth0 -t 172.17.0.1 172.17.0.3"
echo "  -> Cobre a rota de retorno (controle bidirecional)."
echo ""
echo "TERMINAL 5 - Ataque DoS + Corrupção de Pacotes"
echo "  iptables -A FORWARD -p tcp --sport 502 -j DROP"
echo "  python3 attack_simple.py"
echo "  -> Descarta respostas Modbus legítimas e injeta pacotes vazios."
echo ""
echo "RESULTADO ESPERADO:"
echo "  - Terminal 1: Dispara alertas imediatamente ao ativar T3+T4."
echo "  - FUXA:       Mantém leitura estável (sem 'Device CLP error!')."
echo "  - Conclusão:  Defesa Ativa (Camada 2) neutraliza ataque (Camadas 4+7)."
echo ""
