# SR-001 / B2-FM-1 — Errata de robustez pós-observação — 13/10/2026

**Status:** correção experimental restrita / sem promoção a produção.

## Achado independente
A revisão externa identificou que a regex de fixadores da PR #188 lê erroneamente `M10X1.25X40` como comprimento de **1 mm**, confundindo passo de rosca com comprimento. Em comparação a `M10X40`, isto pode gerar `DISAGREEMENT` indevido. Há risco de suprimir um verdadeiro positivo fora da T02.

## Correção conservadora
A sonda B2 retorna `UNKNOWN` para notações de rosca métrica com três componentes (`M10X1.25X40`, `M10X1,25X40`, com espaços e separadores), em vez de atribuir comprimento a um atributo não resolvido. `UNKNOWN` nunca veta a decisão original. Também removido padrão morto de válvula da tabela `_GRAMMAR` e alinhado comentário de código.

## Custódia
A observação original da PR #188 em `docs/experiments/SR-001_b2_t02_posthoc_observation_20261013.md` permanece **imutável**: não retroeditar o resultado histórico de 19 TP / 13 FP / 7 TN / 1 FN. A errata é vinculada explicitamente ao problema e não constitui nova validação independente.

A implementação histórica e a corrigida são versões distintas. Ao aplicar a correção, reexecutar hash gate T02, B0 40/40 e testes adversariais. Os valores T02 podem coincidir mesmo com a falha de generalização demonstrada.

## Escopo e limites
Somente `experiments/` e esta errata são afetados. Dados T02 FROZEN, Ground Truth, manifesto, `src/agent_lab/` e `tests/` não mudam. A1, B1, B3-B5 e T03 não são executados. `Issue #158` continua OPEN / experimental / weight=0. B2 segue NOT ELIGIBLE FOR PRODUCTION.
