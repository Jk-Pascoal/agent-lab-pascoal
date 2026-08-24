# SPEC 0061 — Correction Follow-up Lineage Persistence v1 — Persistência e reidratação de linhagem causal de follow-up

> Especificação técnica para extensão da persistência de ciclo de vida e projeção determinística
> de workflows sucessores de governança, preservando os identificadores de linhagem causal
> (`predecessor_workflow_id` e `triggering_review_id`) através de reinicializações de processo.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0061` |
| Status | `Implementada, Validada e Integrada na main` |
| Issue relacionada | `#61` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-24` |
| Última atualização | `2026-08-24` |

---

## 1. Contexto

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais PDM/BOM. O baseline atual integrado na branch `main` possui 297 testes aprovados e consolida:

- Evidence Engine determinístico e fronteira LLM estruturada com guardrails de identidade;
- recommendation pipeline com compulsoriedade constitucional de `requires_human_decision = True`;
- deliberação humana estruturada via `HumanReview` com `VerifiedSpecialistIdentity`;
- persistência auditável durável append-only (`AuditEvent` com `schema_version = 1` e `JsonlAuditRepository`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow` com `opened_at`, `closed_at`, `review_lead_time`);
- persistência append-only de abertura e conclusão de ciclo de vida (`WorkflowOpened`, `WorkflowConcluded` com `schema_version = 1` e `JsonlWorkflowLifecycleRepository`);
- projeção determinística de reidratação (`rehydrate_workflow`) reconstruindo `GovernanceWorkflow` nos estados `PENDING_HUMAN_REVIEW` e `REVIEWED`;
- verificação somente-leitura de consistência cruzada entre as trilhas desacopladas de lifecycle e auditoria (`verify_dual_write_consistency` e `verify_repositories_consistency`);
- **contrato em memória de follow-up de correção integrado na Issue #58:** `GovernanceWorkflow` suporta `predecessor_workflow_id` e `triggering_review_id`, e a função pura `open_correction_follow_up(...)` instancia um novo workflow successor vinculado causalmente ao predecessor concluído com `HumanDecision.REQUEST_CORRECTION`.

Baseline oficial verificado:

```text
Ran 297 tests in 0.532s
OK
```

Runner oficial:

```powershell
python -m unittest discover -s tests -v
```

Na arquitetura atual, a lineage causal do successor existe exclusivamente em memória no objeto `GovernanceWorkflow`. Ao persistir a abertura de um workflow successor através de `WorkflowOpened` e reiniciar o processo, a reidratação atual (`rehydrate_workflow` / `rehydrate_pending_workflow`) perde esses identificadores causais, retornando instâncias com `predecessor_workflow_id = None` e `triggering_review_id = None`.

---

## 2. Problema, evidências e impacto

### Problema

A persistência do ciclo de vida de abertura (`WorkflowOpened`), a camada de serialização (`workflow_serialization.py`) e as projeções de reidratação (`workflow_projection.py`) foram concebidas antes da introdução da linhagem causal da Issue #58. Consequentemente:

1. `WorkflowOpened` não possui campos para transportar `predecessor_workflow_id` e `triggering_review_id`;
2. A serialização (`workflow_opened_to_record` / `workflow_opened_from_record`) não grava nem recupera identificadores causais;
3. As funções de projeção (`rehydrate_pending_workflow` e `rehydrate_workflow`) reconstituem `GovernanceWorkflow` sem propagar os campos de linhagem causal;
4. Após reinicialização do processo (restart), um workflow successor reidratado a partir do log JSONL perde seu vínculo causal com o predecessor e a revisão que o originou, tornando-se indistinguível de um workflow de abertura inicial raiz;
5. O domínio (`GovernanceWorkflow`) na `main` valida `predecessor_workflow_id` e `triggering_review_id` de forma independente, permitindo instanciações diretas com lineage parcial ou auto-referencial que entrariam em contradição com as garantias estritas exigidas na persistência.

### Evidências no código atual

1. `GovernanceWorkflow.__post_init__` em `src/agent_lab/workflow.py` valida individualmente a não-vacuidade dos IDs de lineage se presentes, mas não valida o pareamento atômico obrigatório nem a diferenciação `predecessor_workflow_id != workflow_id`.
2. `WorkflowOpened` em `src/agent_lab/workflow_events.py` define apenas `event_id`, `workflow_id`, `recommendation` e `opened_at`.
3. `workflow_opened_to_record` e `workflow_opened_from_record` em `src/agent_lab/workflow_serialization.py` operam exclusivamente sobre o envelope v1 sem suporte a lineage.
4. `rehydrate_pending_workflow` e `rehydrate_workflow` em `src/agent_lab/workflow_projection.py` instanciam `GovernanceWorkflow` omitindo `predecessor_workflow_id` e `triggering_review_id` (assumindo o default `None`).
5. Nenhum teste de integração atual cobre a persistência e reidratação pós-restart de um workflow originado por `open_correction_follow_up`.

### Impacto

- **Perda de rastreabilidade temporal e causal após restart:** a linhagem entre ciclos de governança do mesmo material é efêmera e não resiste a reinicializações operacionais;
- **Ambiguidade operacional:** auditores e analistas não conseguem distinguir, após recuperação do estado persistido, se uma revisão pendente ou concluída é um ciclo inicial ou um follow-up decorrente de solicitação de correção prévia;
- **Inconsistência entre memória e disco:** workflows criados via `open_correction_follow_up` possuem lineage em memória durante a execução, mas tornam-se desconectados após persistência e reidratação.

---

## 3. Hipótese

1. Aplicar hardening de domínio em `GovernanceWorkflow` e no evento `WorkflowOpened` para exigir como invariante inviolável o pareamento atômico da lineage (ambos `None` ou ambos strings não-vazias) e a rejeição de auto-referência (`predecessor_workflow_id != workflow_id`).
2. Estender `WorkflowOpened` para transportar opcionalmente os identificadores causais (`predecessor_workflow_id: str | None` e `triggering_review_id: str | None`).
3. Adotar versionamento explícito e *fail-closed* na serialização de abertura:
   - Root workflows utilizam `schema_version = 1` e preservam a estrutura serializada canônica dos root openings v1 (sem chaves de linhagem);
   - Follow-up workflows utilizam `schema_version = 2` e exigem a presença obrigatória de `predecessor_workflow_id` e `triggering_review_id` como strings não-vazias;
   - Leitores legados rejeitarão registros v2 por versão não suportada, impedindo a perda silenciosa de lineage.
4. Propagar os identificadores de forma fail-closed e determinística pelas funções puras de projeção (`rehydrate_pending_workflow` e `rehydrate_workflow`).

Dessa forma:
- Workflows de abertura raiz continuam operando com estrutura serializada v1 canônica;
- Workflows de follow-up preservam deterministicamente seu vínculo causal através de reinicializações de processo em ambos os estados operacionais (`PENDING_HUMAN_REVIEW` e `REVIEWED`);
- O domínio e a persistência permanecem estritamente alinhados e livres de estados parciais ambíguos.

---

## 4. Objetivo

Implementar o hardening de invariantes de lineage no domínio, a persistência durável e a reidratação pura da linhagem causal de follow-up de correção no ciclo de vida de governança:

1. Consolidar o pareamento atômico e a rejeição de auto-referência em `GovernanceWorkflow` (`src/agent_lab/workflow.py`) e em `WorkflowOpened` (`src/agent_lab/workflow_events.py`);
2. Estender o evento de domínio imutável `WorkflowOpened` com `predecessor_workflow_id: str | None = None` e `triggering_review_id: str | None = None`;
3. Implementar versionamento discriminado fail-closed na serialização de abertura (`workflow_opened_to_record` e `workflow_opened_from_record`):
   - Aberturas raiz são serializadas com `schema_version = 1` sem chaves de lineage;
   - Aberturas de follow-up são serializadas com `schema_version = 2` com ambas as chaves de lineage obrigatórias;
   - Registros v1 contendo chaves de lineage são rejeitados com `ValueError` (*fail-closed*);
   - Registros v2 com ausência total, parcial, `null` explícito ou tipos inválidos de lineage são rejeitados com `ValueError` (*fail-closed*);
   - Qualquer `schema_version` diferente de `1` e `2` é rejeitado com `ValueError` (*fail-closed*);
4. Preservar `WorkflowConcluded` em `schema_version = 1` sem alteração de seu contrato;
5. Atualizar as projeções puras de reidratação (`rehydrate_pending_workflow` e `rehydrate_workflow`) para reconstituir `GovernanceWorkflow` propagando fielmente a lineage causal;
6. Assegurar que tanto o estado `PENDING_HUMAN_REVIEW` quanto o estado `REVIEWED` de um successor preservem deterministicamente a lineage após múltiplos restarts de processo;
7. Manter 100% dos invariantes constitucionais e a suíte completa verde no runner nativo `unittest`.

---

## 5. Escopo

### Incluído

- **Hardening de Domínio (`src/agent_lab/workflow.py`):**
  - Atualização do `__post_init__` de `GovernanceWorkflow`:
    - Validação de pareamento atômico: `predecessor_workflow_id` e `triggering_review_id` devem ser ambos `None` ou ambos strings não-vazias após `strip()`;
    - Validação de auto-referência: `predecessor_workflow_id != workflow_id`.
- **Evento de ciclo de vida (`src/agent_lab/workflow_events.py`):**
  - Adição dos campos opcionais `predecessor_workflow_id: str | None = None` e `triggering_review_id: str | None = None` ao dataclass congelado `WorkflowOpened`;
  - Validação defensiva no `__post_init__` de `WorkflowOpened`:
    - Sanitização com `strip()` e rejeição de strings vazias/whitespace para identificadores de lineage quando fornecidos;
    - Regra de pareamento atômico (integridade causal): ambos os campos devem ser `None` (abertura raiz) ou ambos devem ser strings válidas (abertura de follow-up). Lineage parcial levanta `ValueError`;
    - Diferenciação de identidade: `predecessor_workflow_id != workflow_id` levanta `ValueError`.
- **Serialização de ciclo de vida (`src/agent_lab/workflow_serialization.py`):**
  - Introdução da constante `SCHEMA_VERSION_V2 = 2` mantendo `SCHEMA_VERSION_V1 = 1`;
  - Atualização de `workflow_opened_to_record`:
    - Se `event.predecessor_workflow_id is None`: emite `"schema_version": 1` e omite as chaves de lineage (preservação da estrutura canônica v1);
    - Se presente: emite `"schema_version": 2` e inclui `"predecessor_workflow_id"` e `"triggering_review_id"`;
  - Atualização de `workflow_opened_from_record`:
    - Se `schema_version == 1`: exige que as chaves de lineage estejam ausentes e instancia `WorkflowOpened` com lineage `None`; se alguma chave de lineage estiver presente em registro v1, levanta `ValueError`;
    - Se `schema_version == 2`: exige que ambas as chaves de lineage estejam presentes como strings não-vazias e distintas de `workflow_id`; se houver ausência parcial, total, `null` explícito ou tipo não-string, levanta `ValueError`;
    - Se `schema_version` for diferente de `1` e `2`: levanta `ValueError`;
  - Preservação estrita do dispatcher polimórfico `workflow_event_to_record` e `workflow_event_from_record`.
- **Projeção de ciclo de vida (`src/agent_lab/workflow_projection.py`):**
  - Atualização de `rehydrate_pending_workflow(event: WorkflowOpened)` para passar `predecessor_workflow_id=event.predecessor_workflow_id` e `triggering_review_id=event.triggering_review_id` para `GovernanceWorkflow`;
  - Atualização de `rehydrate_workflow(events: Sequence[WorkflowLifecycleEvent])` para propagar `predecessor_workflow_id=opened.predecessor_workflow_id` e `triggering_review_id=opened.triggering_review_id` tanto para workflows pendentes (`len(events) == 1`) quanto revisados (`len(events) == 2`).
- **Repositório de ciclo de vida (`src/agent_lab/workflow_repository.py`):**
  - Compatibilidade transparente com `JsonlWorkflowLifecycleRepository`, persistindo e recuperando registros lineage-bearing v2 sem alteração nas assinaturas de métodos do protocolo.
- **Suíte de testes:**
  - Testes unitários de hardening de domínio em `tests/test_workflow.py`;
  - Testes unitários de evento em `tests/test_workflow_events.py`;
  - Testes unitários de serialização e round-trip em `tests/test_workflow_serialization.py`, cobrindo root openings (v1), follow-ups (v2), validações de schema version, lineage parcial, `null` explícito e payloads corrompidos;
  - Testes unitários de projeção em `tests/test_workflow_projection.py`;
  - Teste de integração ponta a ponta com múltiplos restarts reais de processo em novo arquivo `tests/test_workflow_lineage_persistence_integration.py`.

### Fora do escopo

- Aplicação automática de correções ao material cadastral (`CorrectionRequest` sobre `MaterialRecord`);
- Semântica de confirmação de correção aplicada (`CORRECTION_APPLIED`);
- Mutação ou reabertura do workflow predecessor ou reutilização do mesmo `workflow_id`;
- Reconstrução em memória do grafo completo do predecessor a partir do successor durante a projeção (o successor preserva apenas os identificadores de linhagem);
- Alteração do contrato de auditoria (`AuditEvent` / `audit.py` / `audit_serialization.py`);
- Alteração do contrato de conclusão (`WorkflowConcluded`, que permanece em `schema_version = 1`);
- Concorrência multiprocesso, locking distribuído ou banco relacional;
- Transações distribuídas (2PC), reconciliação ativa ou reparo automático em disco;
- Filas operacionais, autenticação/autorização real, RBAC, SLAs, UI ou integração ERP.

---

## 6. Invariantes

### Invariantes específicas da Issue #61

1. **Separação Repositório vs Projeção (`Repository != Projection`):** o repositório (`JsonlWorkflowLifecycleRepository`) é um store append-only durável de eventos de domínio; a projeção (`rehydrate_workflow`) é uma função pura e determinística em memória que reconstitui `GovernanceWorkflow` sem reexecução de regras, IO ou chamadas a LLM.
2. **Separação Ciclo de Vida vs Auditoria (`WorkflowLifecycleEvent != AuditEvent`):** a persistência da linhagem causal pertence estritamente ao ciclo de vida temporal de governança (`WorkflowOpened`), sem misturar-se com eventos de auditoria de deliberação pós-decisão (`AuditEvent`).
3. **Separação Recomendação vs Decisão (`DecisionRecommendation != HumanReview`):** `DecisionRecommendation` permanece a proposta atemporal do sistema; `HumanReview` permanece a decisão final do especialista.
4. **Append-Only e Imutabilidade:** arquivos JSONL de lifecycle são estritamente append-only; eventos gravados e instâncias de dataclass são imutáveis (`frozen=True`, `slots=True`).
5. **Versionamento e Desserialização Fail-Closed:** 
   - Aberturas raiz usam `schema_version = 1`; follow-ups usam `schema_version = 2`;
   - Registros com versões não suportadas ou combinações inválidas de versão e campos falham imediatamente com `ValueError` ou `WorkflowCorruptionError`;
   - Leitores legados rejeitam registros v2 por versão não suportada, impedindo a aceitação silenciosa de registros com perda de causalidade.
6. **Preservação da Estrutura Serializada Canônica dos Root Openings v1:** aberturas raiz sem lineage não serializam chaves de linhagem; leituras de registros v1 legados continuam sendo desserializadas perfeitamente com lineage `None`.
7. **Imutabilidade do Predecessor:** o workflow predecessor não é alterado, reaberto ou mutado pela existência do sucessor ou pela persistência da lineage.
8. **Novo `workflow_id` para o Successor:** o workflow successor recebe obrigatoriamente um identificador próprio e distinto do predecessor (`successor.workflow_id != predecessor.workflow_id`).
9. **Ausência de Semântica `CORRECTION_APPLIED`:** a preservação durável da linhagem causal registra unicamente que o novo ciclo decorreu de uma solicitação de correção anterior; não atesta nem valida a aplicação substantiva das alterações no cadastro do material.
10. **Runner Oficial:** todos os testes devem ser executados exclusivamente através de `python -m unittest discover -s tests -v`.

---

## 7. Responsabilidade humana e limites do agente

- A deliberação de solicitar correções (`HumanDecision.REQUEST_CORRECTION`) é ato privativo do especialista humano provido de identidade verificável estruturada (`VerifiedSpecialistIdentity`). O sistema não assume nem implementa mecanismos de autenticação/autorização real ou RBAC neste estágio.
- A persistência da linhagem causal assegura rastreabilidade técnica durável entre ciclos de governança sucessivos, viabilizando auditoria e continuidade operacional após indisponibilidades ou reinicializações.
- O agente não infere correções, não encerra ciclos pendentes e não muta cadastros.

---

## 8. Requisitos

### Requisitos funcionais

- `RF-01`: Consolidar em `GovernanceWorkflow` o pareamento atômico de lineage (ambos `None` ou ambos `str` não-vazia) e a rejeição de `predecessor_workflow_id == workflow_id` com `ValueError`.
- `RF-02`: Permitir instanciar `WorkflowOpened` raiz sem lineage (`predecessor_workflow_id=None` e `triggering_review_id=None`) preservando compatibilidade de leitura e a estrutura serializada canônica dos root openings v1.
- `RF-03`: Permitir instanciar `WorkflowOpened` de follow-up informando `predecessor_workflow_id` e `triggering_review_id` válidos (strings não-vazias e distintas do `workflow_id`).
- `RF-04`: Rejeitar em `WorkflowOpened` instanciações com lineage parcial (um campo preenchido e outro `None`) com `ValueError`.
- `RF-05`: Rejeitar em `WorkflowOpened` lineage auto-referencial (`predecessor_workflow_id == workflow_id`) com `ValueError`.
- `RF-06`: Serializar `WorkflowOpened` raiz via `workflow_opened_to_record` com `"schema_version": 1` omitindo as chaves de lineage.
- `RF-07`: Serializar `WorkflowOpened` de follow-up via `workflow_opened_to_record` com `"schema_version": 2` incluindo `"predecessor_workflow_id"` e `"triggering_review_id"`.
- `RF-08`: Desserializar `WorkflowOpened` com `schema_version == 1` via `workflow_opened_from_record`, exigindo a ausência de chaves de lineage e rejeitando sua presença com `ValueError`.
- `RF-09`: Desserializar `WorkflowOpened` com `schema_version == 2` via `workflow_opened_from_record`, exigindo ambas as chaves de lineage como strings não-vazias e rejeitando ausência total, parcial, `null` explícito ou tipos inválidos com `ValueError`.
- `RF-10`: Rejeitar em `workflow_opened_from_record` qualquer `schema_version` diferente de `1` e `2` com `ValueError`.
- `RF-11`: Garantir round-trip completo de serialização para aberturas raiz (v1) e follow-ups (v2).
- `RF-12`: Reconstituir fielmente `predecessor_workflow_id` e `triggering_review_id` em `rehydrate_pending_workflow(event)` para `GovernanceWorkflow` em estado `PENDING_HUMAN_REVIEW`.
- `RF-13`: Reconstituir fielmente `predecessor_workflow_id` e `triggering_review_id` em `rehydrate_workflow(events)` tanto para `PENDING_HUMAN_REVIEW` (1 evento) quanto para `REVIEWED` (2 eventos).
- `RF-14`: Persistir e recuperar um correction follow-up preservando lineage através de múltiplos restarts.

### Requisitos não-funcionais e de qualidade

- `RQ-01` (Imutabilidade): Entidades congeladas (`frozen=True`, `slots=True`).
- `RQ-02` (Determinismo): Projeções puras, síncronas e sem efeitos colaterais.
- `RQ-03` (Fail-closed): Erros em payload, tipos inválidos, `null` explícito ou violações de integridade falham imediatamente sem degradação silenciosa.
- `RQ-04` (Preservação de Estrutura Canônica): Preservação estrita da estrutura serializada canônica dos root openings v1 e de `WorkflowConcluded` em `schema_version = 1`.
- `RQ-05` (Testabilidade e Rigor): Validação por testes unitários direcionados, integração ponta a ponta e regressão completa via `python -m unittest discover -s tests -v`.

---

## 9. Proposta técnica detalhada

### 9.1 Hardening de Domínio (`workflow.py`)

```python
@dataclass(frozen=True, slots=True)
class GovernanceWorkflow:
    workflow_id: str
    recommendation: DecisionRecommendation
    opened_at: datetime
    review: HumanReview | None = None
    predecessor_workflow_id: str | None = None
    triggering_review_id: str | None = None

    def __post_init__(self) -> None:
        sanitized_workflow_id = _require_non_blank(
            self.workflow_id, "workflow_id"
        )
        object.__setattr__(self, "workflow_id", sanitized_workflow_id)

        if not isinstance(self.recommendation, DecisionRecommendation):
            raise ValueError("recommendation must be a DecisionRecommendation")

        _require_aware_datetime(self.opened_at, "opened_at")

        if self.review is not None:
            if not isinstance(self.review, HumanReview):
                raise ValueError("review must be a HumanReview")
            if self.review.material_id != self.recommendation.material_id:
                raise ValueError(
                    "review material_id must match recommendation material_id"
                )
            if (
                self.review.system_recommendation
                != self.recommendation.decision
            ):
                raise ValueError(
                    "review system_recommendation must match recommendation decision"
                )
            if self.review.reviewed_at < self.opened_at:
                raise ValueError(
                    "review reviewed_at cannot be earlier than workflow opened_at"
                )

        has_pred = self.predecessor_workflow_id is not None
        has_trig = self.triggering_review_id is not None

        if has_pred != has_trig:
            raise ValueError(
                "predecessor_workflow_id and triggering_review_id must both be provided or both be None"
            )

        if has_pred:
            sanitized_pred = _require_non_blank(
                self.predecessor_workflow_id, "predecessor_workflow_id"
            )
            if sanitized_pred == sanitized_workflow_id:
                raise ValueError(
                    "predecessor_workflow_id must differ from workflow_id"
                )
            object.__setattr__(
                self, "predecessor_workflow_id", sanitized_pred
            )

        if has_trig:
            sanitized_trig = _require_non_blank(
                self.triggering_review_id, "triggering_review_id"
            )
            object.__setattr__(
                self, "triggering_review_id", sanitized_trig
            )
```

### 9.2 Evento de Ciclo de Vida (`workflow_events.py`)

```python
@dataclass(frozen=True, slots=True)
class WorkflowOpened:
    event_id: str
    workflow_id: str
    recommendation: DecisionRecommendation
    opened_at: datetime
    predecessor_workflow_id: str | None = None
    triggering_review_id: str | None = None

    def __post_init__(self) -> None:
        sanitized_event_id = _require_non_blank(self.event_id, "event_id")
        object.__setattr__(self, "event_id", sanitized_event_id)

        sanitized_workflow_id = _require_non_blank(
            self.workflow_id, "workflow_id"
        )
        object.__setattr__(self, "workflow_id", sanitized_workflow_id)

        if not isinstance(self.recommendation, DecisionRecommendation):
            raise ValueError("recommendation must be a DecisionRecommendation")

        _require_aware_datetime(self.opened_at, "opened_at")

        has_pred = self.predecessor_workflow_id is not None
        has_trig = self.triggering_review_id is not None

        if has_pred != has_trig:
            raise ValueError(
                "predecessor_workflow_id and triggering_review_id must both be provided or both be None"
            )

        if has_pred:
            sanitized_pred = _require_non_blank(
                self.predecessor_workflow_id, "predecessor_workflow_id"
            )
            if sanitized_pred == sanitized_workflow_id:
                raise ValueError(
                    "predecessor_workflow_id must differ from workflow_id"
                )
            object.__setattr__(
                self, "predecessor_workflow_id", sanitized_pred
            )

        if has_trig:
            sanitized_trig = _require_non_blank(
                self.triggering_review_id, "triggering_review_id"
            )
            object.__setattr__(
                self, "triggering_review_id", sanitized_trig
            )
```

### 9.3 Serialização e Desserialização Versionada (`workflow_serialization.py`)

#### Constantes e Envelopes
- `SCHEMA_VERSION_V1 = 1`
- `SCHEMA_VERSION_V2 = 2`
- `EVENT_TYPE_WORKFLOW_CONCLUDED = "WORKFLOW_CONCLUDED"`

#### Envelope Serializado para Abertura Raiz (`schema_version = 1`)
```json
{
  "schema_version": 1,
  "event_id": "evt-open-001",
  "workflow_id": "wf-mat-001-01",
  "opened_at": "2026-08-24T09:00:00+00:00",
  "recommendation": {
    "material_id": "MAT-001",
    "decision": "REVIEW",
    "rationale": "...",
    "requires_human_decision": true,
    "evidence": [...]
  }
}
```

#### Envelope Serializado para Follow-up de Correção (`schema_version = 2`)
```json
{
  "schema_version": 2,
  "event_id": "evt-open-002",
  "workflow_id": "wf-mat-001-02",
  "opened_at": "2026-08-24T10:00:00+00:00",
  "predecessor_workflow_id": "wf-mat-001-01",
  "triggering_review_id": "rev-001",
  "recommendation": {
    "material_id": "MAT-001",
    "decision": "REVIEW",
    "rationale": "...",
    "requires_human_decision": true,
    "evidence": [...]
  }
}
```

#### Funções de Serialização
```python
def workflow_opened_to_record(event: WorkflowOpened) -> dict[str, object]:
    if not isinstance(event, WorkflowOpened):
        raise ValueError(
            f"Expected WorkflowOpened instance, got {type(event).__name__}"
        )

    evidence_list: list[dict[str, object]] = [
        {
            "material_id": item.material_id,
            "source": item.source.value,
            "issue_type": item.issue_type.value,
            "observation": item.observation,
            "severity": item.severity.value,
        }
        for item in event.recommendation.evidence
    ]

    rec_dict: dict[str, object] = {
        "material_id": event.recommendation.material_id,
        "decision": event.recommendation.decision.value,
        "rationale": event.recommendation.rationale,
        "requires_human_decision": event.recommendation.requires_human_decision,
        "evidence": evidence_list,
    }

    if event.predecessor_workflow_id is None:
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "event_id": event.event_id,
            "workflow_id": event.workflow_id,
            "opened_at": event.opened_at.isoformat(),
            "recommendation": rec_dict,
        }

    return {
        "schema_version": SCHEMA_VERSION_V2,
        "event_id": event.event_id,
        "workflow_id": event.workflow_id,
        "opened_at": event.opened_at.isoformat(),
        "predecessor_workflow_id": event.predecessor_workflow_id,
        "triggering_review_id": event.triggering_review_id,
        "recommendation": rec_dict,
    }


