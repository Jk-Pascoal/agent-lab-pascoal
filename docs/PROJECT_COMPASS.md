# PROJECT COMPASS — Agent Lab Pascoal

> Ponto oficial de reentrada cognitiva e operacional do projeto.
>
> Leia este documento antes de propor uma nova Issue, SPEC ou alteração de código.

## 1. Identidade do projeto

- **Projeto:** Agent Lab Pascoal
- **Repositório:** `Jk-Pascoal/agent-lab-pascoal`
- **Domínio:** governança de materiais PDM/BOM e Master Data
- **Linguagem:** Python 3.11
- **Runner oficial de testes:** `unittest`
- **Branch protegida:** `main`
- **Estado registrado em:** 2026-08-28
- **Baseline integrado na main:** 412 testes aprovados
- **Baseline atual na branch da Issue #74:** 423 testes aprovados
- **Última entrega funcional integrada na main:** Material Revision Lineage Projection v1
- **Última Issue funcional integrada na main:** #71
- **Último PR funcional integrado na main:** #72
- **Último merge funcional:** `eea57ee` — Merge pull request #72
- **Última SPEC integrada na main:** `docs/specs/0071_material_revision_lineage_projection_v1.md`
- **Incremento funcional atual:** Issue #74 — Human Review Application Use Case v1 — implementação concluída na branch, aguardando PR/merge
- **SPEC atual da branch:** `docs/specs/0074_human_review_application_use_case_v1.md`
- **Baseline da branch:** 423 testes GREEN
- **Release formal atual:** `v0.1.0` — Governed Agent Workflow Baseline
- **Status da release:** publicada / Latest
- **Tag:** `v0.1.0`
- **Commit âncora da release:** `c5a9e462d535f90212c59c6f3f7b1354450170de`
- **PR de preparação da release:** #50 — docs: preparar release v0.1.0

> **Distinção de governança:** Merge fecha um incremento; release fecha uma versão coerente.

## 2. Propósito

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais. Seu objetivo é apoiar a análise de cadastros PDM/BOM por meio de uma arquitetura híbrida que combina:

- regras determinísticas;
- normalização e validação de dados;
- detecção de duplicidades;
- saídas estruturadas de LLM;
- evidências auditáveis;
- recomendações de decisão;
- revisão humana obrigatória;
- ciclo de vida temporal de governança com persistência append-only de abertura e conclusão, projeção determinística após restart para PENDING_HUMAN_REVIEW ou REVIEWED, e suporte a novos ciclos sucessores de correção (`open_correction_follow_up`) com vínculo causal explícito e predecessor preservado como histórico imutável;
- trilha de auditoria append-only desacoplada;
- verificação determinística e somente-leitura de consistência cruzada entre as trilhas de lifecycle e auditoria (`verify_dual_write_consistency` e `verify_repositories_consistency`).

O sistema não substitui o especialista de governança. Ele organiza evidências, detecta riscos, gerencia o ciclo temporal de revisão e produz recomendações para apoiar uma decisão humana rastreável.

## 3. Tese arquitetural

O projeto segue uma rigorosa separação de responsabilidades em duas trilhas persistentes complementares e desacopladas:

```text
DecisionRecommendation
        ↓
GovernanceWorkflow
        ↓
WorkflowOpened
        ↓
Workflow lifecycle JSONL
        ↓
rehydrate_workflow
        ↓
PENDING_HUMAN_REVIEW

e, após decisão humana:

HumanReview
   ├── WorkflowConcluded
   │       ↓
   │   Workflow lifecycle JSONL
   │       ↓
   │   rehydrate_workflow
   │       ↓
   │    REVIEWED
   │
   └── AuditEvent
           ↓
       Audit JSONL
```

Separação conceitual mandatória:
- **`WorkflowLifecycleEvent ≠ AuditEvent`**
- **`Repository ≠ Projection`**
- **`DecisionRecommendation ≠ HumanReview`**
- **Workflow lifecycle persistence (`WorkflowOpened`, `WorkflowConcluded`):** preserva os fatos do ciclo temporal de governança operacional e viabiliza a reidratação determinística de workflows nos estados `PENDING_HUMAN_REVIEW` e `REVIEWED` após reinicialização do processo;
- **Audit persistence (`AuditEvent`):** preserva a evidência imutável da deliberação do especialista humano pós-decisão;
- Não fundir as duas responsabilidades em uma mesma entidade ou repositório.

Princípio central:

```text
A IA recomenda; o humano decide; a auditoria preserva o percurso; o lifecycle preserva o estado operacional.
```

## 4. Estado arquitetural atual

### 4.1 Baseline versionado atual (v0.1.0)

A versão `v0.1.0 — Governed Agent Workflow Baseline` é a primeira release formal e versionada do laboratório. Ela consolida uma linha de base fundacional composta por:

