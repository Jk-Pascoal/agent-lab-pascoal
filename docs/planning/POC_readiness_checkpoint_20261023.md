# Agent Lab — checkpoint de prontidão PoC (23/10/2026)

**Status:** READ-ONLY GOVERNANCE CHECKPOINT / NO HUMAN GO / NO FUNCTIONAL CHANGE.  
**Base:** `docs/PROJECT_COMPASS.md`, PR #199 (22/10), SPEC-POC-REPORT-001 (PR #197), auditoria de risco (PR #198), roadmap de 22/10.

## 1. Evidência factual da reentrada

- Última PR identificada na main ao iniciar esta sessão: #199, merge `ac96fbe1c7bf9e1b737f111a44dca9fbb668ee9a`.
- Baseline de produto **1194/1194** e instrumental **40/40** são históricos; **não reexecutados** neste checkpoint.
- D-01 (recorte mínimo da PoC) = **PENDING HUMAN ACCEPTANCE**.
- D-02 (proveniência fail-closed do relatório) = **PENDING HUMAN ACCEPTANCE**.
- R1–R10 = **UNVERIFIED/PENDING**, não convertidos em PASS por documento ou CI.
- PR #191 (pré-registro B2) permanece DRAFT pela linha de base documental; Issue #158 OPEN. B2 não elegível para produção, T02 FROZEN preservada.
- Marco de reporting **25/10/2026** é prazo histórico em risco, **não** evidência de entrega. PoC **20/11/2026** igualmente não revalidada.

## 2. Gate objetivo para desbloquear a primeira fatia

| Gate | Aceite exigido | Estado nesta sessão |
| --- | --- | --- |
| D-01 | Humano aceitar explicitamente PoC estrutural com CSV sintético, sem reivindicar demo HITL-E2E | PENDING |
| D-02 | Humano aceitar `UNAVAILABLE` para proveniência não comprovada, `NOT_RECORDED` para revisão sem evento e manifesto externo de digest | PENDING |
| Fixture | Congelar bytes do CSV sintético e identidades de entrada | NOT STARTED |
| Implementação | Projeção/exportação determinística e auditável em branch própria, após HUMAN GO | NOT STARTED |
| Verificação | Evidência de teste individual para cada R1–R10 e reprodução dos outputs | NOT STARTED |
| Marco 25/10 | Reclassificar por evidência: entregue / parcial / bloqueado; registrar novo prazo somente após decisão humana | AT RISK |

## 3. Ordem operacional de próxima execução

1. Obter decisão humana explícita D-01 e D-02 com inclusões, exclusões e data; se negada, revisar escopo em vez de codificar.
2. Abrir uma Issue funcional única com critérios verificáveis R1–R10; vincular à SPEC já PROPOSED.
3. Congelar fixture e cadeia de custódia; realizar micro-TDD para identidade, nulidade, ordenação e proveniência.
4. Implementar somente o relatório estrutural autorizado. Não inferir eventos HITL, Ground Truth, qualidade semântica ou escala.
5. Validar no CI, executar demo/replay quando autorizado e só então atualizar roadmap e cronograma conforme evidência.

## 4. Critérios de parada

Sem HUMAN GO D-01/D-02, **não implementar** `src/agent_lab`, não alterar testes, Ground Truth, T02, parâmetros B2, KPI ou baseline. Não deslocar os marcos unilateralmente. Não reivindicar contribuição GitHub de 23/10 até o commit/PR existirem de fato.

**Conclusão deste checkpoint:** o gargalo é de *decisão de produto/aceite*, não falta de documentação. Documentação adicional não substitui demonstração funcional. Este arquivo registra o limite e evita a falsa aparência de conclusão.
