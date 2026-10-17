# Agent Lab — Reentrada operacional de 17/10/2026

**Natureza:** checkpoint documental e somente-leitura, sem execução experimental.  
**Fonte canônica:** `docs/PROJECT_COMPASS.md` (âncora 14/10), PRs #191 e #192, PMP e CRONO do fechamento de 16/10.

## Estado verificado no GitHub

- `origin/main` em `fe983af1906ba48d618b6392a35a28a62390eebb` (merge PR #192, 16/10/2026).
- PR #192: MERGED, revisão metodológica de oito lacunas do pré-registro.
- PR #191: OPEN / DRAFT, protocolo de validação independente B2 ainda não promovido nem executado.
- Issue #158: investigação experimental em aberto, peso e contribuição ao KPI iguais a zero (conforme registro canônico anterior).
- Baseline histórico de produto: 1194/1194; instrumental experimental legado: 40/40. **Não reexecutados neste checkpoint**. Os testes específicos B2 não são somados à suíte canônica.
- Sincronia de checkout local, limpeza da working tree e testes locais: **NÃO VERIFICADOS** (acesso somente remoto).

## Distinções científicas preservadas

- T02 permanece FROZEN (40 pares, 20P/20HN). Nenhuma alteração em GT, manifestos, hashes ou observações originais.
- B0/T02: TP=19, FP=17, TN=3, FN=1, precision ≈52,78%, recall=95%.
- B2/T02 pós-hoc: TP=19, FP=13, TN=7, FN=1, precision=59,375%, recall=95%; redução de 4 FPs, sem TP perdido **na T02**, não prova fora da amostra.
- A correção da PR #189 mantém interpretação de passo de rosca e valores ambíguos como UNKNOWN, sem elegibilidade para produção.
- Nenhuma avaliação industrial em 100 mil SKUs comprovada; P-07 é frente distinta.

## Reentrada — próximo passo protegido

Antes de qualquer coleta ou validação independente, resolver e registrar no pré-registro #191 os oito gates apontados na revisão #192:
1. unidade de independência estatística / clusters de SKUs;
2. população-alvo, estratos e plano/tamanho de amostra;
3. prevenção de leakage e separação de papéis;
4. semântica de UNKNOWN e taxa de cobertura;
5. recall end-to-end e controle das perdas de blocking;
6. semântica física e comparação tipada de atributos;
7. análise estatística pareada, incerteza e critérios de falha;
8. separação da hipótese de escala P-07 (100 mil SKUs).

**Decisão desta sessão:** registrar a reentrada, não editar o pré-registro #191 por inferência e não autorizar amostragem, T03, execução B2 independente, A1/B3–B5, mudanças em `src/agent_lab/` ou `tests/`, promoção a produção ou alteração de KPI.

**Critério de saída:** reentrada documentada por branch → PR → CI → merge quando aprovado; a revisão metodológica do protocolo continua pendente de deliberação humana.
