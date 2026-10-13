# SR-001 / Issue #158 — B2/FM-1: contrato verificável pré-execução (13/10/2026)

**Status:** PROPOSED — PRE-EXECUTION REVIEW / NO HUMAN GO.  
**Natureza:** somente documento de engenharia; nenhuma implementação, teste ou execução de B2.

## 1. Reentrada e problema mensurável
Origem: PROJECT_COMPASS, especificação B2 de 10/10 e revisão de 11/10. Na T02 congelada, B0 incondicional = TP 19, FP 17, TN 3, FN 1 (40 pares). A taxonomia forense atribui quatro FPs a FM-1 (005, 013, 029, 037), mas a análise da própria T02 é *post-hoc*. B1 demonstrou o risco de um veto amplo: 17 FPs suprimidos com 7 TPs perdidos (recall 95% → 60%). A B2 deve testar **dimensão física bilateral comparável**, não PN divergente de modo indiscriminado.

## 2. Contrato de observação proposto
O detector experimental deve permanecer inalterado até novo HUMAN GO explícito. Em futura implementação autorizada, a sonda recebe somente os dois registros brutos e o contexto inferível desses registros, nunca label, case_id, Ground Truth ou resultado esperado. Deve produzir:
- `DISAGREEMENT` somente quando **mesmo atributo funcional** foi identificado nos dois lados, comparabilidade demonstrada e valores incompatíveis;
- `NO_DISAGREEMENT` quando a evidência bilateral comparável foi examinada e não demonstra incompatibilidade;
- `UNKNOWN` quando atributo ausente, unilateral, truncado, interpretação múltipla ou unidades/designações sem conversão auditada.

`UNKNOWN` e `NO_DISAGREEMENT` são **não-vetos**. Mera desigualdade textual, de números, PN, série, classe ou norma não autoriza `DISAGREEMENT`. Em pares com múltiplas medidas, uma divergência só é válida se a função física de **cada medida comparada** estiver estabelecida; conflitos entre dimensões de funções distintas são vedados.

## 3. Tabela de decisão para a futura sonda
| Situação | Resultado permitido | Razão |
|---|---|---|
| Mesmo atributo dimensional, unidades compatíveis, valores incompatíveis | DISAGREEMENT | Conflito físico bilateral demonstrado |
| Mesmo atributo, valores equivalentes com separador diferente | NO_DISAGREEMENT | Variação lexical não é física |
| Mesmo atributo, valores iguais | NO_DISAGREEMENT | Sem sinal de conflito |
| Só um material informa a dimensão | UNKNOWN | Evidência unilateral |
| Falta unidade/ambiguidade de notação sem regra auditada | UNKNOWN | Conversão não demonstrada |
| Números referem-se a papéis físicos diferentes | UNKNOWN | Comparação ilegítima |
| Apenas PNs, classes, normas ou séries diferem | UNKNOWN | Não inferir dimensão de código |
| Múltiplas leituras dimensionalmente plausíveis | UNKNOWN | Conservadorismo explícito |

## 4. Matriz de testes mínima antes da primeira execução
1. Valor igual com espaçamento e delimitadores diferentes — não veto.
2. Mesma propriedade e unidade com cotas incompatíveis — DISAGREEMENT somente com evidência tipada.
3. Dimensão ausente de um lado — UNKNOWN.
4. Duas unidades sem equivalência previamente auditada — UNKNOWN.
5. Dimensão truncada ou sintaxe insuficiente — UNKNOWN.
6. PN divergente, dimensão idêntica — não veto.
7. Números iguais, propriedades físicas distintas — UNKNOWN.
8. Notação DN versus polegadas — UNKNOWN sem regra de equivalência aprovada.
9. Múltiplas dimensões presentes — nenhum cruzamento por posição/número solto.
10. Reversão A/B — mesmo sinal, sempre que comparabilidade for bilateral e simétrica.
11. Rota 1 positiva — não pode ser invertida pelo veto proposto restrito à Rota 2.
12. Candidate Selection — pares retidos/descartados devem ser idênticos ao B0.

São **cenários de especificação**, não testes implementados ou aprovados. Os IDs 005/013/029/037 servem somente à auditoria das observações; não podem integrar a lógica da sonda. O caso 021 é TN original, não FP recuperável.

## 5. Protocolo de execução em etapa futura (não autorizado aqui)
**Gate 0:** registrar HEAD, versão do instrumental, SHA-256 do catálogo/GT/manifesto e ausência de alterações nos três inputs FROZEN. Se divergirem da custódia, STOP.

**Gate 1:** reproduzir B0 par-a-par em 40/40 pares, inclusive Candidate Selection e status de ambos os estágios; qualquer diferença = STOP.

**Gate 2:** executar unicamente B2 sobre a Rota 2 experimental com logs por par: tipo de sinal, evidências dos atributos bilaterais, decisão B0, decisão B2, rótulo consultado somente na avaliação. Nunca combinar B1+B2 ou modificar `src/agent_lab/`, `tests/`, dataset ou Ground Truth.

**Gate 3:** matriz B0→B2 por família e quadrante; contagens TP/FP/TN/FN incondicionais, condicionadas e end-to-end em tabelas separadas; publicar efeitos nulos e adversos.

**Gate de segurança primário:** `TP_B2=19` entre os 19 TP originais e `FN_B2=1` na medição incondicional, já que o blocking se mantém inalterado; **qualquer TP original perdido = SAFETY FAILED**, mesmo que a precisão ou o F1 cresçam. O teto exploratório de correção FM-1 é 4 FPs, não uma promessa de 4/4. Sem veto legítimo, melhoria pode ser zero e deve ser reportada.

**Gate epistêmico:** T02 contém 40 pares sintéticos conhecidos durante o desenho; nenhuma conclusão de significância estatística, generalização, prontidão industrial ou elegibilidade de produção decorre do ensaio post-hoc. Requer tranche independente antes de qualquer recomendação de promoção.

## 6. Deliberações humanas ainda necessárias
- Aprovar **ou rejeitar** expressamente: escopo focal; semântica triestável; precedência Rota 2; matriz de testes; stop conditions.
- Emitir, em ato separado, **HUMAN GO — IMPLEMENT AND EXECUTE ISOLATED B2/FM-1** se e somente se desejar avançar para código experimental e execução.
- Até então: B2 `NOT EXECUTED`; Issue #158 `OPEN`, `weight=0`, `progress=0`; A1/B3–B5/T03 intactos; 1194/1194 e 40/40 citados apenas como **baselines históricos**, não reexecutados nesta sessão.

**Este documento não atualiza o PROJECT_COMPASS**: a âncora canônica continua HUMAN GO REQUIRED FOR B2 EXECUTION.