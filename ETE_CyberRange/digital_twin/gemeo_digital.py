"""
Gêmeo Digital - Simulador Físico da ETE
========================================
Projeto: Simulador Virtual de ETE para Análise de Segurança Cibernética
Autora:  Leticia dos Santos Matos (PIBIT/UNIFEI 2025)
Orient:  Prof. Otávio de Souza Martins Gomes
Fonte:   Documentação Técnica da Planta Virtual (nov/2025)

Descrição:
    Simula o comportamento hidráulico da planta em tempo real.
    Opera em laço infinito com ciclo de atualização configurável.
    Lê atuadores via Modbus TCP, calcula física, escreve sensores de volta.
    Inclui Safety Interlock: nível mínimo de 10% para evitar falha do PLC
    por latência de comunicação.

Dependências: pip install pymodbus
"""

import time
from pymodbus.client import ModbusTcpClient

# --- CONFIGURAÇÕES ---
PLC_IP              = "127.0.0.1"
PLC_PORT            = 502
VELOCIDADE_SIMULACAO = 0.2   # segundos por ciclo
TAXA_ENCHIMENTO     = 6      # unidades % por ciclo com bomba ligada
NIVEL_MINIMO        = 10     # Safety Interlock: piso de simulação (%)

# --- ENDEREÇOS MODBUS (Holding Registers %MW) ---
REG_T1    = 2   # Nível Tanque 1 (%QW2  / FUXA 400002)
REG_T2    = 4   # Nível Tanque 2 (%QW4  / FUXA 400004)
REG_T3    = 6   # Nível Tanque 3 (%QW6  / FUXA 400006)
REG_ESTADO = 8  # Estado da Máquina (%MW8 / FUXA 400008)

# --- ENDEREÇOS MODBUS (Coils %QX - Atuadores) ---
COIL_C1_MOTOR = 9   # Bomba de Entrada  P-01 (%QX1.0)
COIL_C2_MOTOR = 10  # Bomba Transf.     P-02 (%QX1.1)
COIL_C3_MOTOR = 11  # Misturador        M-01 (%QX1.2)
COIL_V1       = 12  # Válvula Saída T1       (%QX1.3)
COIL_V2       = 13  # Válvula Entrada Filtro (%QX1.4)
COIL_V3       = 14  # Válvula Entrada T2     (%QX1.5)
COIL_V4       = 15  # Válvula Saída T2       (%QX1.6)

client = ModbusTcpClient(PLC_IP, port=PLC_PORT)


def ler_atuadores():
    """Lê o estado de todas as bobinas de atuadores do OpenPLC."""
    result = client.read_coils(COIL_C1_MOTOR, count=7)
    if result.isError():
        return None
    bits = result.bits
    return {
        "C1": bits[0],  # Bomba P-01
        "C2": bits[1],  # Bomba P-02
        "C3": bits[2],  # Misturador
        "V1": bits[3],  # Válvula T1 saída
        "V2": bits[4],  # Válvula filtro
        "V3": bits[5],  # Válvula T2 entrada
        "V4": bits[6],  # Válvula T2 saída
    }


def ler_niveis():
    """Lê os níveis atuais dos tanques dos holding registers."""
    result = client.read_holding_registers(REG_T1, count=4)
    if result.isError():
        return None
    regs = result.registers
    return {
        "T1": regs[0],
        "T2": regs[1],
        "T3": regs[2],
        "estado": regs[3],
    }


def calcular_fisica(niveis, atuadores):
    """
    Calcula a variação de nível de cada tanque baseado nos atuadores.
    Aplica Safety Interlock: nível mínimo de NIVEL_MINIMO %.
    """
    t1 = niveis["T1"]
    t2 = niveis["T2"]
    t3 = niveis["T3"]

    # --- T1: Bomba C1 + Válvula V1 drenam T1 ---
    if atuadores["C1"] and atuadores["V1"]:
        # Modo enchimento externo: simulamos entrada de efluente bruto
        t1 = min(100, t1 + TAXA_ENCHIMENTO)
    elif atuadores["V1"] and not atuadores["C1"]:
        # Drenagem passiva por gravidade (mais lenta)
        t1 = max(NIVEL_MINIMO, t1 - int(TAXA_ENCHIMENTO / 2))

    # --- T2: Alimentado por C2+V3, drenado por V4 ---
    if atuadores["C2"] and atuadores["V3"]:
        delta_t2 = TAXA_ENCHIMENTO
        t2 = min(100, t2 + delta_t2)
        t1 = max(NIVEL_MINIMO, t1 - delta_t2)   # transferência T1->T2
    if atuadores["V4"] and atuadores["C2"]:
        delta_desc = TAXA_ENCHIMENTO
        t2 = max(NIVEL_MINIMO, t2 - delta_desc)
        t3 = min(100, t3 + delta_desc)           # transferência T2->T3

    return int(t1), int(t2), int(t3)


def escrever_sensores(t1, t2, t3):
    """Escreve os níveis calculados de volta nos holding registers do PLC."""
    client.write_registers(REG_T1, [t1, t2, t3])


def iniciar_simulacao():
    if not client.connect():
        print(f"Erro: Falha ao conectar em {PLC_IP}:{PLC_PORT}")
        return

    print(f"Simulador Conectado. Proteções de Nível Ativas (mínimo {NIVEL_MINIMO}%).")
    print("-" * 70)

    try:
        while True:
            # 1. Leitura de Atuadores
            atuadores = ler_atuadores()
            if atuadores is None:
                print("[WARN] Falha ao ler atuadores. Tentando novamente...")
                time.sleep(VELOCIDADE_SIMULACAO)
                continue

            # 2. Leitura dos Níveis Atuais
            niveis = ler_niveis()
            if niveis is None:
                print("[WARN] Falha ao ler níveis. Tentando novamente...")
                time.sleep(VELOCIDADE_SIMULACAO)
                continue

            # 3. Cálculo Físico
            t1, t2, t3 = calcular_fisica(niveis, atuadores)

            # 4. Escrita de Sensores
            escrever_sensores(t1, t2, t3)

            print(
                f"T1={t1:>3}% | T2={t2:>3}% | T3={t3:>3}% | "
                f"C1={int(atuadores['C1'])} C2={int(atuadores['C2'])} "
                f"M={int(atuadores['C3'])} V1-4={int(atuadores['V1'])}"
                f"{int(atuadores['V2'])}{int(atuadores['V3'])}{int(atuadores['V4'])}"
            )

            time.sleep(VELOCIDADE_SIMULACAO)

    except KeyboardInterrupt:
        print("\n[*] Simulador encerrado pelo usuário.")
    finally:
        client.close()


if __name__ == "__main__":
    iniciar_simulacao()
