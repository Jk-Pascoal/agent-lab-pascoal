# Agent Lab — protocolo de apuração do marco de reporting de 25/10 (preflight de 24/10/2026)

**Status:** GOVERNANCE / EVIDENCE-ONLY / NO HUMAN GO / NO FUNCTIONAL CHANGE.  
**Objetivo:** impedir que o prazo de 25/10 seja encerrado por mera produção de documentos, ou silenciosamente adiado, sem evidência de execução.  
**Base auditada em 24/10:** `main=e559ff6ecf70f771b948dfcdec3cbc142e8447d2` (PR #200 MERGED em 23/10); `docs/PROJECT_COMPASS.md`; `docs/specs/poc_audit_report_contract_v0_proposed_20261020.md`; `docs/planning/POC_D01_D02_decision_package_20261022.md`; `docs/planning/POC_readiness_checkpoint_20261023.md`.  
**Fonte temporal:** 24/10 é **pré-marco**; 25/10 é prazo histórico de `report`. Não classificar o marco como vencido antes do encerramento do período aplicável; não presumir entrega.

## 1. Quadro de evidência verificável — corte 24/10

| Controle | Evidência existente | Estado de aceite |
| --- | --- | --- |
| Escopo D-01 — CSV sintético estrutural; HITL-E2E separado | Pacote decisório PROPOSED de 22/10; falta manifestação humana inequívoca | **PENDING HUMAN ACCEPTANCE** |
| Proveniência D-02 — `UNAVAILABLE` / `NOT_RECORDED` / digest em manifesto externo | Proposta fail-closed de 22/10; falta manifestação humana inequívoca | **PENDING HUMAN ACCEPTANCE** |
| Contrato de exportação `poc_audit_report.v0` | SPEC documental de 20/10 e revisão adversarial de 21/10 | **PROPOSED**, não implementado |
| Fixture CSV PoC com bytes congelados, hashes e custódia | Sem artefato aprovado identificado no checkpoint de 23/10 | **NOT STARTED / NOT EVIDENCED** |
| Relatório físico, manifesto SHA-256, replay independente | Nenhum artefato de execução referenciado no checkpoint de 23/10 | **NOT EVIDENCED** |
| R1–R10 da SPEC | Critérios propostos; nenhum gate comprovado por evidência específica desta implementação | **PENDING / UNVERIFIED** |
| Suite produto 1194/1194 e instrumental 40/40 | Baselines históricos; não reexecutados neste preflight | **HISTORICAL ONLY** |
| PoC vendável HITL-E2E e 100 mil SKUs | Sem demonstração validada | **NOT DEMONSTRATED** |

*Nota de rigor:* ausência de evidência consultada não é prova absoluta de inexistência do artefato. Nenhum estado deve evoluir para PASS sem evidência primária de execução, vínculo de commit e aceite.

## 2. Regra de classificação do marco `report` em 25/10

Na sessão de apuração de 25/10, registrar a **data da observação** e aplicar exatamente uma classificação **sem modificar a baseline histórica**:

- **ENTREGUE:** exportador aprovado, integrado e executado sobre fixture congelada; payload e manifesto reproduzíveis; gates R1–R10 individualmente verificados conforme escopo aprovado; assinatura/aceite humano compatível. **Não** inferir HITL-E2E de um relatório estrutural.
- **PARCIAL:** parte material e demonstrável da entrega existe com artefatos, mas falta(m) gate(s) ou aceite. Discriminar precisamente provas existentes versus pendentes e **não** apresentar a macrofrente como DONE.
- **BLOQUEADO / NÃO DEMONSTRADO:** D-01 ou D-02 não aceitos, ou inexistência de evidência de artefato de reporting executado. Registrar explicitamente dependência humana e dívida de entrega; não substituir por PR documental, suite antiga ou SPEC.
- **INDETERMINADO:** evidências acessíveis incompletas ou contraditórias; conservar status conservador e documentar lacuna de investigação, sem forçar “ENTREGUE”.

**Resultado esperado se a situação de 24/10 persistir até a apuração:** **BLOQUEADO / NÃO DEMONSTRADO**, por ausência de aceite D-01/D-02 e de prova de implementação/exportação; isso é uma condição futura, **não** fechamento antecipado de 25/10.

## 3. Pacote mínimo para uma apuração auditável

1. **Decisão humana:** registrar D-01 e D-02 com autor, data, texto expresso de aceitar/rejeitar e escopo IN/OUT. Não deduzir aceitação de pedidos genéricos de “atividade do dia”.
2. **Rastreabilidade:** registrar Issue funcional, PR, merge SHA, versão de código/fixture e hashes de bytes de origem e do output; preservar distinção de input hash versus report hash.
3. **Teste:** capturar execução da suite oficial `python -m unittest discover -s tests -v`, novos testes e matriz R1–R10 com `PASS/FAIL/PENDING/NOT_APPLICABLE` por gate; anexar logs e outputs. Nenhum PASS pode decorrer de CI apenas documental.
4. **Demonstração:** registrar replay reprodutível CSV sintético → diagnóstico → relatório; o gate R9 de HITL-E2E só poderá ser comprovado quando existir vínculo auditável de decisão humana real.
5. **Cronograma:** conservar `end=2026-10-25` como data planejada original; se houver replanejamento aprovado, registrar previsão revisada em **campo distinto**, com decisão, dependências e atraso visíveis. Não alterar silenciosamente `progress`, `status`, `weight` ou KPI.

## 4. Decisão que desbloqueia a próxima fatia

- **D-01:** aceitar explicitamente a primeira fatia de relatório estrutural sobre **CSV sintético**, com separação da futura demonstração HITL-E2E, e exclusão de alegações de escala/qualidade semântica.
- **D-02:** aceitar explicitamente proveniência **fail-closed**: `source_row=null/UNAVAILABLE` sem mapa físico confiável; `source_sha256=null/UNAVAILABLE` sem custódia do mesmo snapshot; `human_review=NOT_RECORDED` sem evento; manifesto separado de hash do payload canônico.
- **Se aceitas:** só então abrir Issue funcional, congelar fixture, micro-TDD, implementar, executar e medir R1–R10. **Se não aceitas:** reformular a SPEC antes de implementar.
- **Decisões D-03/D-04:** tratar evolução de percentuais e previsão de prazos em ato separado e autorizado, preservando desvios históricos.

## 5. Exclusões, invariantes e critério de parada

Este protocolo **não** altera `docs/PROJECT_COMPASS.md`: a próxima âncora permanece decisão humana D-01/D-02; não há mudança arquitetural ou de baseline que justifique atualização cosmética. Nenhuma alteração em `src/agent_lab/`, `tests/`, Ground Truth, T02 FROZEN, parâmetros B2, PR #191 DRAFT, Issue #158 OPEN, peso/KPI ou cronograma. SR-001 não foi promovida a produto; 100 mil SKUs não estão validados.

**Fechamento de 24/10:** preparo de regra verificável para o marco de 25/10, exclusivamente documental. Este arquivo **não é relatório executivo de produto**, execução de exportador, cumprimento de R1–R10, aceite humano nem demonstração E2E.
