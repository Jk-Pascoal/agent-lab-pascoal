# PoC — pacote de decisão D-01/D-02 e primeira fatia verificável (22/10/2026)

**Status:** PROPOSED / DECISION SUPPORT / NO HUMAN ACCEPTANCE / NO FUNCTIONAL CHANGE.  
**Base factual:** SPEC-POC-REPORT-001 (PR #197), revisão adversarial F1–F5 e matriz R1–R10 (PR #198).  
**Limites:** este registro não autoriza implementação, não fecha gates e não constitui demonstração E2E. O marco original de reporting em 25/10 e o da PoC em 20/11 continuam históricos, não previsões revalidadas.

## 1. D-01 — escopo mínimo sujeito a aceite humano

**Opção recomendada para deliberação, não aprovada:** demonstrar um relatório determinístico e rastreável sobre **catálogo CSV sintético controlado**, usando capacidades existentes de diagnóstico e uma projeção de relatório nova somente após HUMAN GO.

- **Incluído na primeira fatia:** identidade canônica de catálogo/material; contagens e razões estruturais existentes; lista de problemas e pares **candidatos**; limitações explícitas; payload versionado e manifesto separado; status de revisão humana explícito como `NOT_RECORDED` quando não existir evento vinculável.
- **Não incluído nesta primeira fatia:** alegação de precisão/recall sem Ground Truth independente; adjudicação de duplicidade verdadeira; integração de LLM externa; execução automática de revisão humana; demonstração de throughput industrial; escala de 100 mil SKUs; promoção de B2/SR-001 ao produto.
- **HITL:** preservar autoridade humana como invariante; a ausência de revisão registrada não pode ser transformada em aprovação automática. Uma demo de **decisão humana efetiva** será uma fatia separada, exigindo vínculo verificável de evento, identidade e contexto.
- **Ground Truth:** opcional apenas para a demonstração *estrutural do relatório*. Qualquer afirmação de qualidade semântica/performance depende de amostra e GT independentes e deve ter outro gate.

**Pergunta D-01 para decisão explícita:** aceitar/rejeitar este MVP CSV sintético e separar formalmente a demo de relatório estrutural da demo HITL-E2E? Até aceite, `D-01=PENDING`.

## 2. D-02 — contrato conservador de proveniência sujeito a aceite

| Campo/problema | Proposta para primeira fatia | Evidência necessária |
| --- | --- | --- |
| `source_row` | `null`, `source_row_status=UNAVAILABLE` até haver mapa de linhas físicas | Para VERIFIED, provar linha física inicial de registro inclusive CSV multilinha, blanks e reordenação |
| `source_sha256` | Capturar somente bytes da fonte congelada; se parser e hash não usam o mesmo snapshot, `null` e `UNAVAILABLE` | Prova de mesma sequência de bytes no hashing e parse, contra TOCTOU |
| `source_ref` | Identificador controlado e não sensível do fixture; não inventar URI estável | Evidência do vínculo com snapshot capturado |
| `report_sha256` | SHA-256 de payload JSON canônico fechado; manifesto externo referenciando digest | Duas exportações lógicas iguais produzem bytes iguais; mutação é detectada |
| `human_review` | `NOT_RECORDED` sem evento correspondente; nunca derivar de `GovernanceAssessment.decision` | Para RECORDED, vínculo auditado catalog/material/workflow/review/tempo |
| candidatos de duplicidade | Rotular apenas como candidatos de triagem | Não converter candidate_pairs em TP/precision ou duplicidade confirmada |

**Pergunta D-02 para decisão explícita:** aprovar a degradação fail-closed (`UNAVAILABLE`/`NOT_RECORDED`) e o manifesto desacoplado para a primeira entrega, reservando `VERIFIED` e `RECORDED` à prova de custódia/vinculação? Até aceite, `D-02=PENDING`.

## 3. Sequência de execução condicionada ao aceite

1. Registrar decisões humanas D-01 e D-02 com escopo, exclusões, autoria e data; não interpretar este documento como assinatura.
2. Fixar um fixture CSV sintético que inclua entrada vazia, ids fora de ordem, registro multilinha e candidato de duplicidade. Conservar os bytes e o hash com cadeia de custódia.
3. Implementar projeção pura `CatalogQualityReport -> poc_audit_report.v0` com limites explícitos; sem fabricar linha física ou evento HITL.
4. Implementar payload determinístico e manifesto separado, com rejeição de versão e inconsistências.
5. Adicionar testes adversariais e evidências para **cada** R1–R10, registrando `PASS/FAIL/NOT_APPLICABLE` por gate; não marcar todos como concluídos por existência da SPEC.
6. Fazer ensaio real a partir do fixture, inspecionar outputs e replay; abrir demo HITL vinculada como etapa própria, se aprovada.

## 4. Critérios de interrupção

- Se o exportador não puder preservar identidade, ordenação, nulidade e proveniência sem inventar dados, **falhar fechado**.
- Se a seleção entre recomendação e decisão humana ficar ambígua, não produzir `RECORDED`.
- Se qualquer gate R1–R10 não tiver teste e evidência, reportar **PENDING**; não usar aprovação documental como substituto.
- Não alterar `src/agent_lab`, `tests`, GT, T02 FROZEN, SR-001, pesos/KPI ou o cronograma nesta sessão.

## 5. Registro da sessão

**22/10/2026:** proposta de recorte decisório e sequência operacional, apenas documentação. `D-01/D-02=PENDING`; `R1–R10=PENDING` salvo comprovação futura individual; baseline canônico de 1194 e instrumental legado de 40 são referências históricas, não testes reexecutados hoje. PR #191 permanece pré-registro independente DRAFT segundo última verificação documental; Issue #158 permanece OPEN segundo a última linha de base documentada. Não declarar CI, merge ou estado do perfil sem verificação específica.

**Próxima âncora:** HUMAN DECISION D-01/D-02, antes de implementar exportador ou replanejar marcos.