def workflow_opened_from_record(
    record: Mapping[str, object],
) -> WorkflowOpened:
    if not isinstance(record, Mapping):
        raise ValueError(
            f"Expected mapping record, got {type(record).__name__}"
        )

    if "schema_version" not in record:
        raise ValueError("Missing required field 'schema_version'")
    schema_version = record["schema_version"]
    if type(schema_version) is not int or isinstance(schema_version, bool):
        raise ValueError(
            f"schema_version must be an int, got {type(schema_version).__name__}"
        )

    if schema_version not in (SCHEMA_VERSION_V1, SCHEMA_VERSION_V2):
        raise ValueError(
            f"Unsupported schema_version: {schema_version}, expected {SCHEMA_VERSION_V1} or {SCHEMA_VERSION_V2}"
        )

    event_id = _require_str(record, "event_id")
    workflow_id = _require_str(record, "workflow_id")
    opened_at_str = _require_str(record, "opened_at")

    try:
        opened_at = datetime.fromisoformat(opened_at_str)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid ISO 8601 datetime: '{opened_at_str}'"
        ) from exc

    if opened_at.tzinfo is None or opened_at.utcoffset() is None:
        raise ValueError(f"opened_at must be timezone-aware: '{opened_at_str}'")

    if "recommendation" not in record:
        raise ValueError("Missing required field 'recommendation'")
    recommendation = _parse_recommendation(record["recommendation"])

    has_pred = "predecessor_workflow_id" in record
    has_trig = "triggering_review_id" in record

    if schema_version == SCHEMA_VERSION_V1:
        if has_pred or has_trig:
            raise ValueError(
                "Lineage fields are not permitted in schema_version 1"
            )
        return WorkflowOpened(
            event_id=event_id,
            workflow_id=workflow_id,
            recommendation=recommendation,
            opened_at=opened_at,
            predecessor_workflow_id=None,
            triggering_review_id=None,
        )

    # schema_version == SCHEMA_VERSION_V2
    if not has_pred or not has_trig:
        raise ValueError(
            "schema_version 2 requires both 'predecessor_workflow_id' and 'triggering_review_id'"
        )

    pred_val = record["predecessor_workflow_id"]
    trig_val = record["triggering_review_id"]

    if pred_val is None or trig_val is None:
        raise ValueError(
            "Explicit null values are not permitted for lineage fields in schema_version 2"
        )

    if type(pred_val) is not str or not pred_val.strip():
        raise ValueError(
            f"Field 'predecessor_workflow_id' must be a non-blank string, got {type(pred_val).__name__}"
        )
    if type(trig_val) is not str or not trig_val.strip():
        raise ValueError(
            f"Field 'triggering_review_id' must be a non-blank string, got {type(trig_val).__name__}"
        )

    predecessor_workflow_id = pred_val.strip()
    triggering_review_id = trig_val.strip()

    if predecessor_workflow_id == workflow_id.strip():
        raise ValueError(
            "predecessor_workflow_id must differ from workflow_id"
        )

    return WorkflowOpened(
        event_id=event_id,
        workflow_id=workflow_id,
        recommendation=recommendation,
        opened_at=opened_at,
        predecessor_workflow_id=predecessor_workflow_id,
        triggering_review_id=triggering_review_id,
    )
