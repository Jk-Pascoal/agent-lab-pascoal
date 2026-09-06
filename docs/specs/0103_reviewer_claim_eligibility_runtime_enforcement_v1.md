# SPEC 0103 — Reviewer Claim Eligibility Runtime Enforcement v1

> Especificação técnica do enforcement operacional e autorização pré-write em tempo de execução
> da política de elegibilidade de revisores (`Reviewer Claim Eligibility Policy`)
> no caso de uso de decisão humana (`RecordHumanDecisionUseCase`) do Agent Lab Pascoal.

---

## 1. Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0103` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#103` |
| **Título da Issue** | `Reviewer Claim Eligibility Runtime Enforcement v1` |
| **Branch funcional** | `feature/issue-103-reviewer-claim-eligibility-runtime-enforcement` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-06` |
| **Data do ambiente** | `2026-09-06` |
| **Última atualização** | `2026-09-06` |
| **Baseline de entrada** | `569 testes aprovados` |
| **Runner oficial** | `unittest` / Python 3.11 |

---

## 2. Contexto Arquitetural

O **Agent Lab Pascoal** consolidou progressivamente o ecossistema de assunção voluntária e deliberação humana através de incrementos rigorosamente desacoplados e orientados a responsabilidade única:

1. **Issue #74 (Human Review Application Use Case v1):** introduziu `RecordHumanDecisionUseCase` e `RecordHumanDecisionResult` em `src/agent_lab/human_review_use_case.py`, estabelecendo a coordenação em duas fases (preparação de domínio com zero I/O $\rightarrow$ persistência sequencial `Audit → Lifecycle`);
2. **Issue #85 (Human Review Claim Domain Contract v1):** formalizou o contrato puro em memória `HumanReviewClaim` e `claim_pending_human_review(...)` em `src/agent_lab/human_review_claim.py`, estabelecendo que `HumanReviewClaim ≠ HumanReview` e `CLAIMED ≠ REVIEWED`;
3. **Issue #88 (Human Review Claim Persistence v1):** introduziu o protocolo `HumanReviewClaimRepository` e a implementação append-only durável `JsonlHumanReviewClaimRepository` com `schema_version = 1`, permitindo múltiplos claims para o mesmo `workflow_id`;
4. **Issue #91 (Record Human Review Claim Application Use Case v1):** introduziu o boundary de gravação `RecordHumanReviewClaimUseCase` em `src/agent_lab/human_review_claim_use_case.py`;
5. **Issue #94 (Human Review Claim State Projection v1):** introduziu a projeção pura em memória `project_human_review_claim_state` e o read-model `HumanReviewClaimState` em `src/agent_lab/human_review_claim_projection.py`, categorizando factual e deterministicamente o histórico em `NO_CLAIM`, `SINGLE_CLAIM` e `MULTIPLE_CLAIMS`;
6. **Issue #97 (Pending Human Review Queue with Claim State Application Use Case v1):** introduziu `ListPendingHumanReviewsWithClaimStateUseCase` em `src/agent_lab/pending_human_reviews_with_claim_state_use_case.py`, compondo de forma somente-leitura e com snapshot local único por repositório os workflows pendentes com o estado factual de claims;
7. **Issue #100 (Reviewer Claim Eligibility Policy v1):** introduziu o enum canônico `ReviewerEligibilityStatus`, o read-model `ReviewerEligibilityDecision` e a política normativa pura em memória `evaluate_reviewer_claim_eligibility` em `src/agent_lab/reviewer_eligibility_policy.py`.

### Direção Canônica de Responsabilidades

O fluxo arquitetural estabelecido pelo projeto segue a hierarquia linear e unidirecional:

```text
Repository preserva (fatos físicos brutos na ordem de append)
    ↓
Projection interpreta (read-model factual: HumanReviewClaimState)
    ↓
Policy governa (autoridade normativa pura em memória: ReviewerEligibilityDecision)
    ↓