- baseline determinístico e validação cadastral de materiais;
- fronteira LLM estruturada, tipada e com guardrail de identidade (`MaterialIdentityMismatchError`);
- Evidence Engine multiorigem (`RULE`, `VALIDATION`, `DUPLICATE`, `LLM`);
- recommendation pipeline determinístico com compulsoriedade de `requires_human_decision = True`;
- deliberação humana estruturada via `HumanReview` com `VerifiedSpecialistIdentity`;
- persistência auditável durável append-only (`AuditEvent` com `schema_version = 1` e `JsonlAuditRepository`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow` com `opened_at`, `closed_at`, `review_lead_time`);
- evento de domínio imutável `WorkflowOpened`;
- persistência de lifecycle de abertura append-only (`JsonlWorkflowLifecycleRepository` com `schema_version = 1`);
- projeção pura de reidratação de workflows pendentes (`rehydrate_pending_workflow`) sem reexecução de regras ou chamadas a LLM.

### 4.2 Núcleo normativo implementado

O sistema já representa e valida:

- materiais e atributos relevantes;
- normalização de descrições;
- validações cadastrais;
- possíveis duplicidades;
- issues estruturadas;
- severidade de problemas;
- evidências de regras e LLM;
- recomendações `APPROVE`, `REVIEW` e `REJECT`;
- confiança da recomendação;
- revisão humana;
- aprovação, reprovação e solicitação de correção;
- concordância e divergência humano–sistema;
- `VerifiedSpecialistIdentity`;
- proveniência da identidade humana;
- correlação entre `specialist_id`, `HumanReview` e `AuditEvent`;
- `WorkflowStatus.PENDING_HUMAN_REVIEW` e `WorkflowStatus.REVIEWED`;
- `GovernanceWorkflow` imutável e temporal em memória;
- transição pura canônica via `conclude_governance_workflow`;
- `opened_at` explícito e timezone-aware;
- propriedades derivadas `material_id`, `status`, `closed_at` e `review_lead_time`;
- validação temporal cronológica `opened_at <= reviewed_at`;
- validação de coerência de material e do parecer (`review.system_recommendation == recommendation.decision`);
- bloqueio estrito de dupla conclusão;
- integração ponta a ponta entre `GovernanceWorkflow`, `HumanReview`, `AuditEvent` e `JsonlAuditRepository`;
- eventos de auditoria imutáveis com `schema_version = 1` isolado;
- persistência local append-only de auditoria com `JsonlAuditRepository`;
- evento de domínio imutável `WorkflowOpened` com `event_id`, `workflow_id`, `recommendation` e `opened_at`;
- serialização versionada de lifecycle (`schema_version = 1`) com preservação integral de `DecisionRecommendation` e `GovernanceEvidence`;
- repositório `JsonlWorkflowLifecycleRepository` append-only com escrita durável (`flush` + `os.fsync`);
- leitura *fail-closed* com identificação precisa de `line_number` em caso de corrupção;
- bloqueio de `event_id` duplicado (`DuplicateWorkflowEventError`) e bloqueio de segunda abertura para o mesmo `workflow_id` (`WorkflowAlreadyOpenedError`);
- projeção pura `rehydrate_pending_workflow` reconstituindo fielmente `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` sem reexecução de regras ou LLM;
- conclusão de workflow reidratado via `conclude_governance_workflow` com validação de ciclo completo;
- **Incremento integrado da Issue #52 (Workflow Conclusion Persistence v1):**
  - evento de domínio imutável `WorkflowConcluded` com `event_id`, `workflow_id` e `review: HumanReview`;
  - type alias `WorkflowLifecycleEvent = WorkflowOpened | WorkflowConcluded`;
  - serialização versionada de lifecycle (`schema_version = 1`) com discriminador explícito `event_type = "WORKFLOW_CONCLUDED"` e round-trip integral de `HumanReview`;
  - dispatcher de ciclo de vida fail-closed (`workflow_event_to_record` / `workflow_event_from_record`) com preservação estrita da compatibilidade de `WorkflowOpened` legado (ausência da chave `event_type`);
  - repositório `JsonlWorkflowLifecycleRepository` misto suportando `append_concluded`, `get_events_by_workflow_id` e `list_all_events`;
  - bloqueio de conclusão sem abertura prévia (`WorkflowNotOpenedError`), bloqueio de segunda conclusão (`WorkflowAlreadyConcludedError`) e unicidade global de `event_id` (`DuplicateWorkflowEventError`);
  - validação estrita de consistência de material (`concluded.review.material_id == opened.recommendation.material_id`), parecer (`concluded.review.system_recommendation == opened.recommendation.decision`) e temporalidade (`opened.opened_at <= concluded.review.reviewed_at`);
  - projeção pura `rehydrate_workflow` reconstruindo deterministicamente `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` (se contiver apenas `WorkflowOpened`) ou `REVIEWED` (se contiver `WorkflowOpened` seguido de `WorkflowConcluded`), mantendo `closed_at` e `review_lead_time` derivados pelas regras de domínio;
  - teste de integração ponta a ponta validando persistência e reconstrução de workflow revisado através de dois restarts de processo;
- **Incremento integrado da Issue #55 (Dual-Write Consistency Check v1):**
  - módulo `src/agent_lab/consistency.py`;
  - enum canônico `ConsistencyIssueType` com 8 categorias discriminadas de inconsistência (`MISSING_AUDIT_EVENT`, `MISSING_WORKFLOW_CONCLUDED`, `MATERIAL_ID_MISMATCH`, `ACTOR_ID_MISMATCH`, `TIMESTAMP_MISMATCH`, `AUDIT_METADATA_MISMATCH`, `DUPLICATE_REVIEW_ID_IN_LIFECYCLE`, `DUPLICATE_REVIEW_ID_IN_AUDIT`);
  - dataclasses imutáveis `ConsistencyIssue` e `DualWriteConsistencyReport` (com `is_consistent`, `matched_pairs_count`, contagens físicas e issues ordenadas deterministicamente);
  - função pura `verify_dual_write_consistency` inspecionando sequências em memória de `WorkflowLifecycleEvent` e `AuditEvent` por `review_id`, com comparação semântica timezone-aware de datas, validação defensiva de metadados sem `KeyError` e precedência estrita de duplicidades com isolamento do identificador ambíguo;
  - ordenação canônica e determinística de issues no relatório independente da ordem de chegada dos eventos de entrada;
  - adaptador `verify_repositories_consistency` consumindo instâncias dos protocolos `WorkflowLifecycleRepository` e `AuditRepository`, validado em testes de integração ponta a ponta com simulação de interrupção entre gravações e persistência real em arquivos JSONL após restart de processo;
- **Incremento integrado da Issue #58 (Correction Follow-up Workflow Contract v1):**
  - `GovernanceWorkflow` passa a suportar identificadores opcionais de lineage causal: `predecessor_workflow_id: str | None` e `triggering_review_id: str | None`;
  - identificadores de lineage, quando fornecidos, são validados como strings não-vazias, sanitizados via `strip()` e gravados de forma imutável;
  - função pura de domínio `open_correction_follow_up(...)` originando um novo ciclo de workflow em estado `PENDING_HUMAN_REVIEW` a partir de um predecessor concluído exclusivamente com `HumanDecision.REQUEST_CORRECTION`;
  - validação defensiva de tipos: `predecessor` deve ser instância de `GovernanceWorkflow` (rejeição com `TypeError`) e `recommendation` deve ser `DecisionRecommendation` (rejeição com `ValueError`);
  - predecessor precisa estar revisado (`WorkflowStatus.REVIEWED`), e deliberações `APPROVE` ou `REJECT` são rejeitadas;
  - successor deve possuir `workflow_id` distinto após sanitização (impedindo reaproveitamento de identidade por whitespace externo);
  - successor preserva obrigatoriamente o mesmo `material_id` do predecessor;
  - `opened_at` do successor deve ser timezone-aware e cronologicamente maior ou igual ao fechamento do predecessor (`successor.opened_at >= predecessor.closed_at`), com igualdade no boundary temporal explicitamente suportada;
  - successor nasce com `review = None` e em `PENDING_HUMAN_REVIEW`;
  - predecessor permanece estritamente imutável e inalterado (sem reabertura ou mutação);
  - lineage causal (`predecessor_workflow_id` e `triggering_review_id`) é preservada deterministicamente após a transição para `REVIEWED` via `conclude_governance_workflow(...)`;
  - contrato implementado puramente em memória no domínio, sem persistência da lineage causal em disco e sem introdução de semântica `CORRECTION_APPLIED`;
- **Incremento integrado da Issue #61 (Correction Follow-up Lineage Persistence v1):**
  - hardening de invariantes de lineage causal em `GovernanceWorkflow`: pareamento atômico (`predecessor_workflow_id` e `triggering_review_id` ambos `None` ou ambos preenchidos com strings válidas) e anti-auto-referência (`predecessor_workflow_id != workflow_id`);
  - `WorkflowOpened` passa a suportar identificadores opcionais de lineage causal `predecessor_workflow_id: str | None` e `triggering_review_id: str | None`, com validações idênticas de pareamento atômico, sanitização e anti-auto-referência;
  - serialização versionada com envelope discriminado: root `WorkflowOpened` serializa canonicamente em `schema_version = 1` sem chaves de lineage e sem `event_type`; follow-up `WorkflowOpened` serializa em `schema_version = 2` com `predecessor_workflow_id` e `triggering_review_id`, sem `event_type`;
  - leitura *fail-closed*: registros v1 contendo qualquer chave de lineage (inclusive `None`) são rejeitados com `ValueError`; registros v2 exigem ambas as chaves válidas e rejeitam ausência parcial/total, `null` explícito ou tipos inválidos; versões desconhecidas são rejeitadas;
  - `WorkflowConcluded` permanece exclusivamente em `schema_version = 1`;
  - dispatcher polimórfico de ciclo de vida (`workflow_event_to_record` / `workflow_event_from_record`) mantém compatibilidade de leitura com registros v1 legados e suporta WorkflowOpened em schema_version = 2;
  - projeção determinística (`rehydrate_pending_workflow` e `rehydrate_workflow`) preserva fielmente `predecessor_workflow_id` e `triggering_review_id` tanto para workflows em `PENDING_HUMAN_REVIEW` quanto em `REVIEWED`;
  - princípio `Repository != Projection` estritamente mantido: nenhum predecessor é reconstruído em memória, nenhum grafo é carregado e nenhuma consulta ao repositório ocorre durante a projeção pura;
  - predecessor permanece estritamente imutável e inalterado;
  - teste vertical de integração validando continuidade causal e reidratação de follow-up através de dois restarts simulados por novas instâncias do repositório sobre o mesmo JSONL persistido;
- **Incremento integrado da Issue #64 (Material Revision Provenance v1):**
  - módulo `src/agent_lab/material_revision.py`;
  - dataclass congelado `MaterialRevision` imutável (`frozen=True`, `slots=True`) com `revision_id`, `record: MaterialRecord`, `revised_at: datetime`, `predecessor_revision_id: str | None = None` e `source_review_id: str | None = None`;
  - propriedade `material_id` derivada exclusivamente de `record.material_id` (fonte única da verdade), preservando os campos brutos do `MaterialRecord` sem mutação ou normalização factual;
  - `revision_id`, `predecessor_revision_id` e `source_review_id` validados e armazenados sanitizados via `strip()`;
  - `revised_at` obrigatório e explicitamente timezone-aware (`tzinfo` e `utcoffset()` validados sem fallback para `datetime.now()`);
  - suporte formal a Root Revision (`predecessor=None`, `source_review=None`), Derived Revision (`predecessor_revision_id` presente) e Review-Associated Derived Revision (`predecessor_revision_id` e `source_review_id` presentes);
  - validação de proveniência estrutural: `source_review_id` exige obrigatoriamente a presença de `predecessor_revision_id`;
  - anti-auto-referência estrutural: `predecessor_revision_id != revision_id` após sanitização;
  - função pura `create_successor_revision(predecessor, *, revision_id, record, revised_at, source_review_id=None) -> MaterialRevision` para vincular revisões sucessivas do mesmo material;
  - taxonomia formal de erros: `TypeError` para predecessor não-`MaterialRevision`; `ValueError` para todas as violações estruturais e de sucessão;
  - compatibilidade exata de `material_id`: `record.material_id == predecessor.material_id` por comparação textual exata (sem `strip()` ou coerção);
  - monotonicidade temporal declarada: `successor.revised_at >= predecessor.revised_at`, com suporte explícito a igualdade cronológica no boundary (`successor.revised_at == predecessor.revised_at`);
  - vínculo determinístico de linhagem: `predecessor_revision_id = predecessor.revision_id`;
  - preservação estrita de objetos anteriores: `predecessor`, `predecessor.record` e novo `record` permanecem 100% inalterados;
  - `source_review_id` tratado estritamente como proveniência/contexto declarado, sem consultas a repositórios externos e sem alegações causais;
  - distinção ontológica fundamental: `CorrectionRequest` (intenção/prescrição humana) $\neq$ `MaterialRevision` (estado factual cadastral), sem transformação automática entre intenção e fato;
- **Incremento da Issue #68 (Material Revision Persistence v1 — integrada na main):**
  - módulo `src/agent_lab/material_revision_serialization.py`: serialização canônica versionada com `schema_version = 1` explícito (`material_revision_to_record` / `material_revision_from_record`), round-trip de Root Revision, Derived Revision e Review-Associated Revision, preservação estrita dos 8 campos de `MaterialRecord` com validação de tipos string sem coerção silenciosa (`str()`) ou normalização factual, e validação temporal de `revised_at` timezone-aware em formato ISO 8601;
  - módulo `src/agent_lab/material_revision_repository.py`: protocolo `MaterialRevisionRepository` e repositório append-only `JsonlMaterialRevisionRepository` com durabilidade física explícita (`flush` + `os.fsync`), consulta pontual via `get_by_id`, retorno de tuplas imutáveis em `list_by_material` e `list_all`, e preservação estrita da ordem física de append (sem ordenação por timestamp `revised_at`);
  - hierarquia de exceções: `MaterialRevisionPersistenceError`, `DuplicateMaterialRevisionError` (bloqueio de unicidade estrita por `revision_id` antes da escrita) e `MaterialRevisionCorruptionError` (leitura *fail-closed* acusando `line_number` físico 1-based para linhas vazias, JSON malformado e violações de schema);
  - sobrevivência comprovada a múltiplos restarts simulados por novas instâncias do repositório sobre o mesmo arquivo JSONL em disco sem dependência de estado em memória ou cache;
- **Incremento integrado da Issue #71 (Material Revision Lineage Projection v1):**
  - módulo `src/agent_lab/material_revision_projection.py`: dataclass imutável `MaterialRevisionLineage` (`frozen=True`, `slots=True`) com `material_id: str`, `revisions: tuple[MaterialRevision, ...]`, `root_revision_ids: tuple[str, ...]`, `head_revision_ids: tuple[str, ...]`, `orphan_revision_ids: tuple[str, ...]`, `fork_predecessor_ids: tuple[str, ...]`, `cycle_revision_ids: tuple[str, ...]` e propriedades derivadas (`is_empty`, `is_linear`, `has_orphans`, `has_forks`, `has_multiple_roots`, `has_cycles`, `has_ambiguities`);
  - função pura de leitura e interpretação topológica `project_material_revision_lineage(revisions: Sequence[MaterialRevision]) -> MaterialRevisionLineage` operando estritamente em memória e sem I/O;
  - ordenação determinística e canônica de `revisions` por `revision_id` em ordem lexicográfica ascendente, garantindo equivalência funcional e independência integral da ordem física de entrada;
  - identificação causal exata de raízes (`root_revision_ids`), cabeças (`head_revision_ids`), revisões órfãs (`orphan_revision_ids`), bifurcações (`fork_predecessor_ids` inclusive com predecessor externo ausente) e ciclos indiretos de tamanho $\ge 2$ (`cycle_revision_ids`) com exclusão estrita de nós de cauda externos;
  - validação *fail-closed* nominal e defensiva: `TypeError` para argumentos não-`Sequence` e elementos não-`MaterialRevision`; `ValueError` para sequências vazias `()`, mistura de `material_id` e duplicidade de `revision_id` na entrada;
  - princípio `Repository != Projection` estritamente mantido: repositório preserva a ordem física e os fatos persistidos; projeção interpreta deterministicamente a topologia causal;
  - teste de integração vertical pós-restart (`tests/test_material_revision_lineage_projection_integration.py`) comprovando a integridade do pipeline `JsonlMaterialRevisionRepository` $\rightarrow$ reinicialização $\rightarrow$ `project_material_revision_lineage`.

### 4.3 Limite atual

A versão atual integrada na `main` possui:

- persistência append-only de abertura e conclusão de ciclo de vida operacional (`WorkflowOpened` e `WorkflowConcluded`);
- dual-write entre `AuditEvent` e `WorkflowConcluded` continua não-atômico (escritas append-only independentes em arquivos JSONL distintos), diagnosticável de forma estritamente somente-leitura pós-restart via `verify_repositories_consistency`;
- reparo automático, reconciliação ativa em disco e atomicidade transacional (2PC) permanecem fora do escopo;
- `closed_at` e `review_lead_time` não são persistidos de forma redundante, permanecendo derivados em memória no domínio;
- múltiplos ciclos sucessivos de governança após `REQUEST_CORRECTION` podem ser representados por novos `GovernanceWorkflow`, causalmente vinculados ao predecessor;
- reabertura ou mutação do mesmo `workflow_id` continua estritamente proibida;
- persistência e reidratação em disco da linhagem causal de correction follow-up (`predecessor_workflow_id` e `triggering_review_id`) estão integradas e validadas;
- sucessores em `PENDING_HUMAN_REVIEW` e `REVIEWED` preservam seus identificadores causais após reinicialização;
- predecessor permanece estritamente imutável e inalterado, e nenhuma reconstrução de grafo de predecessores ocorre durante a projeção;
- persistência append-only em disco de `MaterialRevision` integrada na main via `JsonlMaterialRevisionRepository` com durabilidade e leitura fail-closed, e projeção determinística de linhagem em memória integrada na main via `project_material_revision_lineage` (Issue #71);
- sem eleição de `latest revision`, `current revision` ou cabeça canônica; sem eleição por timestamp `revised_at`; sem reparo automático ou mutação em disco;
- conexão de `MaterialRevision` ao pipeline de evidências e recomendações permanece fronteira futura;
- aplicação automática das correções ao material (`CORRECTION_APPLIED`), mutação automática de `MaterialRecord` e reexecução automática de regras/LLM continuam fora do escopo;
- execução síncrona/monoprocesso;
- ausência de locking multiprocesso;
- ausência de autenticação e autorização real (RBAC);
- ausência de filas e SLAs operacionais;
- ausência de integração com ERP;
- ausência de banco de dados relacional ou transacional.

### 4.4 Incremento atual da branch — Issue #74

- **Status:** implementação concluída na branch `feature/issue-74-human-review-application-use-case`, aguardando PR/merge.
- **SPEC:** `docs/specs/0074_human_review_application_use_case_v1.md`.
- **Baseline da branch:** 423 testes GREEN (`unittest` / Python 3.11).
- **Entregas da branch:**
  - módulo `src/agent_lab/human_review_use_case.py`: introdução do primeiro boundary explícito da camada de aplicação do Agent Lab Pascoal (`RecordHumanDecisionUseCase`);
  - dataclass imutável `RecordHumanDecisionResult` (`frozen=True`, `slots=True`) consolidando os quatro artefatos do fluxo (`workflow`, `review`, `audit_event`, `lifecycle_event`);
  - coordenação estrita em duas fases:
    - **Fase 1 (Preparação e Validação Determinística em Memória / Zero I/O):** validação defensiva de entrada (`isinstance(workflow, GovernanceWorkflow) -> TypeError`), construção determinística de `HumanReview` e `AuditEvent` via `record_human_review`, transição pura do workflow via `conclude_governance_workflow` e instanciação de `WorkflowConcluded`;
    - **Fase 2 (Persistência Coordenada):** persistência sequencial em `audit_repository.append(audit_event)` seguida de `workflow_lifecycle_repository.append_concluded(lifecycle_event)`;
  - preservação canônica das responsabilidades (*Application coordena, Domain decide, Repository preserva, Projection interpreta*): zero duplicação de regras de transição ou negócio na Application;
  - preservação estrita da semântica de dual-write não-atômico: falhas propagam de forma *fail-closed* sem 2PC, rollbacks, compensações, retries ou reparos automáticos em disco;
  - integração vertical com repositórios JSONL reais, persistência em disco, sobrevivência a reinicialização de processo, reidratação fiel do estado `REVIEWED` e diagnóstico limpo de consistência cruzada via `verify_repositories_consistency`;
  - **Limites mantidos na branch:** outros use cases de aplicação, filas HITL, SLAs operacionais, UI/Streamlit, APIs e otimizações P-07 permanecem fora de escopo.

### 4.5 Próxima âncora

Próxima âncora arquitetural: a definir somente após novo planejamento humano.

Sequência evolutiva recomendada:

```text
Contrato
  → Memória persistente
  → Identidade verificável
  → Workflow temporal
  → Persistência de abertura de workflow (concluída na #47)
  → Persistência de conclusão de workflow (concluída na #52)
  → Verificação de consistência dual-write (concluída na #55)
  → Contrato de correction follow-up com novo ciclo causal (concluído na #58)
  → Persistência de correction follow-up com schema v2 (concluída na #61)
  → Contrato de proveniência de revisões de material (concluído na #64)
  → Persistência de revisões de material (concluída na #68)
  → Projeção de linhagem de revisões de material (concluída na #71)
  → Avaliação de revisões sucessivas / Integração ERP (futuras)
```

## 5. Invariantes constitucionais

Estas regras não devem ser alteradas incidentalmente:

1. A recomendação automática nunca é uma decisão humana.
2. `requires_human_decision` permanece `True` no escopo atual.
3. Confiança não concede autoridade operacional.
4. A recomendação original não pode ser sobrescrita pela decisão humana.
5. Divergências humano–sistema devem permanecer auditáveis.
6. Revisões concluídas e eventos de auditoria e lifecycle são imutáveis.
7. Reprovação exige justificativa.
8. Solicitação de correção exige justificativa e correção estruturada.
9. Aprovação não pode conter correções pendentes.
10. Timestamps de abertura de workflow, revisão, auditoria e revisão de material devem conter timezone.
11. A integração com ERP não deve executar apenas com base em recomendação automática.
12. O histórico não deve ser reconstruído somente a partir do estado final.
13. Concordância humano–IA não equivale automaticamente à verdade.
14. Casos objetivos devem ser resolvidos por regras antes de recorrer à LLM.
15. A LLM deve operar com contratos de saída estruturados e validados.
16. A recomendação do sistema permanece imutável e atemporal; o tempo pertence ao ciclo de vida (`GovernanceWorkflow`) e à revisão factual (`MaterialRevision`).
17. Um workflow não pode ser concluído mais de uma vez e a transição deve ser pura e determinística.
18. O repositório de ciclo de vida é append-only e opera sob o princípio `Repository != Projection`.
19. Um workflow concluído não é reaberto; um novo ciclo pós-correção exige novo `workflow_id`.
20. Um correction follow-up só pode nascer de predecessor revisado com `HumanDecision.REQUEST_CORRECTION`.
21. O novo ciclo de workflow deve preservar o mesmo `material_id` e não pode começar antes do fechamento do predecessor (`opened_at >= closed_at`).
22. Vínculo causal entre ciclos de workflow não equivale à afirmação ou garantia de que as correções foram aplicadas.
23. `CorrectionRequest` (prescrição normativa humana) $\neq$ `MaterialRevision` (fato cadastral). Não existe transformação automática entre prescrição e estado factual.
24. A revisão sucessora de material deve pertencer com identidade exata ao mesmo material do predecessor e não pode declarar timestamp anterior ao predecessor (`revised_at >= predecessor.revised_at`).
25. `source_review_id` expressa proveniência declarada e não constitui prova de causalidade física, existência da review no repositório ou cumprimento de correções.

Qualquer mudança nessas regras exige:

- Issue explícita;
- evidências;
- análise de impacto;
- nova SPEC ou atualização deliberada de SPEC;
- testes que demonstrem o novo comportamento;
- revisão humana no PR.

## 6. Contratos e módulos centrais

### 6.1 Domínio e validação

```text
src/agent_lab/domain.py
src/agent_lab/normalization.py
src/agent_lab/validator.py
src/agent_lab/decision.py
```

Responsabilidades:

- tipos centrais;
- normalização;
- validação determinística;
- recomendação de decisão atemporal.

### 6.2 LLM e evidências

```text
src/agent_lab/llm_schema.py
src/agent_lab/llm_service.py
src/agent_lab/evidence.py
```

Responsabilidades:

- contrato estruturado da LLM;
- fronteira de execução da LLM;
- evidências originadas por regras e modelo;
- preservação da identidade do material;
- integração evidência–decisão.

### 6.3 Human-in-the-Loop

```text
src/agent_lab/human_review.py
```

Contratos principais:

- `VerifiedSpecialistIdentity`;
- `HumanDecision`;
- `CorrectionRequest`;
- `HumanReview`.

Responsabilidades:

- representar a decisão final humana;
- preservar a recomendação automática;
- registrar especialista e timestamp timezone-aware;
- estruturar correções;
- indicar concordância ou divergência.

### 6.4 Workflow Temporal de Domínio

```text
src/agent_lab/workflow.py
```

Contratos principais:

- `WorkflowStatus`;
- `GovernanceWorkflow`;
- `conclude_governance_workflow`;
- `open_correction_follow_up`.

Responsabilidades:

- representar o ciclo de vida temporal da governança em memória;
- suportar identificadores opcionais de lineage causal `predecessor_workflow_id` e `triggering_review_id`, com validação e sanitização estritas;
- abrir ciclos iniciais em estado `PENDING_HUMAN_REVIEW` com timestamp `opened_at` timezone-aware;
- abrir novos ciclos de follow-up via `open_correction_follow_up` a partir de predecessor concluído exclusivamente com `REQUEST_CORRECTION`, sem reabertura ou mutação do predecessor;
- derivar `material_id`, `status`, `closed_at` e `review_lead_time` sem duplicação de estado;
- executar a transição canônica pura para `REVIEWED` ao receber deliberação de `HumanReview`, preservando a lineage causal existente;
- validar consistência de material, coerência do parecer, tipos defensivos e invariantes cronológicas (`opened_at <= reviewed_at`, `successor.opened_at >= predecessor.closed_at`);
- manter o objeto estritamente imutável.

### 6.5 Ciclo de Vida: Eventos, Projeção, Serialização e Repositório

```text
src/agent_lab/workflow_events.py
src/agent_lab/workflow_projection.py
src/agent_lab/workflow_serialization.py
src/agent_lab/workflow_repository.py
```

Contratos principais:

- `WorkflowOpened`: evento de domínio imutável da abertura do ciclo;
- `WorkflowConcluded`: evento de domínio imutável da conclusão do ciclo com `HumanReview`;
- `WorkflowLifecycleEvent`: TypeAlias unindo `WorkflowOpened | WorkflowConcluded`;
- `rehydrate_pending_workflow`: projeção pura reconstruindo `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW`;
- `rehydrate_workflow`: projeção pura reconstruindo `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` ou `REVIEWED` a partir do histórico;
- `workflow_opened_to_record` / `workflow_opened_from_record`: serialização versionada de abertura com suporte a `schema_version = 1` (abertura raiz sem chaves de lineage e sem `event_type`) e `schema_version = 2` (correction follow-up com `predecessor_workflow_id` e `triggering_review_id`, sem `event_type`);
- `workflow_concluded_to_record` / `workflow_concluded_from_record`: serialização versionada de conclusão (`schema_version = 1`) com `HumanReview` completo;
- `workflow_event_to_record` / `workflow_event_from_record`: dispatcher polimórfico de ciclo de vida com fail-closed estrito;
- `WorkflowLifecycleRepository` (Protocol) / `JsonlWorkflowLifecycleRepository`: repositório append-only em JSONL com escrita durável (`os.fsync`), leitura *fail-closed* e operações de persistência e consulta (`append_opened`, `append_concluded`, `get_opened_by_id`, `get_opened_by_workflow_id`, `list_opened_by_material`, `list_all_opened`, `get_events_by_workflow_id`, `list_all_events`);
- `WorkflowPersistenceError`, `DuplicateWorkflowEventError`, `WorkflowAlreadyOpenedError`, `WorkflowAlreadyConcludedError`, `WorkflowNotOpenedError`, `WorkflowCorruptionError`.

### 6.6 Auditoria

```text
src/agent_lab/audit.py
```

Contratos principais:

- `AuditEventType`;
- `AuditEvent`;
- `HumanReviewResult`;
- `record_human_review`.

Responsabilidades:

- criar evento correlacionado à revisão humana;
- congelar metadados defensivamente;
- preservar material, especialista, instante e decisão;
- produzir resultado auditável sem persistência ou efeitos externos.

### 6.7 Persistência e repositório de auditoria

```text
src/agent_lab/audit_serialization.py
src/agent_lab/audit_repository.py
```

Contratos principais:

- `audit_event_to_record`;
- `audit_event_from_record`;
- `AuditRepository`;
- `JsonlAuditRepository`;
- `AuditPersistenceError`;
- `DuplicateAuditEventError`;
- `AuditCorruptionError`.

Responsabilidades:

- serializar e desserializar `AuditEvent` com versão de schema explícita (`schema_version = 1`);
- persistir eventos de forma append-only em arquivo JSONL local;
- garantir sincronização em disco com `flush` e `os.fsync`;
- recuperar histórico por `event_id`, `material_id` e listagem completa;
- falhar de forma *fail-closed* diante de corrupção ou duplicidade.

### 6.8 Verificação de Consistência Dual-Write

```text
src/agent_lab/consistency.py
```

Contratos principais:

- `ConsistencyIssueType`: enum canônico com as 8 categorias de inconsistência;
- `ConsistencyIssue`: diagnóstico estruturado e imutável de uma inconsistência pontual;
- `DualWriteConsistencyReport`: sumário consolidado com contagens físicas, pares correlacionados 1:1, tupla de issues e propriedade `is_consistent`;
- `verify_dual_write_consistency`: função pura de inspeção cruzada entre eventos de lifecycle e auditoria por `review_id`;
- `verify_repositories_consistency`: adaptador somente-leitura para repositórios `WorkflowLifecycleRepository` e `AuditRepository`.

Responsabilidades:

- correlacionar `WorkflowConcluded` e `AuditEvent` (`HUMAN_REVIEW_RECORDED`) unívocos por `review_id`;
- detectar e isolar identificadores duplicados em qualquer trilha;
- identificar eventos órfãos de conclusão ou auditoria;
- validar coerência de `material_id`, `actor_id` (`reviewer_id`) e validar equivalência temporal semântica timezone-aware entre `concluded.review.reviewed_at` e `audit_event.occurred_at`;
- verificar defensivamente o dicionário de metadados sobrepostos de auditoria;
- garantir ordenação canônica e determinística no diagnóstico final sem efetuar qualquer escrita ou reparo em disco.

### 6.9 Proveniência de Revisões de Material

```text
src/agent_lab/material_revision.py
```

Contratos principais:

- `MaterialRevision`: representação factual imutável de um snapshot cadastral revisionado;
- `create_successor_revision`: função pura para criação de revisão sucessora com integridade de linhagem e temporalidade.

Responsabilidades:

- encapsular `revision_id`, `record: MaterialRecord`, `revised_at: datetime`, `predecessor_revision_id` e `source_review_id`;
- derivar `material_id` diretamente de `record.material_id` (fonte única da verdade);
- validar e sanitizar identificadores de contrato via `strip()` sem normalizar dados brutos do `MaterialRecord`;
- garantir imutabilidade estrita (`frozen=True`, `slots=True`);
- validar obrigatoriedade de `revised_at` timezone-aware;
- assegurar anti-auto-referência estrutural;
- vincular deterministicamente o predecessor na transição de sucessão (`predecessor_revision_id = predecessor.revision_id`);
- validar identidade exata de `material_id` entre predecessor e sucessor;
- validar monotonicidade temporal declarada (`successor.revised_at >= predecessor.revised_at`);
- manter a distinção ontológica estrita entre intenção humana (`CorrectionRequest`) e fato cadastral (`MaterialRevision`).

### 6.10 Persistência e Repositório de Revisões de Material

```text
src/agent_lab/material_revision_serialization.py
src/agent_lab/material_revision_repository.py
```

Contratos principais:

- `SCHEMA_VERSION_V1 = 1`;
- `material_revision_to_record` / `material_revision_from_record`;
- `MaterialRevisionRepository` (Protocol);
- `JsonlMaterialRevisionRepository`;
- `MaterialRevisionPersistenceError`;
- `DuplicateMaterialRevisionError`;
- `MaterialRevisionCorruptionError(line_number)`.

Responsabilidades:

- serializar e desserializar `MaterialRevision` com envelope versionado canônico (`schema_version = 1`);
- validar estritamente tipos string dos 8 campos de `MaterialRecord` e integridade temporal/proveniência na fronteira de serialização de forma *fail-closed*;
- persistir revisões de forma append-only em arquivo JSONL local com durabilidade explícita (`flush` + `os.fsync`);
- recuperar histórico por `revision_id`, `material_id` e listagem geral retornando tuplas imutáveis na ordem física de inserção;
- rejeitar identificadores duplicados (`DuplicateMaterialRevisionError`) antes de qualquer alteração física em disco;
- interromper leituras de arquivos corrompidos ou com linhas vazias reportando `MaterialRevisionCorruptionError` com `line_number` 1-based.

### 6.11 Projeção de Linhagem de Revisões de Material

```text
src/agent_lab/material_revision_projection.py
```

Contratos principais:

- `MaterialRevisionLineage`: read-model imutável da linhagem de revisões de um material;
- `project_material_revision_lineage`: função pura para cálculo causal determinístico e diagnóstico de topologia.

Responsabilidades:

- calcular ordenação canônica de revisões por `revision_id`;
- identificar de forma determinística raízes (`root_revision_ids`) e cabeças concorrentes (`head_revision_ids`);
- diagnosticar revisões órfãs (`orphan_revision_ids`), bifurcações (`fork_predecessor_ids`) e ciclos indiretos fechados (`cycle_revision_ids`), sem incluir nós de cauda externos;
- validar entradas *fail-closed* contra tipos não-`Sequence`, itens não-`MaterialRevision`, sequências vazias, mistura de `material_id` e identificadores duplicados;
- produzir diagnóstico determinístico e imutável sem realizar I/O, mutação de instâncias ou eleição de "revisão atual".

### 6.12 Camada de Aplicação / Use Cases — branch #74 (aguardando PR/merge)

```text
src/agent_lab/human_review_use_case.py
```

Contratos principais:

- `RecordHumanDecisionResult`: estrutura de retorno imutável contendo os quatro artefatos produzidos (`workflow`, `review`, `audit_event`, `lifecycle_event`);
- `RecordHumanDecisionUseCase`: caso de uso de aplicação responsável por orquestrar o registro da decisão humana sobre um workflow de governança pendente.

Responsabilidades:

- validar estruturalmente os argumentos de fronteira da aplicação (`isinstance(workflow, GovernanceWorkflow)`);
- coordenar a preparação e validação determinística de todos os artefatos de domínio em memória antes de qualquer I/O;
- disparar a persistência sequencial em `AuditRepository` e `WorkflowLifecycleRepository`;
- propagar exceções e falhas parciais de persistência de forma *fail-closed* sem mascaramento ou tentativas artificiais de compensação/rollback.

## 7. Comando canônico de testes e baseline

Use sempre:

```powershell
python -m unittest discover -s tests -v
```

Baseline oficial integrado na `main`:

```text
Ran 412 tests
OK
```

Histórico de baselines integrados e baseline atual da branch:
- Baseline inicial / release v0.1.0: 206 testes
- Incremento da Issue #47: +54 testes sobre o baseline anterior de 152
- Incremento da Issue #52: +49 testes sobre o baseline de entrada de 206
- Baseline integrado após a Issue #52: 255 testes
- Incremento da Issue #55: +29 testes sobre o baseline de entrada de 255 (27 testes unitários em `tests/test_dual_write_consistency.py` + 2 testes de integração em `tests/test_dual_write_consistency_integration.py`)
- Baseline integrado após a Issue #55: 284 testes
- Incremento da Issue #58: +13 testes sobre o baseline de entrada de 284
- Baseline integrado após a Issue #58: 297 testes
- Incremento da Issue #61: +23 testes sobre o baseline de entrada de 297
- Baseline integrado após a Issue #61: 320 testes
- Incremento da Issue #64: +27 testes sobre o baseline de entrada de 320 (testes unitários em `tests/test_material_revision.py`)
- Baseline integrado após a Issue #64: 347 testes
- Incremento da Issue #68: +50 testes sobre o baseline de entrada de 347 (31 testes unitários em `tests/test_material_revision_serialization.py` + 19 testes em `tests/test_material_revision_repository.py`)
- Baseline integrado após a Issue #68: 397 testes
- Incremento da Issue #71: +15 testes sobre o baseline de entrada de 397 (14 testes unitários em `tests/test_material_revision_projection.py` + 1 teste de integração em `tests/test_material_revision_lineage_projection_integration.py`)
- Baseline integrado após a Issue #71 (main): 412 testes
- Incremento da Issue #74 (concluído na branch): +11 testes sobre o baseline de entrada de 412 (9 testes unitários em `tests/test_human_review_use_case.py` + 2 testes de integração em `tests/test_human_review_use_case_integration.py`)
- Baseline da branch após a Issue #74: 423 testes

Não assumir `pytest`.

Uma migração de runner somente poderá ocorrer por decisão explícita, documentada e testada.

## 8. Métrica de custo do baseline

O baseline utiliza uma função de custo ponderado inicial:

```text
duplicidade não detectada = custo 5
revisão humana desnecessária = custo 1
```

Representação:

```text
custo = 5 × falsos negativos de duplicidade
      + 1 × revisões desnecessárias
```

Interpretação:

- deixar uma duplicidade entrar tende a produzir efeitos sistêmicos;
- uma revisão desnecessária tende a produzir custo localizado de tempo e fila;
- o valor 5:1 é uma hipótese inicial de risco, não uma constante universal;
- a razão deverá ser calibrada com dados industriais reais.

## 9. Fronteira de autoridade

`DecisionRecommendation` é uma recomendação, não uma autorização.

Mesmo quando:

```text
decision = APPROVE
confidence = 1.0
```

o contrato deve preservar:

```text
requires_human_decision = True
```

Razão:

```text
confiança epistemológica ≠ autoridade operacional
```

Uma integração futura com ERP deverá exigir decisão humana válida e auditável, e não apenas recomendação automática.

## 10. Protocolo diário de reentrada

Ao iniciar uma nova rotina do Agent Lab, seguir esta ordem.

### Passo 1 — Ler este Compass

Confirmar:

- propósito;
- estado arquitetural;
- baseline;
- última entrega;
- próxima âncora;
- invariantes.

### Passo 2 — Verificar o Git

```powershell
git status
git branch --show-current
git log -5 --oneline
```

Confirmar:

- branch atual;
- sincronização com `origin/main`;
- working tree;
- últimos commits.

### Passo 3 — Confirmar o contrato operacional

Antes de recomendar comandos:

- verificar Python configurado;
- verificar workflow da CI;
- verificar runner oficial;
- verificar estrutura de arquivos;
- não substituir fatos do repositório por convenções genéricas.

### Passo 4 — Executar o baseline

```powershell
python -m unittest discover -s tests -v
```

Não iniciar nova implementação se o baseline estiver vermelho sem diagnóstico explícito.

### Passo 5 — Recapitular o estado

Registrar em poucas linhas:

```text
Núcleo atual:
Última entrega:
Baseline:
Limitação principal:
Próxima âncora:
```

### Passo 6 — Somente então abrir nova Issue

Toda Issue deve conter, conforme aplicável:

- problema;
- contexto;
- objetivo;
- evidências;
- solução ou hipóteses;
- escopo;
- fora do escopo;
- riscos e limitações;
- impactos;
- critérios de aceite;
- estratégia de validação.

## 11. Fluxo de engenharia

Fluxo padrão:

```text
Issue
  → branch
  → SPEC
  → commit documental
  → teste RED
  → commit do teste
  → implementação GREEN
  → regressão completa
  → atualização da SPEC
  → push
  → Pull Request
  → CI
  → merge
  → exclusão da branch
  → sincronização da main
  → validação pós-merge
  → Relatório Diário
```

O Relatório Diário é uma etapa obrigatória do encerramento técnico.

## 12. Hierarquia das fontes de verdade

Em caso de dúvida ou conflito, usar esta ordem:

1. comportamento validado pelos testes atuais;
2. código integrado à `main`;
3. SPEC implementada mais recente;
4. workflows e configurações do repositório;
5. este `PROJECT_COMPASS.md`;
6. Relatórios Diários;
7. memória conversacional;
8. convenções genéricas de engenharia.

Se este Compass divergir da `main`, a `main` e seus testes prevalecem e o Compass deve ser atualizado.

## 13. Decisões deliberadamente adiadas

- reabertura ou mutação do mesmo workflow após `REQUEST_CORRECTION` continua adiada/proibida no contrato atual (cada ciclo pós-correção é um novo workflow imutável);
- aplicação automática das `CorrectionRequest` ao material (`CORRECTION_APPLIED`) e mutação automática de `MaterialRecord` continuam adiadas;
- campos `diff`/`changed_fields` persistidos, eleição de `latest revision` / `current revision` / `canonical head` e ordenação semântica por timestamp `revised_at` continuam adiados (a persistência JSONL append-only de `MaterialRevision` foi integrada na Issue #68 e a projeção pura de linhagem determinística sem eleição de head foi integrada na Issue #71);
- conexão de `MaterialRevision` ao pipeline de evidências (`EvidenceCollection`) e recomendações (`DecisionRecommendation`), e reexecução automática de regras/LLM após revisão continuam adiadas;
- atomicidade transacional em disco, 2PC, reparo automático ou reconciliação ativa entre trilha de auditoria e trilha de lifecycle (a detecção e o diagnóstico determinístico somente-leitura foram integrados na Issue #55; intervenções ativas em disco continuam adiadas);
- persistência em banco de dados relacional ou transacional;
- proteção física ou criptográfica contra adulteração do histórico;
- event sourcing completo;
- concorrência multiprocesso e distributed locking;
- autenticação e autorização real (RBAC);
- papéis e segregação de funções;
- taxonomia completa de motivos;
- filas e SLAs;
- notificações e escalonamento;
- interface do especialista;
- integração e fila de injeção ERP;
- idempotência e retentativas da integração;
- métricas de override humano–IA;
- benchmark industrial com ground truth;
- automação parcial por classe de risco.

Não implementar uma decisão adiada incidentalmente dentro de outra Issue.

## 14. Esteira evolutiva

Frentes oficiais de evolução:

- PoC vendável de diagnóstico de qualidade cadastral;
- Duplicate Intelligence;
- prevenção de novos cadastros duplicados;
- copiloto do analista PDM;
- arquitetura híbrida de regras, similaridade, RAG e LLM;
- Evidence Engine;
- Human-in-the-Loop;
- workflow temporal e métricas de ciclo de revisão;
- persistência e reidratação de lifecycle de workflow;
- benchmark com ground truth;
- métricas de precision, recall e F1;
- versionamento de dados;
- dashboards;
- integração com CSV, Excel, SQL e ERP.

Essas frentes formam uma esteira; não são autorização para desenvolvimento simultâneo.

## 15. Critérios para a próxima Issue

Antes de abrir a próxima Issue, responder:

1. Qual limitação atual ela resolve?
2. Qual evidência demonstra que a limitação importa agora?
3. Qual é a menor entrega vertical testável?
4. Quais invariantes ela deve preservar?
5. O que ficará explicitamente fora do escopo?
6. Como saberemos que a implementação funcionou?
7. Quantos novos riscos operacionais ela introduz?
8. A nova camada pode ser removida ou substituída sem corromper o domínio?

## 16. Política de atualização deste Compass

Atualizar este documento quando houver mudança em:

- baseline de testes;
- comando canônico;
- arquitetura;
- invariantes;
- última entrega;
- próxima âncora;
- módulos centrais;
- limites do sistema;
- decisões deliberadamente adiadas.

Não atualizar o Compass por alterações cosméticas ou tarefas que não modifiquem o estado estrutural do projeto.

Toda atualização deve ocorrer na mesma branch da mudança que a tornou necessária, ou em uma Issue documental explicitamente vinculada.

## 17. Estado resumido para reentrada rápida

```text
AGENT LAB PASCOAL

Propósito:
Governança assistida de materiais PDM/BOM.

Release formal atual:
v0.1.0 — Governed Agent Workflow Baseline (publicada / Latest | tag v0.1.0 | commit c5a9e46).

Distinção de governança:
Merge fecha um incremento; release fecha uma versão coerente.

MAIN INTEGRADA:
- Baseline integrado na main: 412 testes | unittest | Python 3.11.
- Última entrega funcional integrada na main: Issue #71 | Material Revision Lineage Projection v1 | PR #72 (merge eea57ee).
- Última SPEC integrada: docs/specs/0071_material_revision_lineage_projection_v1.md.
- Último PR funcional integrado: PR #72.
- Último merge funcional: eea57ee.
- Arquitetura integrada: Regras + LLM estruturada + evidências + recomendação + identidade verificável
  + decisão humana + workflow temporal + persistência append-only de WorkflowOpened (v1/v2) e WorkflowConcluded (v1)
  + projeção pura rehydrate_workflow (reconstruindo deterministicamente PENDING_HUMAN_REVIEW e REVIEWED após restarts com preservação de lineage causal)
  + auditoria append-only desacoplada
  + verificação determinística e somente-leitura de consistência dual-write pós-restart (verify_dual_write_consistency / verify_repositories_consistency)
  + correction follow-up causal com persistência de WorkflowOpened v2 e reidratação de lineage em PENDING_HUMAN_REVIEW e REVIEWED pós-restart
  + MaterialRevision factual e imutável com identidade temporal explícita, predecessor_revision_id, source_review_id declarativo, create_successor_revision pura, identidade exata de material_id e monotonicidade temporal
  + persistência append-only de MaterialRevision em JSONL com schema_version=1 canônico, JsonlMaterialRevisionRepository durável (flush + fsync), unicidade de revision_id e diagnóstico fail-closed de corrupção com line_number 1-based
  + projeção pura MaterialRevisionLineage determinística em memória via project_material_revision_lineage com ordenação canônica por revision_id, identificação de raízes, cabeças, órfãos, bifurcações (inclusive com predecessor ausente) e ciclos indiretos fechados (sem caudas externas), e validações fail-closed de entrada.
- Princípios: Repository != Projection | WorkflowLifecycleEvent != AuditEvent | DecisionRecommendation != HumanReview | CorrectionRequest != MaterialRevision (intenção humana != estado factual).
- Autoridade: A IA recomenda; o humano decide; a auditoria preserva o percurso; o lifecycle preserva o estado operacional; MaterialRevision registra o fato cadastral revisionado; MaterialRevisionLineage interpreta deterministicamente o grafo de linhagem.
- Limites atuais: Dual-write AuditEvent/WorkflowConcluded continua não-atômico, com detecção/diagnóstico somente-leitura integrado na #55 e sem reconciliação/reparo automático;
  correction follow-up causal persiste lineage mas não reconstrói grafo de predecessores; sem reabertura ou mutação do mesmo workflow; sem aplicação automática das correções (CORRECTION_APPLIED); sem eleição de latest/current revision ou canonical head; sem eleição por revised_at; sem conexão MaterialRevision -> Evidence/DecisionRecommendation; sem reexecução automática de regras/LLM; sem locking multiprocesso, RBAC real, filas, SLAs ou ERP.

INCREMENTO ATUAL:
- Issue #74 — Human Review Application Use Case v1 — implementação concluída na branch, aguardando PR/merge.
- SPEC atual da branch: docs/specs/0074_human_review_application_use_case_v1.md.
- Baseline da branch: 423 testes GREEN | unittest | Python 3.11.
- Princípio da branch: Application coordena; Domain decide; Repository preserva; Projection interpreta.
- RecordHumanDecisionUseCase introduzido na branch como primeiro boundary explícito de Application.

PRÓXIMA ÂNCORA:
- Ainda não definida; deve ser escolhida somente após novo planejamento humano.

Comando oficial:
python -m unittest discover -s tests -v
```
