# SR-001 — Matriz de decisões pendentes para validação independente B2 (18/10/2026)

**Status:** CHECKPOINT DOCUMENTAL / NO EXPERIMENT / NO HUMAN GO FOR VALIDATION.  
**Fontes:** `docs/PROJECT_COMPASS.md`; `docs/experiments/SR-001_pr191_methodology_review_20261016.md`; PR #191 (OPEN/DRAFT); PR #193 (MERGED).  
**Finalidade:** transformar oito lacunas metodológicas já identificadas em critérios auditáveis de decisão, sem editar ou promover o pré-registro.

| Gate | Decisão que falta | Evidência mínima antes de autorizar | Estado |
| --- | --- | --- | --- |
| G1 — Unidade | Par, SKU, família ou cluster; regra para dependências | Definição de unidade e agrupamento de SKUs compartilhados | PENDENTE |
| G2 — Amostra | População-alvo, estratos, seleção e n justificado | Plano amostral prévio e denominadores por estrato | PENDENTE |
| G3 — Leakage | Separação de design/debug T02/B1/B2 da confirmação | Critério de exclusão, papéis independentes e hashes pré-revelação | PENDENTE |
| G4 — UNKNOWN | Propagação de indeterminação e cobertura de tipagem | Tabela de tratamento de UNKNOWN e denominadores por estrato | PENDENTE |
| G5 — Segurança | Gate pareado de TP e recall absoluto end-to-end | Regra de falha, tratamento de FN do blocking e recall operacional | PENDENTE |
| G6 — Física | Tipos, unidades, posição semântica e tolerâncias | Convenções por categoria (ex.: M10X1.25X40: diâmetro/passo/comprimento) | PENDENTE |
| G7 — Estatística | Discordância B0/B2, incerteza, clusters, potência | Plano analítico pré-especificado, incluindo limites de prevalência | PENDENTE |
| G8 — Escala | Isolar P-07 da validade semântica | Plano próprio futuro de integridade/migração/latência para 100 mil SKUs | PENDENTE |

## Ordem de resolução proposta — não aprovada

1. Resolver G6 e G4 primeiro: sem contrato físico tipado nem política explícita de UNKNOWN, não é possível definir desfechos semânticos auditáveis.
2. Resolver G1, G2 e G3 antes de qualquer amostragem: dependência entre pares, desenho amostral e leakage condicionam a validade.
3. Congelar G5 e G7 antes de revelar rótulos: critérios de falha e análise não devem nascer dos resultados.
4. Tratar G8 em protocolo separado; não declarar escalabilidade a partir da T02.

## Fatos históricos preservados

- T02 FROZEN: 40 pares (20P/20HN). B0: TP=19, FP=17, TN=3, FN=1.
- B2 pós-hoc na mesma T02: TP=19, FP=13, TN=7, FN=1; **4 FP a menos e zero TP sacrificado apenas nesta amostra**.
- Produto: baseline histórico 1194/1194 GREEN; instrumental legado: 40/40 GREEN. **Não reexecutados hoje.**
- Issue #158 OPEN / experimental / weight=0 / progress contribution=0; PR #191 deve permanecer OPEN/DRAFT.
- T02, Ground Truth, manifestos, hashes, evidências observed-as-run, `src/agent_lab/`, `tests/` e KPI não alterados.
- Não há evidência de validação independente, prontidão industrial ou desempenho em 100 mil SKUs.

## Stop/go e próxima âncora

**STOP:** nenhuma coleta, T03, B2 independente, A1/B3–B5, tuning, alteração de produção ou aprovação da PR #191 por inferência.  
**NEXT:** deliberação humana explícita sobre contratos de atributos físicos tipados e UNKNOWN (G6/G4), seguida do planejamento pré-registrado dos demais gates. Esta matriz não equivale a decisão humana nem substitui o pré-registro.  
**Escopo operacional de 18/10:** documentação e revisão GitHub; checkout local, working tree e execução local de testes não verificados.