Application coordena e aplica (gate de autorização pré-write e orquestração de persistência)
```

---

## 3. Problema

No estado atual integrado na `main`, a política de elegibilidade normativa pura formalizada na Issue #100 ainda **não é aplicada em tempo de execução** na camada de aplicação.

O caso de uso `RecordHumanDecisionUseCase.execute(...)` recebe `reviewer_identity` e orquestra a conclusão do workflow sem consultar a trilha de claims:

1. Se o workflow possui `NO_CLAIM` $\rightarrow$ a Policy classificaria como `CLAIM_REQUIRED`, mas a Application atualmente aceita e persiste a deliberação sem qualquer claim prévio;
2. Se o workflow possui `SINGLE_CLAIM` registrado para o Especialista A e o Especialista B submete deliberação $\rightarrow$ a Policy classificaria como `CLAIMANT_MISMATCH`, mas a Application atualmente aceita e conclui o workflow em nome de B;
3. Se o workflow possui `MULTIPLE_CLAIMS` (disputa concorrente ou assunções repetidas não resolvidas) $\rightarrow$ a Policy classificaria como `MULTIPLE_CLAIMS_CONFLICT`, mas a Application atualmente aceita a deliberação de qualquer revisor.

Existe, portanto, uma lacuna explícita entre a **governança normativa** e o **enforcement operacional em tempo de execução** na camada de aplicação. Sem esse gate, a compulsoriedade da política de claims não é garantida nas transições de escrita do sistema.

---

## 4. Objetivo

Integrar a **Reviewer Claim Eligibility Policy** ao `RecordHumanDecisionUseCase` como **gate obrigatório de autorização pré-write**, reutilizando exclusivamente os contratos canônicos já existentes no sistema:

```text
HumanReviewClaimRepository
    ↓ list_by_workflow_id(workflow.workflow_id)
project_human_review_claim_state(workflow.workflow_id, claims)
    ↓
HumanReviewClaimState
evaluate_reviewer_claim_eligibility(claim_state, reviewer_identity)
    ↓
ReviewerEligibilityDecision
    ↓
RecordHumanDecisionUseCase (Gate de Enforcement: autoriza se ELIGIBLE, bloqueia com exceção se inelegível)
```

A Camada de Aplicação deve permitir a persistência da deliberação humana em `AuditRepository` e `WorkflowLifecycleRepository` **somente quando** `eligibility.status == ReviewerEligibilityStatus.ELIGIBLE`. Em qualquer outro caso, a operação deve falhar imediatamente de forma *fail-closed*, com **zero escritas** físicas efetuadas.

---

## 5. Decisões Arquiteturais e de Design

### 5.1 Injeção Obrigatória de Dependência

`RecordHumanDecisionUseCase` passa a receber `claim_repository: HumanReviewClaimRepository` como dependência obrigatória no construtor (`__init__`):

```python
class RecordHumanDecisionUseCase:
    def __init__(
        self,
        *,
        audit_repository: AuditRepository,
        workflow_lifecycle_repository: WorkflowLifecycleRepository,
        claim_repository: HumanReviewClaimRepository,
    ) -> None:
        self._audit_repository = audit_repository
        self._workflow_lifecycle_repository = workflow_lifecycle_repository
        self._claim_repository = claim_repository
