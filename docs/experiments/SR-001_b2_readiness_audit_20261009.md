# SR-001 — Auditoria de prontidão B2 (FM-1) — 09/10/2026

**Issue:** #158 — Scale Reconnaissance v1  
**Natureza:** registro documental de auditoria READ-ONLY; não é implementação, execução de probe nem evidência de generalização.  
**Status:** B2 SELECTED / NOT YET EXECUTED — novo HUMAN GO obrigatório para execução.

## Reentrada reportada pelo Agy

- `main == origin/main` no commit `addb633ed58e0ed9d86e3a2ac7b3ef1c30aaedc6` (PR #183).
- Issue #158 OPEN; nenhuma PR aberta no momento da auditoria.
- Baseline do produto: 1194/1194 GREEN (7.007s).
- Suíte experimental: 40/40 GREEN (0.428s).
- Auditoria realizada sem alterações locais. Os valores acima são evidências **reportadas pelo Agy na sessão**, não reexecução independente neste documento.

## Observações pré-existentes na Tranche 02 congelada

Na observação original da T02, o detector registrou 17 falsos positivos. Quatro (4/17 = 23,53%) pertencem à família HN-DIM / FM-1:

| Caso | Estrato | Diferença física crítica |
| --- | --- | --- |
| CASE-SR001-B-T02-005 | FASTENERS | M12×60 vs M12×70 |
| CASE-SR001-B-T02-013 | VALVES | 3 POL vs 4 POL |
| CASE-SR001-B-T02-029 | ELECTRICAL | seção 16 mm² vs 25 mm² |
| CASE-SR001-B-T02-037 | GENERAL | correia B60 vs B62 |

O quinto caso HN-DIM, CASE-SR001-B-T02-021 (rolamento 6305 vs 6306), já era TN na observação original; logo, **quatro FPs não significam cinco falhas**.

**Hipótese experimental, ainda não comprovada:** um sinal de divergência entre grandezas dimensionais comparáveis poderá suprimir FPs FM-1 sem diminuir o recall positivo. Números compartilhados de normas, classes, pressão ou tensão não demonstram identidade dimensional.

## Riscos de recall destacados pela auditoria

- CASE-011: notações DN 100, DN100 e 4 POL exigem interpretação de designação nominal; não presumir equivalência por conversão aritmética direta.
- CASE-001: M12X45 vs M12-45 — variação de delimitador.
- CASE-002: 3/4 POL X 150 MM vs 3/4 X 150 MM — omissão de unidade.
- CASE-017: informação dimensional assimétrica entre registros.
- CASE-027: comprimento do cabo vs distância sensora são atributos fisicamente distintos.
- CASE-020/028/036: truncamentos podem destruir contexto dimensional.

Essas observações **não especificam ainda um parser ou predicado aprovado**.

## Gates candidatos à futura especificação

1. Definir o escopo do predicado: sonda focal de sensibilidade T02 ou extrator dimensional tipado, com justificativa e limites explícitos.
2. Comparar apenas atributos da mesma natureza física e função cadastral; ausência unilateral não constitui divergência bilateral.
3. Separar tokens de normas, classes e códigos dos atributos dimensionais.
4. Reproduzir o controle B0 par a par nos 40 casos antes da medição contrafactual.
5. Meta primária de segurança: **zero TPs sacrificados** (recall positivo incondicional B2 = B0 = 95% nesta T02, se a seleção de candidatos for preservada).
6. Meta exploratória FM-1: avaliar a supressão dos quatro FPs observados; 4/4 é **objetivo**, não resultado.
7. Relatar mudanças nas demais famílias e conservar os limites de inferência: observação pós-hoc sobre T02 != validação independente != elegibilidade de produção.

## Decisão e próximo passo

**READY somente para detalhar a especificação B2**, não autorização para implementá-lo ou executá-lo. Solicitar deliberação humana explícita antes de qualquer código de probe, teste experimental ou execução. B1 permanece VALID EXPERIMENT / SAFETY GOAL FAILED / NOT ELIGIBLE FOR PRODUCTION; A1, B3–B5 e T03 não foram iniciados nesta sessão.

**Guarda de escopo deste commit:** documentação somente; sem alterações em `src/agent_lab/`, `tests/`, instrumentação, T02 FROZEN, Ground Truth, manifesto ou KPIs. Issue #158 permanece OPEN e experimental/non-functional, weight=0.
