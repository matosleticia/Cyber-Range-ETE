<<<<<<< HEAD
# Cyber Range — Simulador Virtual de ETE para Segurança Cibernética

**Pesquisadora:** Leticia dos Santos Matos — PIBIT 2025 / UNIFEI (Itajubá-MG)  
**Orientador:** Prof. Otávio de Souza Martins Gomes  
**Programa:** PIBIT — Programa Institucional de Bolsas de Iniciação em Desenvolvimento Tecnológico e Inovação  
**Duração:** 12 meses (2025-2026)

---

## Descrição do Projeto

Este repositório consolida o código, algoritmos e documentação técnica do projeto **"Simulador Virtual de Estação de Tratamento de Efluentes (ETE) para Análise de Segurança Cibernética"**.

O projeto implementa um **Cyber Range** baseado em ferramentas open-source que integra:

- **OpenPLC** — lógica de controle em Structured Text (IEC 61131-3), Máquina de Estados Finitos com 7 estados
- **FUXA SCADA** — Interface Homem-Máquina (IHM) web, comunicação Modbus TCP/IP
- **Gêmeo Digital Python** — simulação física dos tanques em tempo real
- **Ambiente Docker** — containers isolados para PLC, SCADA e nó atacante (kali-rolling)

A arquitetura permite validação segura de ataques cibernéticos e contramedidas em ambiente virtualizado, sem risco a infraestruturas reais.

---

## Árvore de Diretórios

```
/
├── resources/                          ← Código autoral da pesquisadora
│   └── ETE_CyberRange/
│       ├── plc_logic/
│       │   └── ete_control.st          ← Lógica ST completa (OpenPLC, IEC 61131-3)
│       ├── digital_twin/
│       │   └── gemeo_digital.py        ← Gêmeo Digital: simulação física dos tanques
│       └── defense/
│           └── defesa_ativa.py         ← IPS: Escudo ARP Bidirecional (Defesa Ativa)
│
└── references/                         ← Algoritmos extraídos dos relatórios de pesquisa
    └── LeticiaMatosPIBIT_2025/
        ├── attack_mitm/
        │   ├── mitm_bomba1.py          ← Exploit MitM v5: manipulação atuador Bomba 1
        │   ├── modbus_sniffer.py       ← Script espião: reconhecimento de assinaturas
        │   └── setup_attacker.sh       ← Setup do container atacante (Docker + iptables)
        ├── fdi_sensor/
        │   └── attack_level.py         ← False Data Injection no sensor de nível
        └── mitigation/
            ├── attack_simple.py        ← Carga maliciosa: corrupção de pacotes Modbus
            └── protocolo_5_terminais.sh ← Procedimento de validação experimental
```

---

## Arquitetura do Cyber Range