```

**Diretrizes de Integridade e Delimitação:**
- O parâmetro `claim_repository` é mandatório por assinatura/injeção explícita;
- É terminantemente proibido o suporte a `None`, valores padrão, fallbacks permissivos, flags de bypass ou modos de compatibilidade legados sem claims;
- Todos os chamadores e testes de `RecordHumanDecisionUseCase` devem fornecer uma instância de `HumanReviewClaimRepository`;
- **Não introduzir validação runtime adicional:** não introduzir nesta fatia validações com `isinstance(...)`, coerções, adaptações automáticas ou verificações runtime adicionais sobre os repositórios injetados no construtor;
- **Preservação de contratos existentes:** não alterar os contratos ou protocolos de `AuditRepository` ou `WorkflowLifecycleRepository`;
- **Não criar camadas intermediárias:** não criar factories, wrappers, decorators ou adapters para gerenciar a injeção;
- A nova dependência permanece estritamente como um contrato tipado explícito da Application Layer.

### 5.2 Reuso Integral de Projeção e Política (Zero Duplicação)

Em estrita obediência ao princípio:
```text
Repository preserva → Projection interpreta → Policy governa → Application coordena e aplica
```
A camada de aplicação **NÃO deve duplicar nenhuma lógica**:
- Não contar ou filtrar claims manualmente;
- Não comparar identidades ou tuplas de principal estável diretamente;
- Não recalcular estados `NO_CLAIM`, `SINGLE_CLAIM` ou `MULTIPLE_CLAIMS`;
- Não eleger claim ativo, vencedor, titular ou prioritário;
- Não criar regras de desempate (*Last-Claim-Wins* / *First-Claim-Wins*).

A Application coordena estritamente a composição:
```python
claims = self._claim_repository.list_by_workflow_id(workflow.workflow_id)
claim_state = project_human_review_claim_state(workflow.workflow_id, claims)
eligibility = evaluate_reviewer_claim_eligibility(claim_state, reviewer_identity)
```

**Regra Estrita de Consulta de Claims:**
`list_by_workflow_id(workflow.workflow_id)` deve ser chamado exatamente uma vez em toda execução que concluir com sucesso a Fase 1 de preparação e validação determinística. Execuções rejeitadas durante a Fase 1 devem realizar zero consultas ao `HumanReviewClaimRepository`.

Preserva-se rigorosamente:
```text
domain failure → 0 claim reads → 0 writes
valid Phase 1  → exatamente 1 claim read → Projection → Policy → gate
```

### 5.3 Sequência Canônica de Execução em Quatro Fases

Para preservar o princípio da SPEC 0074 de que nenhuma falha determinística de domínio deve ocorrer após o início do I/O, e garantir que nenhum write físico ocorra antes da autorização de elegibilidade, a sequência de coordenação em `execute(...)` é estruturada nas seguintes fases determinísticas:

```text
[Chamador / Interface]
      │
      │ execute(workflow, review_id, audit_event_id, lifecycle_event_id, ...)
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: PREPARAÇÃO E VALIDAÇÃO DETERMINÍSTICA EM MEMÓRIA (Zero I/O)        │
│                                                                             │
│ 1. Validação estrutural de entrada:                                         │
│    - isinstance(workflow, GovernanceWorkflow) -> TypeError                  │
│                                                                             │
│ 2. Construção e validação do parecer humano e evento de auditoria:          │
│    - result = record_human_review(...)                                      │
│    - Violações de justificativa, correções, temporalidade falham aqui.      │
│                                                                             │
│ 3. Transição de estado em memória do workflow:                              │
│    - concluded_workflow = conclude_governance_workflow(workflow, review)    │
│    - Se o workflow já estiver revisado, levanta ValueError.                 │
│                                                                             │
│ 4. Construção e validação do evento de lifecycle em memória:                │
│    - lifecycle_event = WorkflowConcluded(...)                               │
│    - Se event_id for inválido/em branco, levanta ValueError.                │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      │ (Todos os artefatos em memória válidos com sucesso — ZERO I/O ocorrido)
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: GATE DE ELEGIBILIDADE PRÉ-WRITE (Read-Only I/O + Policy Pura)       │
│                                                                             │
│ 5. Consulta de claims para o workflow específico:                           │
│    - claims = self._claim_repository.list_by_workflow_id(                   │
│          workflow.workflow_id                                               │
│      )                                                                      │
│    - [PONTO DE FALHA]: Corrupção ou I/O no repositório propaga fail-closed; │
│      zero writes em Audit ou Lifecycle.                                     │
│                                                                             │
│ 6. Projeção factual do estado de claims:                                    │
│    - claim_state = project_human_review_claim_state(                        │
│          workflow.workflow_id, claims                                       │
│      )                                                                      │
│                                                                             │
│ 7. Avaliação normativa pura da política de elegibilidade:                   │
│    - eligibility = evaluate_reviewer_claim_eligibility(                      │
│          claim_state, reviewer_identity                                     │
│      )                                                                      │
│                                                                             │
│ 8. Verificação do Gate de Autorização:                                      │
│    - Se NOT eligibility.is_eligible (status != ELIGIBLE):                   │
│      raise ReviewerNotEligibleError(eligibility)                            │
│    - ZERO writes em Audit e ZERO writes em Lifecycle.                       │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      │ (Revisor validado como ELIGIBLE)
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: PERSISTÊNCIA COORDENADA (Writes I/O Sequenciais)                    │
│                                                                             │
│ 9. Persistência de Auditoria:                                               │
│    - self._audit_repository.append(human_review_result.audit_event)          │
│    - Se falhar, propaga exceção e Lifecycle NÃO é chamado.                  │
│                                                                             │
│ 10. Persistência de Lifecycle:                                              │
│     - self._workflow_lifecycle_repository.append_concluded(lifecycle_event) │
│     - Se falhar, propaga exceção; AuditEvent já gravado (dual-write         │
│       não-atômico mantido conforme SPEC 0074).                              │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 4: RETORNO CONSOLIDADO                                                 │
│                                                                             │
│ 11. Retorno dos artefatos:                                                  │
│     - RecordHumanDecisionResult(concluded_workflow, review, audit, lifecycle)│
└─────────────────────────────────────────────────────────────────────────────┘
```

**Justificativa da Posição do Gate:**
1. A Fase 1 (validação do domínio) ocorre estritamente antes do Gate de Leitura de Claims, garantindo que parâmetros de domínio inválidos (ex.: justificativa ausente em `REJECT`, workflow já revisado) continuem falhando com `ValueError` antes mesmo de consultar o `HumanReviewClaimRepository`;
2. O Gate de Leitura e Elegibilidade (Fase 2) ocorre estritamente antes de qualquer persistência física (Fase 3), garantindo que nenhuma linha seja escrita em `AuditRepository` ou `WorkflowLifecycleRepository` se o revisor for inelegível.

### 5.4 Exceção Dedicada de Aplicação: `ReviewerNotEligibleError`

Para sinalizar a rejeição por inelegibilidade normativa com precisão diagnóstica, cria-se a exceção dedicada no módulo `src/agent_lab/human_review_use_case.py`:

```python
class ReviewerNotEligibleError(Exception):
    """Raised when a reviewer attempts to record a human decision but is not eligible."""

    def __init__(self, decision: ReviewerEligibilityDecision) -> None:
        self.decision = decision
        super().__init__(
            f"Reviewer is not eligible to record decision: {decision.status.value} - {decision.reason}"
        )
