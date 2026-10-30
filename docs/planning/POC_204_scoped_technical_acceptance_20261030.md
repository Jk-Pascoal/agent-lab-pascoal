# Issue #204 — revisão técnica e aceitação de escopo limitado (30/10/2026)

**Objeto:** PR #205, PoC v0 de relatório auditável CSV sintético.
**Escopo da análise:** código da PR, SPEC-POC-REPORT-001, decisão D-01/D-02 de 27/10, matriz R1–R10, testes específicos e demonstração física.
**Natureza:** revisão adversarial técnica feita no fluxo assistido; **não se faz passar por avaliação independente de terceiro**.
**Limite do aceite:** um fluxo estrutural/determinístico *sem* custódia original verificada, *sem* revisão humana e *sem* claims industriais. A PR não encerra a macrofrente de reporting/PoC vendável nem substitui aprovação de produção.

## 1. Decisões humanas e dependências

- D-01 — **APPROVED 27/10:** MVP CSV sintético estrutural; HITL-E2E fora do incremento.
- D-02 — **APPROVED 27/10:** `source_row/source_sha256` permanecem `UNAVAILABLE` quando não comprovados; `human_review=NOT_RECORDED`; manifesto separado com SHA-256 dos bytes de relatório.
- Instrução do proprietário em 30/10: concluir pendências técnicas e, **se houver gates cumpridos**, integrar os commits históricos corretamente para contabilização nas datas de autoria.
- D-03/D-04 — **PENDING / NÃO DECIDIDAS:** pesos/progresso e revisão de previsão do cronograma; não são assumidos nem replanejados por esta PR. Marco `report` de 25/10 continua vencido, 20/11 não revalidado.
- Revisão humana externa independente: **não obtida** nesta sessão. Este documento registra revisão técnica assistida, sem falsificar aprovação de terceiro.

## 2. Matriz factual de gates para o MVP restrito

| Gate | Resultado no recorte aprovado | Evidência e limites |
|---|---|---|
| R1 schema/versionamento | PASS — SCOPED | JSON canônico v0 + rejeição de versão e chaves desconhecidas |
| R2 identidade | PASS — SCOPED | material_id único/ordenado; candidatos simétricos, pares válidos |
| R3 métricas | PASS — SCOPED | summary recomputado e validado, `null` para razões indefinidas |
| R4 proveniência | PASS **somente para fallback fail-closed** | `UNAVAILABLE` e `null` obrigatórios; testes rejeitam linha, hash/CSV/execução fabricados mesmo com hash de relatório recalculado. **Custódia física de CSV permanece NÃO DEMONSTRADA.** |
| R5 replay | PASS — SCOPED | 2 relatórios e manifestos byte a byte iguais |
| R6 recomendação ≠ decisão | PASS — SCOPED | `human_review.NOT_RECORDED`; falso `RECORDED` rejeitado |
| R7 falha segura | PASS **somente para consumo validado** | CSV inválido falha; manifesto ausente/adulterado rejeitado; `SIGKILL` antes/entre/depois dos links; novo destino permite recuperação, arquivo órfão não é consumido como íntegro. **Não demonstra atomicidade de par em queda de energia, durability de diretório ou reparo de arquivos órfãos.** |
| R8 segregação | PASS — SCOPED | diff da PR restrito à PoC: `.github/workflows/poc-204-demo.yml`, `scripts/poc_204_demo.py`, `src/agent_lab/poc_audit_*`, `tests/test_poc_audit_*`, fixture sintética e este relatório |
| R9 HITL-E2E | OUT OF SCOPE — D-01 | nunca marcar como PASS |
| R10 CI | PASS condicionado à última execução no HEAD | suíte `unittest` e workflow físico devem estar GREEN antes da integração |

## 3. Observações da revisão adversarial

1. A publicação usa `os.link`, não sobrescreve destinos e faz `fsync` de cada stage, mas não pode prometer transação de dois nomes; o verificador com manifesto é obrigatório para todo consumo. Não interpretar mera presença de arquivos como garantia física.
2. Verificador lê snapshots dos arquivos em memória, valida JSON canônico, schema v0, digest e estados fail-closed. Hash de manifesto **não é assinatura contra um adversário capaz de reescrever relatório e manifesto**.
3. `source_sha256` capturado pelo runner externo da fixture é evidência restrita dos bytes presentes no checkout, **não** prova que o adaptador leu um snapshot imutável/custodiado. O relatório continua `UNAVAILABLE`.
4. `triage.csv` é projeção auxiliar somente-leitura; rótulos `REVIEW` e `APPROVE` são exclusivamente recomendações de algoritmo.
5. Escopo e dados apenas sintéticos; não projetar acurácia, recall, capacidade 100k SKUs, substituição de especialista ou prontidão para produção.

## 4. Condições operacionais do merge

- [ ] CI geral GREEN na versão final da PR.
- [ ] CI específico PoC + replay físico GREEN na versão final da PR.
- [ ] Diff sem alteração de T02 FROZEN, GT, SR-001/B2 ou `docs/PROJECT_COMPASS.md` além do fluxo de pós-merge normal.
- [ ] Confirmar o aceite condicional do proprietário no pedido da sessão de 30/10.
- [ ] Se os requisitos de proteção do GitHub exigirem revisão independente, respeitar o bloqueio; **nunca** simular reviewer/APPROVED.
- [ ] Integrar usando **merge normal**, não squash/rebase, para preservar identidade e datas originais dos oito commits de 28/29. Não falsificar timestamps.
- [ ] Verificar CI após integração e conferir calendário; visibilidade do quadradinho é dependente de atualização do perfil, não garantia instantânea.

## 5. Não-confusões

`Merge MVP estrutural` ≠ `macro reporting concluída` ≠ `R4 custódia verificada` ≠ `R7 atomicidade power-loss` ≠ `HITL E2E` ≠ `PoC vendável`.

**Nota:** esta revisão não contém dados privados ou eventuais decisões de negócio. A atualização final das evidências de CI/merge fica nos comentários da PR e na Issue #204, sem reescrever o diagnóstico histórico deste relatório.