```

### 9.4 Projeção de Reidratação (`workflow_projection.py`)

```python
def rehydrate_pending_workflow(event: WorkflowOpened) -> GovernanceWorkflow:
    if not isinstance(event, WorkflowOpened):
        raise TypeError("event must be a WorkflowOpened instance")

    return GovernanceWorkflow(
        workflow_id=event.workflow_id,
        recommendation=event.recommendation,
        opened_at=event.opened_at,
        review=None,
        predecessor_workflow_id=event.predecessor_workflow_id,
        triggering_review_id=event.triggering_review_id,
    )


def rehydrate_workflow(
    events: Sequence[WorkflowLifecycleEvent],
) -> GovernanceWorkflow:
    if not events:
        raise ValueError("events sequence cannot be empty")

    for event in events:
        if not isinstance(event, (WorkflowOpened, WorkflowConcluded)):
            raise ValueError(
                f"Unsupported lifecycle event type: {type(event).__name__}"
            )

    if not isinstance(events[0], WorkflowOpened):
        raise ValueError("First event in workflow history must be WorkflowOpened")

    opened_events = [
        event for event in events if isinstance(event, WorkflowOpened)
    ]
    if len(opened_events) != 1:
        raise ValueError(
            f"Expected exactly one WorkflowOpened event, got {len(opened_events)}"
        )

    concluded_events = [
        event for event in events if isinstance(event, WorkflowConcluded)
    ]
    if len(concluded_events) > 1:
        raise ValueError(
            f"Expected at most one WorkflowConcluded event, got {len(concluded_events)}"
        )

    if len(events) not in (1, 2):
        raise ValueError(
            f"Unexpected number of events for workflow lifecycle: {len(events)}"
        )

    opened = events[0]

    if len(events) == 1:
        return rehydrate_pending_workflow(opened)

    concluded = events[1]
    if not isinstance(concluded, WorkflowConcluded):
        raise ValueError(
            "Second event in reviewed workflow history must be WorkflowConcluded"
        )

    if concluded.workflow_id != opened.workflow_id:
        raise ValueError(
            f"workflow_id mismatch between opened '{opened.workflow_id}' and concluded '{concluded.workflow_id}'"
        )

    return GovernanceWorkflow(
        workflow_id=opened.workflow_id,
        recommendation=opened.recommendation,
        opened_at=opened.opened_at,
        review=concluded.review,
        predecessor_workflow_id=opened.predecessor_workflow_id,
        triggering_review_id=opened.triggering_review_id,
    )