```

**Diretrizes da Exceção:**
- Preserva a instância integral de `decision: ReviewerEligibilityDecision` como atributo público, permitindo inspeção programática do status (`decision.status`) e motivo (`decision.reason`) por camadas superiores (UI, API, testes);
- Mensagem textual clara contendo o nome do status e a justificativa normativa oficial provida pela Policy;
- Não mascarar exceções do repositório (`HumanReviewClaimPersistenceError`, `HumanReviewClaimCorruptionError`), da projeção ou da policy;
- Não converter inelegibilidade em `ValueError` indistinguível de erros de domínio.

### 5.5 Estrutura de Retorno: `RecordHumanDecisionResult` Inalterada

A estrutura de retorno `RecordHumanDecisionResult` permanece rigorosamente inalterada:

```python
@dataclass(frozen=True, slots=True)
class RecordHumanDecisionResult:
    workflow: GovernanceWorkflow
    review: HumanReview
    audit_event: AuditEvent
    lifecycle_event: WorkflowConcluded
```

**Justificativa:**
- Um retorno com sucesso do `RecordHumanDecisionUseCase` implica, por definição estrita do gate, que o revisor foi avaliado como `ELIGIBLE`;
- Incluir `eligibility: ReviewerEligibilityDecision` no resultado de sucesso seria redundante e violaria o princípio de evitar estado armazenado desnecessário;
- Mantém compatibilidade plena com os contratos existentes de retorno.

### 5.6 Preservação do Dual-Write Não-Atômico

A persistência física entre `AuditRepository` e `WorkflowLifecycleRepository` permanece:
- Sequencial (`Audit → Lifecycle`);
- Não-atômica;
- Sem transação distribuída, sem 2PC, sem rollbacks em disco e sem retries automáticos.

Se a escrita em `AuditRepository` for bem-sucedida, mas a escrita subsequente em `WorkflowLifecycleRepository` falhar:
- A exceção física propaga imediatamente;
- O evento de auditoria permanece imutável no log;
- A discrepância resultante continua diagnosticável pós-restart de forma estritamente somente-leitura pelo verificador cruzado `verify_repositories_consistency` em `src/agent_lab/consistency.py`, exatamente conforme especificado na SPEC 0074.

---

## 6. Escopo Detalhado

### 6.1 No Escopo (In-Scope)

1. **Alteração em `src/agent_lab/human_review_use_case.py`:**
   - Injeção obrigatória de `claim_repository: HumanReviewClaimRepository` no construtor de `RecordHumanDecisionUseCase`;
   - Introdução da classe de exceção `ReviewerNotEligibleError`;
   - Execução da consulta `self._claim_repository.list_by_workflow_id(workflow.workflow_id)` exatamente uma vez em toda execução que concluir com sucesso a Fase 1;
   - Avaliação da elegibilidade via `project_human_review_claim_state` e `evaluate_reviewer_claim_eligibility`;
   - Bloqueio imediato (*fail-closed*) com `ReviewerNotEligibleError` para os status `CLAIM_REQUIRED`, `CLAIMANT_MISMATCH` e `MULTIPLE_CLAIMS_CONFLICT`, com zero writes em Audit e Lifecycle;
   - Prosseguimento da persistência (`Audit → Lifecycle`) exclusivamente quando `status == ReviewerEligibilityStatus.ELIGIBLE`;
   - Exportação de `ReviewerNotEligibleError` no módulo;
2. **Atualização e Expansão dos Testes Unitários (`tests/test_human_review_use_case.py`):**
   - Atualização dos testes existentes para fornecer um mock/fake de `claim_repository` configurado para o cenário esperado;
   - Composição real obrigatória: `project_human_review_claim_state` e `evaluate_reviewer_claim_eligibility` **não** devem ser mockadas nos testes;
   - Teste: `SINGLE_CLAIM` com mesmo principal estável $\rightarrow$ `ELIGIBLE` $\rightarrow$ decisão persistida com sucesso;
   - Teste: `NO_CLAIM` $\rightarrow$ `CLAIM_REQUIRED` $\rightarrow$ levanta `ReviewerNotEligibleError` com `decision.status == CLAIM_REQUIRED`; zero chamadas a `audit_repo.append` e `lifecycle_repo.append_concluded`;
   - Teste: `SINGLE_CLAIM` com principal estável divergente $\rightarrow$ `CLAIMANT_MISMATCH` $\rightarrow$ levanta `ReviewerNotEligibleError` com `decision.status == CLAIMANT_MISMATCH`; zero writes;
   - Teste: `MULTIPLE_CLAIMS` de especialistas distintos $\rightarrow$ `MULTIPLE_CLAIMS_CONFLICT` $\rightarrow$ levanta `ReviewerNotEligibleError`; zero writes;
   - Teste: `MULTIPLE_CLAIMS` do mesmo principal estável $\rightarrow$ `MULTIPLE_CLAIMS_CONFLICT` $\rightarrow$ levanta `ReviewerNotEligibleError`; zero writes;
   - Teste: `SINGLE_CLAIM` com mesmo principal estável porém `verification_id` / `verified_at` distintos $\rightarrow$ `ELIGIBLE` $\rightarrow$ decisão persistida com sucesso;
   - Teste: violação determinística prévia de domínio (ex.: justificativa ausente em `REJECT`, workflow já revisado) $\rightarrow$ falha antes de qualquer chamada a `claim_repository.list_by_workflow_id` e antes de qualquer I/O;
   - Teste: erro ou corrupção no `HumanReviewClaimRepository` $\rightarrow$ exceção propaga de forma *fail-closed*; zero writes em Audit e Lifecycle;
   - Teste: preservação estrita da ordem `audit_repo.append` seguido de `lifecycle_repo.append_concluded` no caminho `ELIGIBLE`;
   - Teste: falha em `audit_repo.append` impede chamada a `lifecycle_repo.append_concluded`;
   - Teste: falha em `lifecycle_repo.append_concluded` ocorre após sucesso em `audit_repo.append` (dual-write não-atômico mantido);
3. **Atualização e Expansão dos Testes de Integração (`tests/test_human_review_use_case_integration.py`):**
   - Atualização dos testes de integração existentes para instanciar e injetar `JsonlHumanReviewClaimRepository` real;
   - Teste de integração vertical de ciclo completo:
     1. Abertura e persistência de `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` no repositório de lifecycle real;
     2. Registro e persistência de `HumanReviewClaim` via `RecordHumanReviewClaimUseCase` sobre arquivo JSONL de claims real;
     3. Reinicialização de processo simulada (novas instâncias dos repositórios sobre os mesmos arquivos);
     4. Execução de `RecordHumanDecisionUseCase.execute(...)` com especialista correspondente;
     5. Comprovação da persistência física nas três trilhas (Claim, Audit, Lifecycle);
     6. Verificação de consistência cruzada via `verify_repositories_consistency` retornando relatório consistente (`is_consistent = True`);
     7. Reidratação do workflow concluído via `rehydrate_workflow` retornando status `REVIEWED`;
   - Teste de integração comprovando que tentativa de conclusão sem claim sobre arquivos reais é bloqueada com `ReviewerNotEligibleError`, com os seguintes estados precisos:
     - `AuditRepository` continua sem novo `AuditEvent`;
     - `WorkflowLifecycleRepository` continua contendo somente o `WorkflowOpened` preexistente;
     - Nenhum `WorkflowConcluded` é persistido;
     - `HumanReviewClaimRepository` permanece sem claims;
     - `ReviewerNotEligibleError.decision.status == ReviewerEligibilityStatus.CLAIM_REQUIRED`.

### 6.2 Explicitamente Fora de Escopo

- Projeção ou política de claim ativo (`Active Claim Projection` / `Active Claim Policy`);
- *Owner*, *assignment*, *winner* ou atribuição gerencial de tarefas;
- Políticas de *First-Claim-Wins* ou *Last-Claim-Wins*;
- *Locking*, *checkout*, *lease*, *mutex*, *TTL*, expiração temporal ou *SLAs*;
- Operações de ciclo de vida de claim (*unclaim*, *release*, *transfer*, revogação);
- Alteração em `WorkflowStatus` ou introdução de estado `WorkflowStatus.CLAIMED`;
- Mutação ou consumo do claim após a revisão;
- Inclusão de `claim_id` em `AuditEvent` ou `WorkflowConcluded` nesta fatia;
- Reconciliação automática ou resolução autônoma de `MULTIPLE_CLAIMS`;
- Alterações em `evaluate_reviewer_claim_eligibility` (Issue #100) ou `project_human_review_claim_state` (Issue #94);
- Automação da decisão humana final (a soberania substantiva do especialista é integralmente preservada);
- Interfaces visuais (UI Streamlit, `app.py`), APIs REST, endpoints HTTP ou CLI;
- Processamento assíncrono ou concorrência multiprocesso (pressão P-07).

---

## 7. Invariantes Constitucionais

1. **`HumanReviewClaim ≠ HumanReview`:** Assumir voluntariamente um workflow pendente não é deliberar;
2. **`CLAIMED ≠ REVIEWED`:** O registro de um claim não conclui o workflow e não altera seu status de ciclo de vida;
3. **`sole_claim ≠ active claim ≠ owner ≠ winner ≠ assignment`:** A cardinalidade unitária atesta apenas a existência factual de um único registro no histórico;
4. **`Repository != Projection`:** O repositório preserva a ordem física dos fatos; a projeção interpreta o estado factual em memória;
5. **`Projection factual != Policy normativa`:** Fatos persistidos não se confundem com regras de autoridade;
6. **`Policy governa; Application coordena e aplica`:** A Policy determina a elegibilidade normativa pura em memória; a Application orquestra o gate pré-write sem reinventar regras de negócio;
7. **Identidade verificada, isoladamente, não concede autoridade de deliberação:** É indispensável satisfazer a política de claims para obter elegibilidade de revisão no workflow;
8. **Nenhum write de deliberação ocorre sem elegibilidade comprovada:** Qualquer status diferente de `ReviewerEligibilityStatus.ELIGIBLE` bloqueia imediatamente as escritas em `AuditRepository` e `WorkflowLifecycleRepository`;
9. **`RecordHumanDecisionResult` não armazena estado redundante:** A estrutura reflete exclusivamente os artefatos de governança produzidos;
10. **A soberania humana substantiva permanece absoluta:** O sistema governa a elegibilidade do revisor, mas a decisão final (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`) é exclusivamente humana.

