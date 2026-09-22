# SPEC-0145 — Human Review Claim Release-Aware Read Path v1

> Especificação técnica da evolução do caminho de leitura de governança para interpretação factual
> integrada de assunções (`HumanReviewClaim`) e liberações voluntárias (`HumanReviewClaimRelease`)
> no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0145` |
| **Status** | `IMPLEMENTED` |
| **Issue relacionada** | `#145` |
| **Título da Issue** | `Human Review Claim Release-Aware Read Path v1` |
| **Branch documental** | `docs/issue-145-release-aware-read-path` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-22` |
| **Última atualização** | `2026-09-22` |
| **Data de integração** | `2026-09-22` |
| **Domínio** | Governança de materiais industriais PDM/BOM e Master Data |
| **Camada arquitetural** | Projeção, Policy e Camada de Aplicação (`Projection`, `Policy`, `Application Layer`) |
| **Baseline de entrada** | `1045 testes aprovados` (100% GREEN) |
| **Baseline final integrado** | `1102 testes aprovados` (100% GREEN) |
| **PR funcional** | `#147` |
| **Commit funcional** | `1c6058a944cf0c4803bb4097a1996b82290953ba` |
| **Merge funcional** | `6a24a20a315de25d3adfc6fe6e6fbe21e156d4b8` |
| **Impacto SemVer** | `MINOR — novas capacidades públicas aditivas e evolução controlada de boundary existente; release formal permanece v0.1.0` |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