```
┌─────────────────────────────────────────────────────────┐
│                    Rede Docker                          │
│                                                         │
│  ┌──────────┐   Modbus TCP    ┌──────────┐             │
│  │  OpenPLC │◄───────────────►│  FUXA    │             │
│  │ (PLC/CLP)│  :502 (sem TLS) │  (SCADA) │             │
│  │ 127.0.0.1│                 │172.17.0.3│             │
│  └────┬─────┘                 └──────────┘             │
│       │                             ▲                   │
│       │ Modbus TCP                  │                   │
│       ▼                             │                   │
│  ┌──────────┐              ┌────────┴───────┐           │
│  │  Gêmeo   │              │   Kali-Rolling │           │
│  │  Digital │              │   (Atacante)   │           │
│  │ (Python) │              │  172.17.0.2    │           │
│  └──────────┘              └────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

**Superfície de Ataque Principal:** Protocolo Modbus TCP/IP sem criptografia e sem autenticação nativas (porta 502), expondo todos os endereços de memória do PLC a leitura e escrita remota.

---

## Ataques Implementados e Validados

| # | Ataque | Vetor | Arquivo | Relatório |
|---|--------|-------|---------|-----------|
| 1 | **MitM + Manipulação de Atuador** | ARP Poisoning + Modbus FC05 | `mitm_bomba1.py` | dez/2025 |
| 2 | **False Data Injection (FDI)** | ARP Poisoning + Modbus FC03/04 | `attack_level.py` | jan/2026 |
| 3 | **DoS por Interrupção de Rota** | iptables DROP porta 502 | `attack_simple.py` | fev/2026 |

**Efeito demonstrado:** *Decoupling* (Desacoplamento de Realidade) — SCADA exibe estado falso enquanto o processo físico diverge silenciosamente.

---

## Defesa Implementada e Validada

| Mecanismo | Camada OSI | Arquivo | Resultado |
|-----------|-----------|---------|-----------|
| **Defesa Ativa ARP Bidirecional** | L2 (Enlace) | `defesa_ativa.py` | FUXA estável sob ataque duplo |
| **IDS Passivo** | L2 (Enlace) | `detect_mitm.py` *(ver docs)* | Alerta imediato ao início do ARP Spoofing |

**Tese central validada:** A imunização da Camada 2 (Enlace) neutraliza completamente ataques nas Camadas 4 (Transporte) e 7 (Aplicação) em infraestruturas legadas que não suportam TLS.

---

## Tabela de Dependências

### Bibliotecas de Software

| Biblioteca | Versão | Uso | Instalação |
|------------|--------|-----|-----------|
| `pymodbus` | ≥ 3.x | Comunicação Modbus TCP (Gêmeo Digital, leitura de coils/registers) | `pip install pymodbus` |
| `scapy` | ≥ 2.5 | Criação e manipulação de pacotes de rede (ataques e defesa ARP) | `pip install scapy` |
| `netfilterqueue` | ≥ 1.0 | Interceptação de pacotes via NFQUEUE do kernel Linux | `pip install netfilterqueue` |
| `struct` | stdlib | Empacotamento/desempacotamento de bytes Modbus | *(nativo Python)* |
| `time` | stdlib | Controle de temporização dos loops | *(nativo Python)* |

### Hardware e Plataformas

| Componente | Tipo | Uso no Projeto |
|------------|------|---------------|
| **OpenPLC Runtime** | Software (open-source) | Execução da lógica ST, exposição Modbus TCP |
| **FUXA SCADA** | Software (open-source) | IHM web, sinótico, leitura/escrita de tags Modbus |
| **Docker Engine** | Plataforma de virtualização | Isolamento de containers (PLC, SCADA, atacante) |
| **Linux Kernel ≥ 4.x** | OS | iptables + NFQUEUE para interceptação de pacotes |
| **Host Windows (opcional)** | Hardware físico | Execução do OpenPLC em testes com PLC real (192.168.0.85) |

### Permissões Especiais

| Requisito | Motivo |
|-----------|--------|
| `sudo` / `root` | Envio de pacotes RAW (Scapy), manipulação de iptables |
| Container flag `--privileged` | Acesso ao subsistema de rede do kernel (iptables, NFQUEUE) |
| `ip_forward = 1` | Roteamento de pacotes entre interfaces no nó atacante |

---

## Mapeamento de Endereços Modbus

### Holding Registers (Sensores / Leitura FC03)

| Variável | End. IEC | End. FUXA | Descrição |
|----------|---------|-----------|-----------|
| `xiNivel_T1` | `%QW2` | 400002 | Nível Tanque 1 (0-100%) |
| `xiNivel_T2` | `%QW4` | 400004 | Nível Tanque 2 (0-100%) |
| `xiNivel_T3` | `%QW6` | 400006 | Nível Tanque 3 (0-100%) |
| `Estado_Sistema` | `%MW8` | 400008 | Estado da Máquina FSM |

### Coils — Comandos (FC05) e Atuadores (FC01)

| Variável | End. IEC | End. FUXA | Função |
|----------|---------|-----------|--------|
| `xiBotao_Start` | `%QX0.0` | 1 | Iniciar Ciclo |
| `xiBotao_Stop` | `%QX0.1` | 2 | Parar/Pausar |
| `xiEmergencia` | `%QX0.2` | 3 | Parada de Emergência (NF) |
| `xqC1_Motor` | `%QX1.0` | 9 | Bomba de Entrada P-01 |
| `xqC2_Motor` | `%QX1.1` | 10 | Bomba de Transferência P-02 |
| `xqC3_Motor` | `%QX1.2` | 11 | Misturador M-01 |
| `xqV1..V4` | `%QX1.3`-`1.6` | 12-15 | Válvulas de processo |

---

## Referências do Projeto

- **Documentação Técnica da Planta Virtual** — nov/2025
- **Testes MitM — Manipulação de Atuador Bomba 1** — dez/2025
- **Relatório Semana 2 — False Data Injection** — jan/2026
- **Relatório de Mitigação — Defesa Ativa ARP Bidirecional** — fev-mar/2026
- Morris & Gao (2014) — *Industrial Control System Cyber Security Research*
- Mathur & Tippenhauer (2016) — *SWaT: A Water Treatment Testbed*
- Beresford (2011) — *Exploiting Siemens S7 PLCs*