---

## 8. Estratégia de Implementação (Micro-TDD Planejado)

A implementação seguirá ciclos estritos de micro-TDD em fatias atômicas orientadas a evidências:

```text
Fatia 1: Exceção Dedicada e Injeção Obrigatória de Dependência
  -> Criar ReviewerNotEligibleError em src/agent_lab/human_review_use_case.py
  -> Atualizar construtor de RecordHumanDecisionUseCase para exigir claim_repository
  -> Atualizar setUp dos testes unitários existentes para fornecer mock de claim_repository
  -> Validar que os testes existentes continuam passando com mock configurado para retornar claim coincidente

Fatia 2: Gate de Elegibilidade no Fluxo Feliz (SINGLE_CLAIM + Mesmo Principal)
  -> Usar instâncias reais de HumanReviewClaim e VerifiedSpecialistIdentity
  -> Não mockar project_human_review_claim_state nem evaluate_reviewer_claim_eligibility
  -> Teste unitário comprovando que SINGLE_CLAIM com mesmo principal resulta em ELIGIBLE
  -> Persistência sequencial (Audit -> Lifecycle) executada com sucesso
  -> Retorno de RecordHumanDecisionResult validado

Fatia 3: Bloqueio Fail-Closed para NO_CLAIM (CLAIM_REQUIRED)
  -> Mock de claim_repository retornando tupla vazia ()
  -> Projeção e Policy reais avaliando o estado factual
  -> Teste unitário comprovando que ausência de claims levanta ReviewerNotEligibleError
  -> Verificar que decision.status == CLAIM_REQUIRED
  -> Verificar ZERO chamadas a audit_repo.append e lifecycle_repo.append_concluded

Fatia 4: Bloqueio Fail-Closed para Divergência de Principal (CLAIMANT_MISMATCH)
  -> Mock de claim_repository retornando claim real de outro especialista
  -> Teste unitário levantando ReviewerNotEligibleError
  -> Verificar que decision.status == CLAIMANT_MISMATCH
  -> Verificar ZERO writes em ambos os repositórios

Fatia 5: Bloqueio Fail-Closed para Multiplicidade de Claims (MULTIPLE_CLAIMS_CONFLICT)
  -> Mock retornando múltiplos claims reais de especialistas diferentes levantando ReviewerNotEligibleError
  -> Mock retornando múltiplos claims reais do mesmo especialista levantando ReviewerNotEligibleError
  -> Verificar ZERO writes em ambos os repositórios

Fatia 6: Equivalência de Principal com Sessões Distintas
  -> Mock retornando claim real do mesmo principal estável mas com verification_id/verified_at distintos
  -> Comprovação de que é ELIGIBLE e a persistência ocorre normalmente

Fatia 7: Precedência de Validação de Domínio e Falhas de Persistência
  -> Teste comprovando que erro de domínio (ex: justificativa ausente em REJECT) falha na Fase 1
     com zero chamadas a claim_repository.list_by_workflow_id e zero writes
  -> Teste comprovando que falha em claim_repository.list_by_workflow_id propaga sem writes
  -> Teste confirmando que a ordem Audit -> Lifecycle e o comportamento de falha parcial permanecem idênticos

Fatia 8: Integração Vertical com Repositórios Reais JSONL e Reidratação Pós-Restart
  -> Atualizar tests/test_human_review_use_case_integration.py com JsonlHumanReviewClaimRepository real
  -> Teste ponta a ponta com persistência em disco, reinicialização e verificação de consistência
  -> Teste negativo: tentativa de conclusão sem claim em arquivo JSONL real bloqueia com ReviewerNotEligibleError,
     Audit permanece sem novo evento e Lifecycle permanece contendo apenas o WorkflowOpened preexistente

Regressão Canônica Completa:
  -> python -m unittest discover -s tests -v (569 + novos testes GREEN)
```

