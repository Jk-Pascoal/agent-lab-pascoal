# SR-001 / Issue #158 — revisão documental dominical da especificação B2/FM-1

**Data:** 2026-10-11  
**Escopo:** registro documental de revisão estática da proposta de 10/10; nenhuma execução experimental.  
**Documento revisado:** `docs/experiments/SR-001_b2_dimensional_probe_spec_DRAFT_20261010.md` (PR #185).

## 1. Evidências verificadas na especificação

- A intervenção proposta permanece **DRAFT / FOR HUMAN REVIEW**, sem HUMAN GO.
- O universo de referência T02 está declarado como 40 pares, com B0 incondicional TP=19, FP=17, TN=3 e FN=1.
- Os quatro falsos positivos FM-1/HN-DIM estão explicitados como hipóteses de investigação, **sem presumir** recuperação de 4/4; o caso 021 é TN original.
- O sinal conceitual distingue `DISAGREEMENT`, `NO_DISAGREEMENT` e `UNKNOWN`, e estabelece que `UNKNOWN` não gera veto.
- O veto candidato é restrito à Rota 2 do **detector experimental**, sem alterar Rota 1, Candidate Selection ou produto.
- O protocolo futuro exige reprodução do B0 par a par, preservação dos 19 TP e divulgação dos quatro quadrantes, além da separação entre avaliação incondicional, condicionada e end-to-end.
- O documento reconhece que o ensaio T02 é post-hoc e não validação independente.

## 2. Pontos que seguem pendentes

1. **Ponto de integração:** identificar o local exato no código experimental e a precedência do veto B2 na Rota 2, antes da implementação.
2. **Semântica verificável:** materializar tabela de decisão e testes para sinais bilaterais comparáveis, conflitantes, ausentes, ambíguos e unilaterais. Não converter `UNKNOWN` em conflito por ausência de informação.
3. **Robustez:** evitar dependência de identificadores de caso, rótulos de Ground Truth, exceções específicas da T02 e normalizações dimensionais sem gramática auditada.
4. **Fronteira de evidência:** quaisquer resultados futuros em T02 devem permanecer explicitamente *post-hoc*; exigir validação independente antes de recomendar generalização ou produção.

## 3. Decisão de custódia desta sessão

**REVISÃO DOCUMENTAL REGISTRADA — SEM APROVAÇÃO DE EXECUÇÃO.**

Não há neste registro execução de B2, rerun de testes, medição nova, validação de eficácia, autorização de merge nem aprovação humana da proposta. A especificação permanece DRAFT; Issue #158 permanece em escopo experimental. B1 continua registrado como SAFETY GOAL FAILED / NOT ELIGIBLE FOR PRODUCTION.

**Alteração realizada em 11/10:** somente este registro de revisão, para manter rastreabilidade diária sem alterar o experimento.
