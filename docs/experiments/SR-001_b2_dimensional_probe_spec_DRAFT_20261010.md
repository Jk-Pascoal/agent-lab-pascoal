# SR-001 / Issue #158 — B2 Dimensional Disagreement: especificação preliminar

**Data:** 2026-10-10  
**Estado:** DRAFT / FOR HUMAN REVIEW — documento de concepção, não autorização para executar.  
**Âmbito:** experimento isolado e reversível sobre a Tranche 02 FROZEN; sem alteração de produto.

## 1. Problema e motivação

A observação T02 (B0) apresentou TP=19, FP=17, TN=3, FN=1 em 40 pares. Quatro FPs (4/17, 23,53%) são da família FM-1/HN-DIM: CASE-005 (M12×60 vs M12×70), CASE-013 (3 POL vs 4 POL), CASE-029 (seção 16 mm² vs 25 mm²) e CASE-037 (correia B60 vs B62). CASE-021 (rolamento 6305 vs 6306) já era TN: não contá-lo como falha B0.

**Questão:** seria possível vetar duplicidade em pares com discordância dimensional física *bilateral, tipada e comparável*, preservando os verdadeiros positivos?

## 2. Deliberação de escopo proposta (NÃO APROVADA)

Propor **sonda focal, explicitamente circunscrita à T02**, em vez de parser dimensional generalista. Justificativa: a evidência disponível limita-se a 40 pares e contém notações ambíguas. Uma futura evolução a extrator tipado exigirá corpus, gramática e validação independentes.

Esta escolha é uma **proposta de projeto**, não decisão humana consumada. Nenhuma regra pode usar IDs de casos, rótulos de Ground Truth ou listas de exceções hardcoded para determinar o resultado; esses identificadores servem apenas para avaliação.

## 3. Contrato candidato do sinal B2

Entradas: dois registros de material e seus atributos textuais; uso somente dos campos disponíveis no catálogo congelado, sem consultar Ground Truth.

Saída conceitual triestável:
- **DISAGREEMENT:** ambos os lados contêm *atributo identificado com a mesma função física*, unidade ou designação interpretável e valores incompatíveis comprováveis;
- **NO_DISAGREEMENT:** atributos bilateralmente comparáveis e sem conflito comprovado;
- **UNKNOWN:** ausente, truncado, ambíguo, unidades não normalizadas, classe de atributo incerta ou informação unilateral. UNKNOWN jamais produz veto.

Ponto de aplicação candidato: **apenas Rota 2 do detector experimental**, preservando Rota 1, Candidate Selection e o pipeline de produto. A especificação final deverá identificar o ponto exato no código antes da implementação.

Regras de segurança:
1. Comparar somente atributos da mesma função (ex.: comprimento do componente ≠ distância sensora ou comprimento de cabo).
2. Não confundir números em norma, série, classe, pressão, tensão, PN de fabricante ou código de produto com grandezas físicas extraídas.
3. Não tratar designações nominais como conversões triviais: DN 100, DN100 e 4 POL requerem regra explícita e auditada.
4. Preservar equivalência perante separadores alternativos (M12X45 / M12-45) e unidades omitidas em uma das descrições (3/4 POL X 150 MM / 3/4 X 150 MM), sempre que o contexto não permitir uma conclusão segura.
5. Quando houver mais de uma leitura plausível, emitir UNKNOWN; não forçar veto.

## 4. Matriz inicial de comportamento esperado (hipóteses, não resultados)

| Casos T02 | Risco / hipótese | Comportamento a examinar |
| --- | --- | --- |
| 005 / 013 / 029 / 037 | Quatro FPs FM-1 | Investigar elegibilidade de veto bilateral tipado; **não** presumir 4/4 |
| 021 | TN original | Manter TN; não contabilizar como FP corrigido |
| 001 / 002 | Delimitador e unidade omitida | Não sacrificar TP por conflito textual aparente |
| 011 | DN versus polegadas | Evitar veto sem modelo de designação nominal |
| 017 | Informação unilateral | UNKNOWN / sem veto |
| 027 | Dimensões de papéis distintos | Não comparar atributos heterogêneos |
| 020 / 028 / 036 | Truncamento | UNKNOWN quando faltar contexto dimensional |

A classificação específica de cada caso exige rastrear os registros brutos no momento da execução autorizada; esta matriz não atribui resultados contrafactuais.

## 5. Protocolo futuro sujeito a HUMAN GO

1. Congelar e registrar HEAD, hashes dos três artefatos T02, ambiente, comando e commit do probe.
2. Reproduzir B0 **par a par** nos 40 pares antes de B2; interromper se qualquer diferença.
3. Executar B2 isoladamente, mantendo todos os outros sinais e limiares constantes; nenhuma combinação com B1, A1 ou B3–B5.
4. Publicar matriz de transição por caso e quatro quadrantes, com métricas **incondicionais**, **condicionadas à seleção** e **end-to-end** separadas.
5. Gate primário: zero TPs de B0 sacrificados; com Candidate Selection invariável, TP B2 deve permanecer 19 e recall positivo incondicional 95%.
6. Resultado secundário: quantidade de FPs FM-1 suprimidos (meta exploratória até 4), além dos efeitos em todos os outros pares e famílias.
7. Classificar segurança, limitações e elegibilidade; resultado sobre T02 é *post-hoc*, não validação independente e não promove automaticamente a produção.

## 6. Fronteiras e decisão pendente

**Neste commit:** somente este DRAFT; sem alterações em `src/`, `tests/`, datasets, Ground Truth, manifesto, catálogo, instrumentação, métricas funcionais ou `PROJECT_COMPASS.md`.

**Pendente de deliberação humana:** aprovar/rejeitar a sonda focal, a semântica triestável, o ponto preciso de integração e a matriz de testes; posteriormente emitir HUMAN GO separado antes de qualquer código ou execução.

Referência de custódia: `docs/experiments/SR-001_b2_readiness_audit_20261009.md` (PR #184). B1 permanece VALID EXPERIMENT / SAFETY GOAL FAILED / NOT ELIGIBLE FOR PRODUCTION. Issue #158 continua OPEN, experimental/non-functional, weight=0/progress=0.