---

## 9. Critérios de Aceite

- [ ] SPEC 0103 aprovada antes de qualquer alteração no código de produção;
- [ ] Baseline de 569 testes preservado 100% GREEN antes e durante a evolução;
- [ ] `HumanReviewClaimRepository` injetado como dependência obrigatória no construtor de `RecordHumanDecisionUseCase`;
- [ ] Construtor e método `execute` rejeitam qualquer modo permissivo ou fallback sem claims;
- [ ] Reuso estrito de `project_human_review_claim_state` da Issue #94 sem recálculo de cardinalidade na Application;
- [ ] Reuso estrito de `evaluate_reviewer_claim_eligibility` da Issue #100 sem reaprendizado da regra de principal estável na Application;
- [ ] `project_human_review_claim_state` e `evaluate_reviewer_claim_eligibility` nunca são mockadas na suíte de testes;
- [ ] `ReviewerNotEligibleError` implementada preservando o read-model `decision: ReviewerEligibilityDecision`;
- [ ] `NO_CLAIM` resulta em `ReviewerNotEligibleError` com status `CLAIM_REQUIRED` e zero escritas em Audit e Lifecycle;
- [ ] `SINGLE_CLAIM` com claimant divergente resulta em `ReviewerNotEligibleError` com status `CLAIMANT_MISMATCH` e zero escritas;
- [ ] `MULTIPLE_CLAIMS` resulta em `ReviewerNotEligibleError` com status `MULTIPLE_CLAIMS_CONFLICT` e zero escritas (inclusive para o mesmo principal);
- [ ] `SINGLE_CLAIM` com mesmo principal estável autoriza a escrita e preserva o comportamento anterior do caminho feliz;
- [ ] Equivalência de principal estável suporta sessões distintas (`verification_id` e `verified_at` diferentes);
- [ ] Validações determinísticas da Fase 1 (domínio) continuam falhando antes de qualquer leitura no repositório de claims (`0 claim reads → 0 writes`);
- [ ] Falhas físicas ou de corrupção no repositório de claims propagam de forma *fail-closed* antes de qualquer escrita;
- [ ] Ordem estrita de dual-write `Audit → Lifecycle` preservada no caminho autorizado;
- [ ] Dual-write não-atômico preservado e documentado sem transações distribuídas ou compensações artificiais;
- [ ] Teste de integração vertical validando pipeline completo com persistência real em JSONL, restart e verificação de consistência cruzada;
- [ ] Teste de integração negativo comprovando que tentativa sem claim preserva o lifecycle com apenas `WorkflowOpened` preexistente e audit intocado;
- [ ] `RecordHumanDecisionResult` preservado inalterado;
- [ ] Suíte completa GREEN no comando canônico `python -m unittest discover -s tests -v`;
- [ ] `git diff --check` limpo, sem erros de whitespace.