```

---

## 10. Estratégia de testes e TDD

A execução seguirá micro-TDD estrito em fatias ordenadas:

1. **Fatia 1 — Hardening de Domínio (`tests/test_workflow.py`):**
   - Teste RED para `GovernanceWorkflow` com pareamento atômico parcial (`predecessor_workflow_id` informado sem `triggering_review_id` e vice-versa);
   - Teste RED para `GovernanceWorkflow` com auto-referência (`predecessor_workflow_id == workflow_id`);
   - Implementação GREEN em `src/agent_lab/workflow.py`.
2. **Fatia 2 — Evento `WorkflowOpened` (`tests/test_workflow_events.py`):**
   - Testes RED para instanciação de `WorkflowOpened` com lineage válida;
   - Testes RED para instanciação de `WorkflowOpened` raiz (sem lineage);
   - Testes RED para rejeição de lineage parcial, auto-referência e identificadores em branco;
   - Implementação GREEN em `src/agent_lab/workflow_events.py`.
3. **Fatia 3 — Serialização e Desserialização (`tests/test_workflow_serialization.py`):**
   - Testes RED verificando que `workflow_opened_to_record` para abertura raiz emite `"schema_version": 1` e omite as chaves de lineage;
   - Testes RED verificando que `workflow_opened_to_record` para follow-up emite `"schema_version": 2` com ambas as chaves;
   - Testes RED de desserialização de payloads v1 legados (sem chaves);
   - Testes RED de rejeição de campos de lineage em registros com `schema_version == 1`;
   - Testes RED de rejeição em `schema_version == 2` para ausência parcial, total, `null` explícito e tipos inválidos;
   - Testes RED de rejeição para versões de schema desconhecidas (diferentes de 1 e 2);
   - Testes RED de round-trip completo com v1 e v2;
   - Implementação GREEN em `src/agent_lab/workflow_serialization.py`.
4. **Fatia 4 — Projeção (`tests/test_workflow_projection.py`):**
   - Testes RED para `rehydrate_pending_workflow` propagando lineage em `PENDING_HUMAN_REVIEW`;
   - Testes RED para `rehydrate_workflow` propagando lineage em `PENDING_HUMAN_REVIEW` (1 evento);
   - Testes RED para `rehydrate_workflow` propagando lineage em `REVIEWED` (2 eventos);
   - Implementação GREEN em `src/agent_lab/workflow_projection.py`.
5. **Fatia 5 — Integração Ponta a Ponta com Múltiplos Restarts (`tests/test_workflow_lineage_persistence_integration.py`):**
   - Criação de novo arquivo de integração testando o ciclo completo:
     1. Predecessor `WF-001` aberto e concluído com `REQUEST_CORRECTION`;
     2. Follow-up `WF-002` gerado via `open_correction_follow_up(...)`;
     3. Gravação de `WorkflowOpened` v2 de `WF-002` no repositório;
     4. **RESTART 1:** Novo repositório recupera `WF-002` e projeta em `PENDING_HUMAN_REVIEW` preservando `predecessor_workflow_id == "WF-001"` e `triggering_review_id == "rev-001"`;
     5. Conclusão de `WF-002` com `APPROVE` e gravação de `WorkflowConcluded` v1;
     6. **RESTART 2:** Novo repositório recupera `WF-002` e projeta em `REVIEWED` mantendo a mesma lineage;
     7. Verificação de que o predecessor `WF-001` permaneceu imutável e inalterado.
6. **Fatia 6 — Regressão Geral:**
   - Execução integral via `python -m unittest discover -s tests -v`.

---

## 11. Gates de qualidade

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

---

## 12. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Leitor legado aceitar follow-up v2 e ignorar lineage silenciosamente | Nula | Alto | Aberturas de follow-up usam `schema_version = 2`, fazendo com que leitores antigos falhem de forma explícita (*fail-closed*) por versão não suportada. |
| Lineage parcial gerando causalidade ambígua | Média | Médio | Validação estrita de pareamento atômico no domínio, evento e desserializador (fail-closed). |
| Inconsistência entre domínio em memória e persistência | Baixa | Alto | Hardening das mesmas invariantes em `GovernanceWorkflow` e em `WorkflowOpened`. |
| Acoplamento indevido entre projeção e predecessor | Baixa | Alto | A projeção preserva puramente os identificadores causais sem carregar o grafo do predecessor em tempo de projeção (`Repository != Projection`). |
| Confusão conceitual com `CORRECTION_APPLIED` | Baixa | Baixo | Reafirmação explícita na SPEC de que lineage causal registra apenas a procedência temporal do ciclo, sem semântica de aplicação automática de correções. |

---

## 13. Plano de reversão

1. **Reversão em nível de código:** Em caso de necessidade antes de gravações operacionais de registros v2, o commit pode ser revertido via `git revert`, restabelecendo o baseline anterior de 297 testes GREEN.
2. **Impacto semântico pós-persistência de registros v2:** Após a gravação de eventos `WorkflowOpened` em `schema_version = 2`, um downgrade para a versão anterior do código não é operacionalmente compatível: a versão anterior rejeitará os registros v2 com `ValueError: Unsupported schema_version: 2`. Essa falha explícita é deliberada e estritamente preferível à perda silenciosa de causalidade semântica. Um rollback pós-gravação de dados v2 requer:
   - Manutenção de um leitor compatível com `schema_version = 2`; ou
   - Execução de uma estratégia explícita de backup ou migração de dados.

---

## 14. Versionamento e release

- O presente incremento introduz `schema_version = 2` exclusivamente para registros de abertura com lineage (`WorkflowOpened`), mantendo `schema_version = 1` para aberturas raiz e para `WorkflowConcluded`.
- Em estrita aderência ao [PROJECT_COMPASS.md](../PROJECT_COMPASS.md):
  ```text
  Merge fecha um incremento; release fecha uma versão coerente.
  ```
- Nenhuma tag ou versão SemVer é declarada nesta SPEC. O fechamento e a numeração da próxima release serão decididos exclusivamente na consolidação formal de uma versão coerente.

---

## 15. Critérios de aceite

- [x] Hardening de `GovernanceWorkflow` rejeita instanciações com lineage parcial ou auto-referencial (`predecessor_workflow_id == workflow_id`);
- [x] `WorkflowOpened` suporta opcionalmente `predecessor_workflow_id` e `triggering_review_id` com sanitização e pareamento atômico estrito;
- [x] Abertura inicial raiz sem lineage continua serializando com `schema_version = 1` e sem as chaves de lineage (preservação da estrutura canônica dos root openings v1);
- [x] Correction follow-up é serializado com `schema_version = 2` e exige ambas as chaves de lineage;
- [x] Desserialização de registros v1 exige ausência de chaves de lineage (*fail-closed*);
- [x] Desserialização de registros v2 exige presença válida de ambas as chaves de lineage (*fail-closed*);
- [x] Desserialização rejeita qualquer versão diferente de `1` e `2` (*fail-closed*);
- [x] Correction follow-up persistido preserva `predecessor_workflow_id` e `triggering_review_id` após múltiplos restarts;
- [x] Successor reidratado em `PENDING_HUMAN_REVIEW` preserva lineage causal;
- [x] Successor concluído e reidratado em `REVIEWED` preserva lineage causal;
- [x] Round-trip preserva a estrutura canônica dos root openings v1 sem lineage e preserva exatamente os identificadores causais nos correction follow-ups v2;
- [x] Predecessor permanece imutável e inalterado;
- [x] Nenhuma semântica de `CORRECTION_APPLIED` é introduzida;
- [x] Suíte completa de testes aprovada e GREEN em Python 3.11 / `unittest`.

---

## 16. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| 2026-08-24 | Exigir pareamento atômico de lineage tanto no domínio (`GovernanceWorkflow`) quanto no evento (`WorkflowOpened`) | Evitar assimetria entre domínio e persistência e impedir causalidade parcial ambígua. | `Jk-Pascoal` |
| 2026-08-24 | Adotar `schema_version = 2` para aberturas com lineage e manter `schema_version = 1` para aberturas raiz | Garantir comportamento fail-closed onde leitores antigos rejeitam registros v2 por versão não suportada em vez de ignorar a lineage silenciosamente. | `Jk-Pascoal` |
| 2026-08-24 | Omitir chaves de lineage em aberturas raiz no serializador e rejeitar lineage em registros v1 | Preservar a estrutura serializada canônica v1 e eliminar representações não-canônicas (*fail-closed*). | `Jk-Pascoal` |
| 2026-08-24 | Isolar a projeção do successor sem navegação em profundidade no predecessor | Respeitar o princípio `Repository != Projection` e manter a reidratação pura, desacoplada e performática. | `Jk-Pascoal` |

---

## 17. Fechamento de Implementação e Evidências das Fatias

- **Status:** Implementação concluída, validada e integrada na branch `main` via PR #62 (merge commit `bfeaf7aeedb4835dd133af827bece9694cd4cf55`).
- **Issue:** #61 concluída.
- **Baseline integrado na main:** 320 testes GREEN em Python 3.11 / `unittest` (297 herdados da `main` + 23 novos testes do incremento).
- **Commits atômicos das fatias:**
  - `c82191d feat: harden workflow lineage invariants` (Fatia 1: Domínio)
  - `0d6a20e feat: add workflow opened lineage contract` (Fatia 2: Evento)
  - `c1a796f feat: persist workflow opened lineage with schema v2` (Fatia 3: Serialização)
  - `2cb3de0 feat: preserve workflow lineage during rehydration` (Fatia 4: Projeção)
  - `f5c12cd test: verify correction follow-up lineage across restarts` (Fatia 5: Integração)

### Resultados implementados e verificados

1. **`GovernanceWorkflow` (`src/agent_lab/workflow.py`):**
   - Pareamento atômico estrito: `predecessor_workflow_id` e `triggering_review_id` devem ser ambos `None` ou ambos strings não-vazias;
   - Sanitização de whitespace via `strip()`;
   - Rejeição de auto-referência (`predecessor_workflow_id != workflow_id`) com `ValueError`.
2. **`WorkflowOpened` (`src/agent_lab/workflow_events.py`):**
   - Campos de lineage opcionais (`predecessor_workflow_id: str | None = None`, `triggering_review_id: str | None = None`);
   - Mesmas validações defensivas de pareamento atômico, sanitização e anti-auto-referência.
3. **Serialização e Desserialização Versionada (`src/agent_lab/workflow_serialization.py`):**
   - Root `WorkflowOpened` serializa em `schema_version = 1` omitindo chaves de lineage e sem `event_type` (preservação da estrutura serializada canônica dos root openings v1);
   - Correction follow-up `WorkflowOpened` serializa em `schema_version = 2` com `"predecessor_workflow_id"` e `"triggering_review_id"`, sem `event_type`;
   - Leitura de registros v1 contendo qualquer chave de lineage (inclusive `None`) falha fechado com `ValueError`;
   - Leitura de registros v2 exige ambas as chaves de lineage preenchidas e válidas (*fail-closed*);
   - `workflow_opened_from_record` rejeita qualquer `schema_version` diferente de `1` e `2` com `ValueError`;
   - `WorkflowConcluded` permanece exclusivamente em `schema_version = 1`;
   - Compatibilidade de leitura com registros v1 legados mantida no dispatcher polimórfico.
4. **Projeção Determinística (`src/agent_lab/workflow_projection.py`):**
   - `rehydrate_pending_workflow` e `rehydrate_workflow` propagam fielmente `predecessor_workflow_id` e `triggering_review_id` para `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` e `REVIEWED`;
   - Princípio `Repository != Projection` estritamente preservado: nenhum predecessor é reconstruído em memória nem consultado no repositório durante a projeção.
5. **Teste Vertical de Aceitação (`tests/test_correction_follow_up_lineage_persistence_integration.py`):**
   - Predecessor `WF-001` concluído com `REQUEST_CORRECTION`;
   - Sucessor `WF-002` criado via `open_correction_follow_up` e persistido em `schema_version = 2`;
   - **Restart 1:** Nova instância do repositório reidrata `WF-002` em `PENDING_HUMAN_REVIEW` com lineage intacta;
   - Conclusão de `WF-002` com `APPROVE` via `conclude_governance_workflow` e persistência de `WorkflowConcluded`;
   - **Restart 2:** Nova instância do repositório reidrata `WF-002` em `REVIEWED` com a mesma lineage causal, `closed_at` e `review_lead_time` derivados;
   - Predecessor `WF-001` permanece imutável e inalterado ao longo de todo o processo.

### Limites e Não-Escopo Preservados

- Nenhuma semântica `CORRECTION_APPLIED` introduzida;
- Nenhuma mutação ou versionamento do cadastro de materiais;
- Nenhuma reconstrução de grafo de predecessores em memória;
- Nenhuma mudança para banco relacional, 2PC, locking multiprocesso, filas, SLA ou RBAC;
- Downgrade para leitor legado após a existência de registros v2 é operacionalmente incompatível e falha explicitamente (*fail-closed*), prevenindo perda silenciosa de lineage.