O **Agent Lab Pascoal** consolidou em seu núcleo de governança temporal e assunção operacional Human-in-the-Loop uma rigorosa separação em trilhas append-only duráveis e desacopladas:
1. **Trilha de Lifecycle:** eventos de abertura e conclusão de workflow (`WorkflowOpened` v1/v2 e `WorkflowConcluded` v1) persistidos em JSONL via `JsonlWorkflowLifecycleRepository`, reidratados por `rehydrate_workflow` e com fila pendente projetada deterministicamente por `project_pending_human_review_queue` e consultada via `ListPendingHumanReviewsUseCase` (Issue #81);
2. **Trilha de Auditoria:** deliberações humanas registradas em `HumanReview` com `VerifiedSpecialistIdentity` e persistidas em `AuditEvent` via `JsonlAuditRepository` com verificação determinística de consistência cruzada via `verify_dual_write_consistency` (Issue #55);
3. **Trilha de Assunção de Revisão Humana (Claims):**
   - **Contrato de domínio em memória (Issue #85 / SPEC-0085):** entidade imutável `HumanReviewClaim` e operação pura `claim_pending_human_review(...)` em `src/agent_lab/human_review_claim.py`;
   - **Persistência durável desacoplada (Issue #88 / SPEC-0088):** protocolo `HumanReviewClaimRepository` e repositório append-only `JsonlHumanReviewClaimRepository` com `schema_version = 1`, garantindo durabilidade física (`flush` + `os.fsync`) e admitindo múltiplos claims para o mesmo `workflow_id`;
   - **Boundary de aplicação para gravação (Issue #91 / SPEC-0091):** classe `RecordHumanReviewClaimUseCase` em `src/agent_lab/human_review_claim_use_case.py`;
   - **Projeção factual canônica de claims (Issue #94 / SPEC-0094):** função pura `project_human_review_claim_state` e read-model imutável `HumanReviewClaimState` categorizando a cardinalidade bruta persistida em `NO_CLAIM`, `SINGLE_CLAIM` e `MULTIPLE_CLAIMS`;
   - **Composição de fila da Issue #97 (SPEC-0097):** read-model `PendingHumanReviewWithClaimStateItem` e caso de uso `ListPendingHumanReviewsWithClaimStateUseCase`;
   - **Política pura de elegibilidade (Issue #100 / SPEC-0100):** função pura `evaluate_reviewer_claim_eligibility` classificando a autoridade normativa em `ELIGIBLE`, `CLAIM_REQUIRED`, `CLAIMANT_MISMATCH` e `MULTIPLE_CLAIMS_CONFLICT` a partir de `HumanReviewClaimState` e equivalência textual de Stable Principal `(specialist_id, identity_provider, identity_subject)`;
   - **Runtime enforcement gate (Issue #103 / SPEC-0103):** classe `RecordHumanDecisionUseCase` aplicando a política como gate obrigatório pré-write em tempo de execução;
4. **Trilha de Liberação de Revisão Humana (Releases):**
   - **Contrato de domínio em memória (Issue #106 / SPEC-0106):** entidade imutável `HumanReviewClaimRelease` e operação pura `release_human_review_claim(...)` em `src/agent_lab/human_review_claim.py`, validando coerência relacional por Stable Principal e não-retroatividade temporal (`released_at >= claim.claimed_at`);
   - **Persistência durável de releases (Issue #109 / SPEC-0109):** protocolo `HumanReviewClaimReleaseRepository` e repositório append-only `JsonlHumanReviewClaimReleaseRepository` com `schema_version = 1`, unicidade estrita por `release_id` e permissão explícita de múltiplos releases para o mesmo `claim_id`;
   - **Boundary de aplicação para liberação (Issue #112 / SPEC-0112):** classe `ReleaseHumanReviewClaimUseCase` em `src/agent_lab/human_review_claim_release_use_case.py`.

Baseline de entrada verificado e auditado na branch `main`:
```text
Ran 1045 tests in 2.254s
OK
```

---

## 2. Problema Factual, Evidências e Impacto

### Problema Factual
Atualmente, existe uma **assimetria factual concreta no read-path operacional** do Agent Lab Pascoal:
* Os fatos de assunção (`HumanReviewClaim`) e os fatos de liberação voluntária (`HumanReviewClaimRelease`) são gravados e preservados de forma durável e independente em seus respectivos repositórios JSONL.
* Entretanto, os release facts persistidos **não participam do caminho de leitura operacional**:
  1. A aplicação não dispõe de uma consulta de fila pendente que exponha a composição de claims correlacionados com releases;
  2. O gate de elegibilidade em runtime de `RecordHumanDecisionUseCase` (`human_review_use_case.py`) consulta exclusivamente o repositório de claims através de `project_human_review_claim_state`, sem nenhuma observação do repositório de releases (`HumanReviewClaimReleaseRepository`).

### Evidências
1. Em `src/agent_lab/pending_human_reviews_with_claim_state_use_case.py`, a classe `ListPendingHumanReviewsWithClaimStateUseCase` injeta exclusivamente `WorkflowLifecycleRepository` e `HumanReviewClaimRepository`. Zero injeção de `HumanReviewClaimReleaseRepository`;
2. Em `src/agent_lab/human_review_use_case.py`, o método `RecordHumanDecisionUseCase.execute(...)` realiza na Fase 2 a leitura exclusiva de `self._claim_repository.list_by_workflow_id(workflow.workflow_id)` e repassa para `project_human_review_claim_state(workflow.workflow_id, claims)`, ignorando completamente releases existentes;
3. Cenário de falha operacional reproduzível:
   - Especialista 1 assume o workflow WF-01 gerando o claim CLM-01 via `RecordHumanReviewClaimUseCase`;
   - Especialista 1 desiste e libera formalmente o claim CLM-01 gerando o release REL-01 via `ReleaseHumanReviewClaimUseCase`;
   - Especialista 2 assume legitimamente o workflow WF-01 gerando o claim CLM-02 via `RecordHumanReviewClaimUseCase`;
   - O histórico contém 2 claims físicos (CLM-01 e CLM-02) e 1 release físico (REL-01 para CLM-01);
   - Especialista 2 submete sua decisão humana através de `RecordHumanDecisionUseCase`;
   - O caso de uso consulta apenas claims, projeta `MULTIPLE_CLAIMS` e bloqueia Especialista 2 levantando `ReviewerNotEligibleError(MULTIPLE_CLAIMS_CONFLICT)` com 0 writes.

### Impacto
* Bloqueio indevido de workflows operacionais legítimos: a devolução voluntária de um item não surte efeito prático no read-path;
* Inutilidade funcional do repositório de releases para o fluxo de decisão;
* Violação do princípio de que o sistema reflete os fatos persistidos.

### Restrição Ontológica e Lição de Governança
A solução para esse problema **não pode adulterar o significado do read-model `HumanReviewClaimState`** da Issue #94:
- Se um workflow possui 1 claim persistido e 1 release persistido, o read-model de claims não pode declarar falsamente que existem zero claims (`claims = ()`).
- 1 claim + 1 release **não significa que nunca houve claim**.
- `HumanReviewClaimState` representa estritamente todos os claims brutos persistidos; ele não é um DTO genérico e não deve ser fabricado a partir de subconjuntos de claims não-liberados.
- É mandatório que o novo caminho de leitura seja **explicitamente tipado e aditivo**, representando simultaneamente a história completa e a interpretação factual de claims sem release.

---

## 3. Objetivo

Implementar verticalmente o caminho de leitura ciente de releases (**Release-Aware Read Path v1**) no Agent Lab Pascoal, abrangendo:
1. Projeção factual pura em memória (`project_release_aware_claim_state`) e read-model imutável (`ReleaseAwareClaimState`) que represente separadamente:
   - `all_claims`: todos os claims factuais persistidos;
   - `releases`: todos os releases factuais persistidos;
   - `unreleased_claims`: claims que não possuem release correspondente.
2. Função pura de Policy aditiva (`evaluate_release_aware_reviewer_claim_eligibility`) operando sobre `ReleaseAwareClaimState`, preservando intactos a API pública, assinatura e comportamento normativo de `evaluate_reviewer_claim_eligibility` (Issue #100).
3. Composição aditiva de fila pendente na Camada de Aplicação (`ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase` e `PendingHumanReviewWithReleaseAwareClaimStateItem`), preservando 100% dos contratos da Issue #97.
4. Evolução do gate pré-write em `RecordHumanDecisionUseCase` para consultar claims e releases, avaliando a elegibilidade via policy release-aware sem transferir responsabilidades entre use cases.

---

## 4. Arquitetura e Responsabilidades por Camada

A arquitetura respeita rigorosamente a constituição do Agent Lab Pascoal:

```text
Repository preserva.
Projection interpreta.
Policy governa.
Application coordena e aplica.
```

### Diagrama Arquitetural de Fluxo

```text
1. REPOSITÓRIOS FÍSICOS (Append-Only)
JsonlHumanReviewClaimRepository            JsonlHumanReviewClaimReleaseRepository
            │                                                 │
            │ list_all() ou list_by_workflow_id()             │ list_all() ou list_by_workflow_id()
            ▼                                                 ▼
        claims: Sequence[HumanReviewClaim]                releases: Sequence[HumanReviewClaimRelease]
            │                                                 │
            └───────────────────────┬─────────────────────────┘
                                    │
2. PROJEÇÃO PURA (Zero-I/O, Memória) │
                                    ▼
                     project_release_aware_claim_state(...)
                                    │
                                    ▼
3. READ-MODEL FACTUAL               │
                          ReleaseAwareClaimState
                          ├── all_claims: tuple[HumanReviewClaim, ...]
                          ├── releases: tuple[HumanReviewClaimRelease, ...]
                          ├── unreleased_claims: tuple[HumanReviewClaim, ...]
                          ├── unreleased_claim_count: int
                          ├── unreleased_claim_state: HumanReviewClaimFactState
                          └── sole_unreleased_claim: HumanReviewClaim | None
                                    │
            ┌───────────────────────┴───────────────────────┐
            │                                               │
4. APLICAÇÃO: CONSULTA DE FILA             4. POLICY & RUNTIME GATE
            │                                               │
            ▼                                               ▼
ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase    evaluate_release_aware_reviewer_claim_eligibility(...)
            │                                               │
            ▼                                               ▼
PendingHumanReviewWithReleaseAwareClaimStateItem            ReviewerEligibilityDecision
                                                            (ELIGIBLE / CLAIM_REQUIRED / ...)
                                                                    │
                                                                    ▼
                                                            RecordHumanDecisionUseCase (Gate Pré-Write)
                                                            ├─ se ELIGIBLE → autoriza dual-write
                                                            └─ se diferente → ReviewerNotEligibleError (0 writes)
```

---

## 5. Contratos Públicos Novos e Preservados

### 5.1 Contratos Preservados (100% Intactos)
* **`HumanReviewClaimState` e `project_human_review_claim_state` (Issue #94):** Assinatura, propriedades e semântica histórica permanecem inalteradas.
* **`PendingHumanReviewWithClaimStateItem` e `ListPendingHumanReviewsWithClaimStateUseCase` (Issue #97):** Assinatura, injeções e semântica histórica permanecem inalteradas.
* **`ReviewerEligibilityStatus`, `ReviewerEligibilityDecision` e API pública de `evaluate_reviewer_claim_eligibility` (Issue #100):** Permanecem inalteradas. A implementação interna da policy histórica pode sofrer apenas refatoração mínima para compartilhamento de helper privado puro com a nova policy release-aware.

### 5.2 Novos Contratos Públicos

#### A. Read-Model `ReleaseAwareClaimState` (`src/agent_lab/human_review_claim_projection.py`)
```python
@dataclass(frozen=True, slots=True)
class ReleaseAwareClaimState:
    workflow_id: str
    all_claims: tuple[HumanReviewClaim, ...]
    releases: tuple[HumanReviewClaimRelease, ...]
    unreleased_claims: tuple[HumanReviewClaim, ...]

    @property
    def all_claims_count(self) -> int: ...

    @property
    def releases_count(self) -> int: ...

    @property
    def unreleased_claim_count(self) -> int: ...

    @property
    def unreleased_claim_state(self) -> HumanReviewClaimFactState: ...

    @property
    def sole_unreleased_claim(self) -> HumanReviewClaim | None: ...

    @property
    def has_unreleased_claims(self) -> bool: ...

    @property
    def has_no_unreleased_claims(self) -> bool: ...

    @property
    def has_multiple_unreleased_claims(self) -> bool: ...
```

**Regras do Read-Model:**
* Proibido incluir método `to_claim_state()` que construa `HumanReviewClaimState` falso;
* Proibido usar termos de "Active Claim", "ownership" ou "winner";
* As propriedades `all_claims_count`, `releases_count`, `unreleased_claim_count`, `unreleased_claim_state` e `sole_unreleased_claim` são computadas puras (`@property`) sem armazenamento redundante.

#### B. Função Pura `project_release_aware_claim_state` (`src/agent_lab/human_review_claim_projection.py`)
```python
def project_release_aware_claim_state(
    workflow_id: str,
    claims: Sequence[HumanReviewClaim],
    releases: Sequence[HumanReviewClaimRelease],
) -> ReleaseAwareClaimState:
```

#### C. Função Pura de Policy `evaluate_release_aware_reviewer_claim_eligibility` (`src/agent_lab/reviewer_eligibility_policy.py`)
```python
def evaluate_release_aware_reviewer_claim_eligibility(
    release_aware_state: ReleaseAwareClaimState,
    reviewer_identity: VerifiedSpecialistIdentity,
) -> ReviewerEligibilityDecision:
```

#### D. Read-Model e Caso de Uso de Composição de Fila (`src/agent_lab/pending_human_reviews_with_claim_state_use_case.py`)
```python
@dataclass(frozen=True, slots=True)
class PendingHumanReviewWithReleaseAwareClaimStateItem:
    workflow: GovernanceWorkflow
    claim_state: ReleaseAwareClaimState

class ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase:
    def __init__(
        self,
        *,
        workflow_lifecycle_repository: WorkflowLifecycleRepository,
        claim_repository: HumanReviewClaimRepository,
        claim_release_repository: HumanReviewClaimReleaseRepository,
    ) -> None: ...

    def execute(self) -> tuple[PendingHumanReviewWithReleaseAwareClaimStateItem, ...]: ...
```

#### E. Evolução de `RecordHumanDecisionUseCase` (`src/agent_lab/human_review_use_case.py`)
O construtor passa a receber obrigatoriamente `claim_release_repository: HumanReviewClaimReleaseRepository`.
Na Fase 2, consulta `claims` e `releases` do workflow e aciona `project_release_aware_claim_state(...)` seguido de `evaluate_release_aware_reviewer_claim_eligibility(...)`.

---

## 6. Invariantes Constitucionais e Ontológicas

1. **A Verdade Histórica é Imutável:**
   - Nenhum claim é apagado, sobrescrito ou filtrado da história.
   - `all_claims` contém a totalidade dos fatos de claim registrados para o workflow.
   - `releases` contém a totalidade dos fatos de release registrados para o workflow.
   - `unreleased_claims` é uma projeção factual interpretada: representa os claims de `all_claims` cujo `claim_id` não possui correspondência causal em `releases`.
2. **Cardinalidade Explícita e Não Ambiguidade:**
   - `unreleased_claim_state` reutiliza `HumanReviewClaimFactState` (`NO_CLAIM`, `SINGLE_CLAIM`, `MULTIPLE_CLAIMS`) aplicando-o explicitamente sobre a tupla `unreleased_claims`.
   - Se `unreleased_claim_count == 0` $\rightarrow$ `unreleased_claim_state = NO_CLAIM`.
   - Se `unreleased_claim_count == 1` $\rightarrow$ `unreleased_claim_state = SINGLE_CLAIM`.
   - Se `unreleased_claim_count >= 2` $\rightarrow$ `unreleased_claim_state = MULTIPLE_CLAIMS`.
3. **Imutabilidade e Pureza em Memória:**
   - Todos os read-models são congelados (`frozen=True, slots=True`).
   - As funções de projeção e policy são 100% puras (zero I/O, determinísticas, sem efeitos colaterais).
4. **Gate Pré-Write Inviolável:**
   - Qualquer status diferente de `ReviewerEligibilityStatus.ELIGIBLE` interrompe o caso de uso com `ReviewerNotEligibleError`, garantindo **zero writes** no repositório de auditoria e no de ciclo de vida.
5. **Separação de Responsabilidades entre Use Cases:**
   - `RecordHumanReviewClaimUseCase` registra assunções de claims.
   - `ReleaseHumanReviewClaimUseCase` registra liberações de claims.
   - `RecordHumanDecisionUseCase` registra deliberações humanas após aplicar o gate de elegibilidade.
   - `RecordHumanDecisionUseCase` não cria, não assume e não altera claims.

---

## 7. Validações Fail-Closed e Integridade Relacional

A função `project_release_aware_claim_state` aplica validações defensivas nominais estritas antes e durante o processamento:

1. **Validação Nominal de Entradas:**
   - `workflow_id`: deve ser `str` não-booleano e não-vazio após `.strip()` $\rightarrow$ `TypeError` ou `ValueError`;
   - `claims`: deve ser `Sequence` e não pode ser sequência textual/binária (`str`, `bytes`, `bytearray`) $\rightarrow$ `TypeError`;
   - `releases`: deve ser `Sequence` e não pode ser sequência textual/binária $\rightarrow$ `TypeError`;
   - Exaustividade antecipada: **todos** os elementos em `claims` devem ser instâncias de `HumanReviewClaim` $\rightarrow$ `TypeError`;
   - Exaustividade antecipada: **todos** os elementos em `releases` devem ser instâncias de `HumanReviewClaimRelease` $\rightarrow$ `TypeError`.
2. **Filtragem por Workflow:**
   - Elementos em `claims` e `releases` com `workflow_id` diferente do alvo são descartados da projeção daquele workflow sem erro (permitindo consumo de coleções globais/snapshots).
3. **Detecção Fail-Closed de Releases Órfãos do Workflow:**
   - Para cada release filtrado para o workflow: se `release.claim_id` não existir em nenhum claim de `all_claims` daquele workflow $\rightarrow$ levanta imediatamente `ValueError(f"Orphan release '{release.release_id}' references unknown claim_id '{release.claim_id}' for workflow '{sanitized_wf}'")`.
4. **Detecção Fail-Closed de Anomalia Cronológica:**
   - Se `release.released_at < claim.claimed_at` $\rightarrow$ levanta imediatamente `ValueError(f"Release '{release.release_id}' released_at ({release.released_at}) cannot be before claim claimed_at ({claim.claimed_at})")`.
5. **Ordenação Canônica Determinística:**
   - `all_claims` é ordenado deterministicamente por `(claimed_at ASC, claim_id ASC)`;
   - `releases` é ordenado deterministicamente por `(released_at ASC, release_id ASC)`;
   - `unreleased_claims` preserva a ordem canônica `(claimed_at ASC, claim_id ASC)`.

---

## 8. Comportamento de Múltiplos Releases por `claim_id`

Conforme consolidado na SPEC-0109 (`docs/specs/0109_human_review_claim_release_persistence_v1.md`):
* O repositório impõe unicidade estrita por `release_id`;
* No entanto, múltiplos fatos de release distintos (`release_id`s diferentes) podem referenciar fisicamente o mesmo `claim_id` no log append-only.

**Tratamento na Projeção Release-Aware:**
* A existência de $\ge 1$ release válido associado causalmente a um claim confirma deterministicamente a liberação daquele claim;
* A projeção opera de forma **idempotente**: múltiplos releases para o mesmo `claim_id` não causam anomalia e todos permanecem registrados em `releases`;
* O claim correspondente é excluído de `unreleased_claims`.

---

## 9. Integração da Camada de Policy Release-Aware

A função pura `evaluate_release_aware_reviewer_claim_eligibility` aplica as regras normativas sobre `ReleaseAwareClaimState`:

```text
Entrada: ReleaseAwareClaimState + VerifiedSpecialistIdentity
   │
   ├─ Se unreleased_claim_state is NO_CLAIM:
   │     └─ ReviewerEligibilityDecision(CLAIM_REQUIRED)
   │
   ├─ Se unreleased_claim_state is MULTIPLE_CLAIMS:
   │     └─ ReviewerEligibilityDecision(MULTIPLE_CLAIMS_CONFLICT)
   │
   └─ Se unreleased_claim_state is SINGLE_CLAIM:
         │
         ├─ Obtém claimant = sole_unreleased_claim.specialist
         ├─ Avalia equivalência estrita de Stable Principal:
         │    (specialist_id, identity_provider, identity_subject)
         │
         ├─ Se estável coincide:
         │     └─ ReviewerEligibilityDecision(ELIGIBLE)
         └─ Se diverge:
               └─ ReviewerEligibilityDecision(CLAIMANT_MISMATCH)
```

**Propriedades Fundamentais:**
* Reutilização da lógica de comparação via helper privado puro compartilhado entre `evaluate_reviewer_claim_eligibility` e `evaluate_release_aware_reviewer_claim_eligibility`;
* Zero duplicação de regras normativas;
* Os mesmos 4 estados normativos consolidados na Issue #100 são estritamente preservados;
* Não introduz Active Claim Policy, ownership, vencedor ou desempate temporal.

---

## 10. Composição Aditiva da Pending Queue na Camada de Aplicação

O novo caso de uso `ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase` realiza a composição unificada da fila:

1. **Injeção de Dependências:**
   - `workflow_lifecycle_repository: WorkflowLifecycleRepository`
   - `claim_repository: HumanReviewClaimRepository`
   - `claim_release_repository: HumanReviewClaimReleaseRepository`
2. **Snapshot Único Local (Zero N+1):**
   ```python
   events_snapshot = self._workflow_lifecycle_repository.list_all_events()
   pending_workflows = project_pending_human_review_queue(events_snapshot)
   claims_snapshot = self._claim_repository.list_all()
   releases_snapshot = self._claim_release_repository.list_all()
   ```
3. **Mapeamento e Retorno:**
   ```python
   return tuple(
       PendingHumanReviewWithReleaseAwareClaimStateItem(
           workflow=workflow,
           claim_state=project_release_aware_claim_state(
               workflow.workflow_id,
               claims_snapshot,
               releases_snapshot,
           ),
       )
       for workflow in pending_workflows
   )
   ```
4. **Preservação:** O caso de uso legado `ListPendingHumanReviewsWithClaimStateUseCase` e seu item `PendingHumanReviewWithClaimStateItem` continuam existindo e funcionando sem qualquer alteração.

---

## 11. Evolução do Gate Pré-Write em `RecordHumanDecisionUseCase`

O caso de uso `RecordHumanDecisionUseCase` é atualizado na Fase 2:

```python
# Fase 2 — Gate de Elegibilidade em Runtime Release-Aware
claims = self._claim_repository.list_by_workflow_id(workflow.workflow_id)
releases = self._claim_release_repository.list_by_workflow_id(workflow.workflow_id)

release_aware_state = project_release_aware_claim_state(
    workflow.workflow_id,
    claims,
    releases,
)

eligibility = evaluate_release_aware_reviewer_claim_eligibility(
    release_aware_state,
    reviewer_identity,
)

if not eligibility.is_eligible:
    raise ReviewerNotEligibleError(eligibility)
```

* Se elegível, prossegue para a Fase 3 (dual-write sequencial `Audit -> Lifecycle`);
* Se inelegível, interrompe imediatamente com `ReviewerNotEligibleError` (zero writes);
* Falhas de I/O nos repositórios propagam de forma fail-closed sem mascaramento.

---

## 12. Cenário Vertical Canônico Ponta a Ponta

O teste de integração vertical deve comprovar com repositórios reais JSONL pós-restart o ciclo completo:

```text
1. Workflow WF-01 aberto em PENDING_HUMAN_REVIEW
2. Especialista A assume WF-01 via RecordHumanReviewClaimUseCase (Claim CLM-01 persistido)
3. Especialista A desiste e libera WF-01 via ReleaseHumanReviewClaimUseCase (Release REL-01 persistido)
4. Especialista B assume WF-01 via RecordHumanReviewClaimUseCase (Claim CLM-02 persistido)
5. Reinicialização de processo (novas instâncias dos repositórios sobre os mesmos JSONLs)
6. ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase projeta:
   - all_claims = (CLM-01, CLM-02)
   - releases = (REL-01,)
   - unreleased_claims = (CLM-02,)
   - unreleased_claim_state = SINGLE_CLAIM
   - sole_unreleased_claim = CLM-02
7. Especialista B submete deliberação humana APPROVE via RecordHumanDecisionUseCase:
   - Gate pré-write consulta claims e releases;
   - evaluate_release_aware_reviewer_claim_eligibility reconhece B como ELIGIBLE;
   - Deliberação gravada com sucesso em Audit e Lifecycle (WorkflowConcluded);
8. Tentativa de deliberação por Especialista C ou repetição rejeitada fail-closed.
```

---

## 13. Estratégia de Testes e Micro-TDD

O desenvolvimento será conduzido estritamente em micro-TDD em fatias isoladas:

### Fatia 1 — Read-Model e Projeção Release-Aware (`tests/test_human_review_claim_projection.py`)
- Testes para `ReleaseAwareClaimState`: imutabilidade, contagens derivadas, `unreleased_claim_state`, `sole_unreleased_claim`, propriedades booleanas;
- Testes para `project_release_aware_claim_state`:
  * Workflow sem claims e sem releases $\rightarrow$ `all_claims=()`, `releases=()`, `unreleased_claims=()`, `NO_CLAIM`;
  * Workflow com 1 claim e 0 releases $\rightarrow$ `unreleased_claims=(C1,)`, `SINGLE_CLAIM`;
  * Workflow com 1 claim e 1 release $\rightarrow$ `all_claims=(C1,)`, `releases=(R1,)`, `unreleased_claims=()`, `NO_CLAIM`;
  * Workflow com 2 claims e 1 release $\rightarrow$ `all_claims=(C1, C2)`, `releases=(R1,)`, `unreleased_claims=(C2,)`, `SINGLE_CLAIM`;
  * Workflow com 2 claims e 2 releases $\rightarrow$ `unreleased_claims=()`, `NO_CLAIM`;
  * Workflow com 2 claims e 0 releases $\rightarrow$ `unreleased_claims=(C1, C2)`, `MULTIPLE_CLAIMS`;
  * Múltiplos releases válidos para o mesmo `claim_id` $\rightarrow$ confirmação idempotente de liberação;
  * Isolamento de workflows: claims e releases de outros workflows filtrados corretamente;
  * Ordenação canônica determinística independente da ordem de entrada física.

### Fatia 2 — Validações Defensivas e Fail-Closed (`tests/test_human_review_claim_projection.py`)
- Tipos inválidos para `workflow_id`, `claims` e `releases` $\rightarrow$ `TypeError`;
- Strings vazias ou whitespace para `workflow_id` $\rightarrow$ `ValueError`;
- Elementos não-`HumanReviewClaim` em `claims` $\rightarrow$ `TypeError`;
- Elementos não-`HumanReviewClaimRelease` em `releases` $\rightarrow$ `TypeError`;
- Release órfão para o workflow (`claim_id` inexistente naquele workflow) $\rightarrow$ `ValueError`;
- Anomalia cronológica (`release.released_at < claim.claimed_at`) $\rightarrow$ `ValueError`.

### Fatia 3 — Policy Release-Aware (`tests/test_reviewer_eligibility_policy.py`)
- Testes unitários para `evaluate_release_aware_reviewer_claim_eligibility`:
  * `unreleased_claim_state == NO_CLAIM` $\rightarrow$ `CLAIM_REQUIRED`;
  * `unreleased_claim_state == MULTIPLE_CLAIMS` $\rightarrow$ `MULTIPLE_CLAIMS_CONFLICT`;
  * `unreleased_claim_state == SINGLE_CLAIM` com Stable Principal coincidente $\rightarrow$ `ELIGIBLE`;
  * `unreleased_claim_state == SINGLE_CLAIM` com Stable Principal divergente $\rightarrow$ `CLAIMANT_MISMATCH`;
  * Preservação de equivalência com metadados de autenticação renovados (`verification_id`, `verified_at`).
- Regressão exaustiva: 100% dos testes existentes de `evaluate_reviewer_claim_eligibility` continuam aprovados sem alteração.

### Fatia 4 — Composição de Fila Release-Aware (`tests/test_pending_human_reviews_with_claim_state_use_case.py`)
- Testes unitários para `PendingHumanReviewWithReleaseAwareClaimStateItem`;
- Testes unitários para `ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase`;
- Validação de snapshot local único por repositório (zero N+1);
- Teste de integração vertical com persistência real JSONL pós-restart.

### Fatia 5 — Gate de Runtime e Interoperabilidade Vertical (`tests/test_human_review_use_case.py` e `tests/test_human_review_use_case_integration.py`)
- Injeção obrigatória de `HumanReviewClaimReleaseRepository` em `RecordHumanDecisionUseCase`;
- Validação de bloqueio quando `unreleased_claim_state` for `NO_CLAIM` ou `MULTIPLE_CLAIMS` (0 writes);
- Teste vertical do ciclo canônico completo com 3 use cases coordenados (`RecordClaim` $\rightarrow$ `ReleaseClaim` $\rightarrow$ `RecordClaim` $\rightarrow$ `RecordDecision`) sobre arquivos JSONL reais pós-restart;
- Regressão completa de todos os testes existentes.

---

## 14. Critérios de Aceitação

1. `project_release_aware_claim_state` recebe `workflow_id`, `claims` e `releases`, retornando `ReleaseAwareClaimState` contendo separadamente `all_claims`, `releases` e `unreleased_claims`.
2. Se todos os claims de um workflow possuírem release correspondente, `unreleased_claims` é vazia, `unreleased_claim_count == 0` e `unreleased_claim_state` é `HumanReviewClaimFactState.NO_CLAIM` (`has_no_unreleased_claims = True`, `sole_unreleased_claim = None`), preservando todos os fatos em `all_claims` e `releases`.
3. Se um workflow com múltiplos claims tiver todos exceto um liberados, `unreleased_claim_state` é `SINGLE_CLAIM` e `sole_unreleased_claim` expõe com exatidão o claim remanescente.
4. Rejeição fail-closed com `TypeError` para qualquer elemento em `claims` que não seja `HumanReviewClaim` ou em `releases` que não seja `HumanReviewClaimRelease`.
5. Rejeição fail-closed com `ValueError` para release órfão pertencente ao workflow (`release.claim_id` ausente em `all_claims`) ou anomalia cronológica (`released_at < claimed_at`).
6. `evaluate_release_aware_reviewer_claim_eligibility` avalia a elegibilidade sobre `ReleaseAwareClaimState` respeitando estritamente a política de stable principal e os 4 status normativos, sem fabricar instâncias de `HumanReviewClaimState`.
7. `ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase` compõe `PendingHumanReviewWithReleaseAwareClaimStateItem` injetando os três repositórios, com snapshot global único e zero N+1.
8. `RecordHumanDecisionUseCase` injeta `HumanReviewClaimReleaseRepository`, consulta releases do workflow na Fase 2 e avalia elegibilidade via `evaluate_release_aware_reviewer_claim_eligibility`, comprovando o cenário vertical canônico ponta a ponta sem conflito com claims previamente liberados.
9. `evaluate_reviewer_claim_eligibility` preserva sua API pública, assinatura e comportamento normativo idênticos, com 100% dos testes legados da Issue #100 aprovados.
10. Contratos, projeções e casos de uso das Issues #94 e #97 permanecem 100% inalterados e com testes aprovados.
11. Todos os testes unitários e de integração novos e existentes executam com 100% GREEN no runner canônico `python -m unittest discover -s tests -v`.
12. Documentação do `PROJECT_COMPASS.md` alinhada refletindo a nova capacidade de interpretação release-aware.

---

## 15. Não Objetivos (Fora de Escopo)

* Não alterar a definição ou o comportamento do read-model `HumanReviewClaimState` da Issue #94;
* Não alterar a assinatura ou comportamento de `PendingHumanReviewWithClaimStateItem` e `ListPendingHumanReviewsWithClaimStateUseCase` da Issue #97;
* Não introduzir conceito ou abstração de "Active Claim" normativa;
* Não introduzir semânticas de titularidade (*ownership*), exclusividade ou atribuição gerencial (*assignment*);
* Não introduzir eleição de vencedor (*winner*) ou regras de desempate (*First-Claim-Wins* / *Last-Claim-Wins*);
* Não introduzir travas (*locking / checkout*), expiração temporal (*TTL / lease / expiry*) ou SLAs operacionais;
* Não introduzir revogação compulsória (*force-release*) ou reatribuição (*reassignment*);
* Não transferir a responsabilidade de assunção de claims para `RecordHumanDecisionUseCase`;
* Não implementar concorrência multiprocesso ou distribuída;
* Não alterar a esteira de Ground Truth / Benchmark ou a frente de Ingestão CSV nesta Issue.

---

## 16. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **Adulterar semântica histórica de `HumanReviewClaimState`** | Baixa | Crítico | Mitigado pela criação do read-model aditivo `ReleaseAwareClaimState`, mantendo o original intacto. |
| **Falsificar tipos na camada de Policy** | Baixa | Alto | Mitigado pela criação de `evaluate_release_aware_reviewer_claim_eligibility` consumindo o novo read-model nominal, sem fabricar `HumanReviewClaimState` a partir de `unreleased_claims`. |
| **Quebrar consultas de fila existentes da Issue #97** | Baixa | Alto | Mitigado pela introdução aditiva de `ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase`, preservando a API da #97 inalterada. |
| **Escorregar para conceito genérico de "Active Claim"** | Média | Alto | Restringir estritamente o read-model à subtração factual de pares correlacionados causalmente por `claim_id`. |
| **Silenciar releases órfãos ou inconsistências de dados** | Baixa | Alto | Validação fail-closed estrita com `ValueError` na projeção para qualquer release sem claim correspondente no workflow. |
| **Degradação de performance por N+1 queries** | Baixa | Médio | Exigência de snapshots únicos globais em `ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase`. |

---

## 17. Definition of Done (DoD)

- [x] SPEC técnica correspondente criada em `docs/specs/` e aprovada em PR documental prévio (`SPEC-0145` via PR #146).
- [x] Implementação conduzida via micro-TDD com testes unitários, defensivos e de integração vertical pós-restart.
- [x] Suíte de testes 100% GREEN via `python -m unittest discover -s tests -v` com baseline incrementado (1102/1102 GREEN).
- [x] PR funcional revisado e integrado na `main` (PR #147, commit funcional `1c6058a`, merge `6a24a20`).
- [ ] PR documental de closeout atualizando o `PROJECT_COMPASS.md` e marcando a SPEC como `IMPLEMENTED`.
- [ ] Higienização completa das branches de trabalho.