---

## 10. Definition of Done (DoD)

- [ ] SPEC 0103 redigida e commitada em branch dedicada `feature/issue-103-reviewer-claim-eligibility-runtime-enforcement`;
- [ ] Branch criada a partir da `main` sincronizada com `origin/main`;
- [ ] Implementação conduzida estritamente via micro-TDD com commits atômicos rastreáveis;
- [ ] Suíte completa de testes GREEN: `python -m unittest discover -s tests -v`;
- [ ] `git diff --check` limpo;
- [ ] Pre-PR Gate e Evidence Reconciliation executados;
- [ ] Pull Request funcional aberto referenciando `Refs #103`;
- [ ] CI aprovada no Pull Request funcional;
- [ ] PR funcional mergeado na `main`;
- [ ] Issue #103 mantida aberta após merge funcional;
- [ ] Closeout documental realizado em branch/PR documental dedicado, atualizando `docs/PROJECT_COMPASS.md`;
- [ ] PR de closeout documental referencia `Closes #103`;
- [ ] Issue #103 formalmente encerrada após merge do closeout documental.

---

## 11. Riscos e Mitigações

| Risco | Severidade | Mitigação Arquitetural |
|---|---|---|
| **Duplicação de regras de Policy na Application** | Crítica | A Application delega 100% da avaliação a `evaluate_reviewer_claim_eligibility`, inspecionando unicamente `decision.is_eligible`. |
| **Escritas parciais em caso de inelegibilidade** | Crítica | O gate de elegibilidade é posicionado estritamente antes de `audit_repository.append(...)`, garantindo zero writes se inelegível. |
| **Achatamento de erro normativo em ValueError genérico** | Alta | Criação da exceção dedicada `ReviewerNotEligibleError` preservando o objeto estruturado `decision`. |
| **Quebra dos testes existentes por dependência nova** | Alta | Todos os testes de `RecordHumanDecisionUseCase` serão adaptados com fakes/mocks explícitos de `claim_repository`. |
| **Tentativa de introduzir modo legado sem claims** | Média | Proibição explícita na SPEC de parâmetros opcionais ou valores `None` para `claim_repository`. |
| **Leituras redundantes N+1 de claims** | Média | Execução de exatamente uma consulta pontual `list_by_workflow_id(workflow.workflow_id)` em execuções válidas na Fase 1. |

---

## 12. Arquivos Envolvidos

* **Documentação:**
  * `docs/specs/0103_reviewer_claim_eligibility_runtime_enforcement_v1.md`
* **Código de Produção:**
  * `src/agent_lab/human_review_use_case.py`
* **Código de Testes:**
  * `tests/test_human_review_use_case.py`
  * `tests/test_human_review_use_case_integration.py`
