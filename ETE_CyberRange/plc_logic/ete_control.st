(* ============================================================ *)
(* PROJETO: Simulador Virtual de ETE - Cyber Range              *)
(* AUTORA:  Leticia dos Santos Matos (PIBIT/UNIFEI 2025)        *)
(* ORIENT:  Prof. Otávio de Souza Martins Gomes                 *)
(* DESCR:   Lógica de Controle em Structured Text (IEC 61131-3) *)
(*          Máquina de Estados Finitos - OpenPLC Runtime         *)
(* ============================================================ *)

(* ============================================================ *)
(* BLOCO 0: SNAPSHOT (MEMORIA DE ESTADO)                        *)
(* ============================================================ *)
(* Salva o estado atual se o sistema estiver operando normalmente *)
(* (Estados 0 a 4). Isso permite retomar apos falhas.           *)

IF (Estado_Sistema >= 0) AND (Estado_Sistema <= 4) THEN
    Estado_Salvo := Estado_Sistema;
END_IF;


(* ============================================================ *)
(* BLOCO 1: LEITURA E MAPEAMENTO DE SENSORES                    *)
(* ============================================================ *)
(* Converte entradas analogicas em flags booleanas com histerese *)

T1_Vazio := (xiNivel_T1 < 5);
T1_Cheio := (xiNivel_T1 >= 95);

T2_Vazio := (xiNivel_T2 < 5);
T2_Cheio := (xiNivel_T2 >= 80);

T3_Vazio := (xiNivel_T3 < 5);
T3_Cheio := (xiNivel_T3 >= 80);

(* Atribuicao direta para indicador visual do misturador *)
xqMisturador_T2 := xqC3_Motor;


(* ============================================================ *)
(* BLOCO 2: SEGURANCA E INTERTRAVAMENTOS                        *)
(* ============================================================ *)

(* 1. Parada de Emergencia (Prioridade Maxima) *)
IF NOT xiEmergencia THEN
    (* Desliga todos os atuadores imediatamente *)
    xqC1_Motor := FALSE;
    xqC2_Motor := FALSE;
    xqC3_Motor := FALSE;
    xqV1       := FALSE;
    xqV2       := FALSE;
    xqV3       := FALSE;
    xqV4       := FALSE;
    xqSistemaAtivo := FALSE;
    xqLampada_Falha := TRUE;
    Estado_Sistema := -1; (* Estado: Emergencia *)
    RETURN;
END_IF;

(* 2. Botao Stop (Pausa com Retencao de Estado) *)
IF NOT xiBotao_Stop THEN
    xqC1_Motor := FALSE;
    xqC2_Motor := FALSE;
    xqC3_Motor := FALSE;
    xqV1       := FALSE;
    xqV2       := FALSE;
    xqV3       := FALSE;
    xqV4       := FALSE;
    xqSistemaAtivo := FALSE;
    (* NAO zera Estado_Salvo -- retencao de fase ativa *)
    Estado_Sistema := 5; (* Estado: Pausado *)
    RETURN;
END_IF;

(* 3. Reset de Falha *)
IF xiBotao_Reset AND (Estado_Sistema = -1) THEN
    xqLampada_Falha := FALSE;
    Estado_Sistema  := Estado_Salvo; (* Retorna para fase salva *)
END_IF;


(* ============================================================ *)
(* BLOCO 3: MAQUINA DE ESTADOS FINITOS                          *)
(* ============================================================ *)

CASE Estado_Sistema OF

    (* ------ ESTADO 0: AGUARDANDO INICIO ------ *)
    0:
        xqSistemaAtivo := FALSE;
        xqC1_Motor := FALSE;
        xqC2_Motor := FALSE;
        xqC3_Motor := FALSE;
        xqV1 := FALSE; xqV2 := FALSE;
        xqV3 := FALSE; xqV4 := FALSE;

        IF xiBotao_Start THEN
            Estado_Sistema := 1;
        END_IF;

    (* ------ ESTADO 1: ENCHIMENTO T1 (Bomba de Entrada P-01) ------ *)
    1:
        xqSistemaAtivo := TRUE;
        xqC1_Motor := TRUE;   (* Liga Bomba P-01 *)
        xqV1       := TRUE;   (* Abre Valvula de Saida T1 *)
        xqC2_Motor := FALSE;
        xqC3_Motor := FALSE;
        xqV2 := FALSE; xqV3 := FALSE; xqV4 := FALSE;

        IF T1_Cheio THEN
            Estado_Sistema := 2;
        END_IF;

    (* ------ ESTADO 2: FILTRAGEM (Transferencia T1 -> T2) ------ *)
    2:
        xqC1_Motor := FALSE;
        xqV1       := TRUE;   (* Valvula saida T1 aberta *)
        xqV2       := TRUE;   (* Valvula entrada filtro *)
        xqV3       := TRUE;   (* Valvula entrada T2 *)
        xqC2_Motor := TRUE;   (* Bomba de Transferencia P-02 *)
        xqC3_Motor := FALSE;
        xqV4       := FALSE;

        IF T2_Cheio AND T1_Vazio THEN
            Estado_Sistema := 3;
        END_IF;

    (* ------ ESTADO 3: MISTURA (T2 com agitador M-01) ------ *)
    3:
        xqC1_Motor := FALSE;
        xqC2_Motor := FALSE;
        xqC3_Motor := TRUE;   (* Liga Misturador M-01 *)
        xqV1 := FALSE; xqV2 := FALSE;
        xqV3 := FALSE; xqV4 := FALSE;

        (* Timer de mistura controlado externamente (TON no bloco 4) *)
        IF TON_Mistura.Q THEN
            Estado_Sistema := 4;
        END_IF;

    (* ------ ESTADO 4: DESCARGA (T2 -> T3 - tanque final) ------ *)
    4:
        xqC3_Motor := FALSE;
        xqV4       := TRUE;   (* Abre Valvula de Saida T2 *)
        xqC2_Motor := TRUE;   (* Reutiliza bomba para descarga *)

        IF T3_Cheio AND T2_Vazio THEN
            xqC2_Motor := FALSE;
            xqV4       := FALSE;
            xqSistemaAtivo := FALSE;
            Estado_Sistema := 0; (* Ciclo concluido, aguarda novo start *)
        END_IF;

    (* ------ ESTADO 5: PAUSADO ------ *)
    5:
        (* Aguarda xiBotao_Start para retomar do estado salvo *)
        IF xiBotao_Start THEN
            Estado_Sistema := Estado_Salvo;
        END_IF;

END_CASE;
