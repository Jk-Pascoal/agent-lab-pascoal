# SPEC 0074 — Human Review Application Use Case v1

> Especificação técnica do primeiro boundary de aplicação do Agent Lab Pascoal,
> responsável por coordenar a deliberação humana sobre um workflow de governança pendente.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0074` |
| Status | `DRAFT / Proposta para revisão humana` |
| Issue relacionada | `#74` |
| Branch funcional | `feature/issue-74-human-review-application-use-case` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-28` |
| Última atualização | `2026-08-28` |
| Baseline de entrada | `412 testes aprovados` |
| Runner oficial | `unittest` / Python 3.11 |

---

## 1. Contexto

O **Agent Lab Pascoal** consolidou em seu núcleo normativo contratos estritos de domínio e persistência append-only em disco:

- Contratos de decisão humana e auditoria imutável ([`HumanReview`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/human_review.py#L98), [`AuditEvent`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/audit.py#L54), [`record_human_review`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/audit.py#L121));
- Contrato temporal e imutável de workflow ([`GovernanceWorkflow`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow.py#L33), [`conclude_governance_workflow`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow.py#L133));
- Eventos e repositórios de ciclo de vida e auditoria ([`WorkflowOpened`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow_events.py#L26), [`WorkflowConcluded`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow_events.py#L80), [`AuditRepository`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/audit_repository.py#L31), [`JsonlAuditRepository`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/audit_repository.py#L43), [`WorkflowLifecycleRepository`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow_repository.py#L48), [`JsonlWorkflowLifecycleRepository`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow_repository.py#L67));
- Verificação determinística e somente-leitura de consistência cruzada ([`verify_dual_write_consistency`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/consistency.py#L190), [`verify_repositories_consistency`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/consistency.py#L321)).

A auditoria arquitetural sobre as pressões **P-06 (Orchestration / Application Layer)** e **P-07 (Industrial Load / Scale Validation)** confirmou que o sistema possui um gap na **orquestração transversal**. Atualmente, para registrar a revisão humana sobre um workflow, o chamador precisa conhecer manualmente e de forma fragmentada a ordem de execução de múltiplos módulos.

Sem uma camada de aplicação explícita, qualquer interface futura (como uma PoC Streamlit em `app.py` ou uma API) seria forçada a atuar como um **"orquestrador acidental"**, assumindo responsabilidades de coordenação e conhecimento de repositórios internos.

---

## 2. Separação Canônica de Camadas e Princípios

Esta SPEC segue rigorosamente o princípio arquitetural:

```text
Application coordena.
Domain decide.
Repository preserva.
Projection interpreta.
```

### Invariantes e Separações Conceituais

1. **`System recommendation ≠ Human authority`:** A deliberação humana soberana é capturada por `HumanReview`; a recomendação do sistema permanece inalterada em `DecisionRecommendation`;
2. **`Evidence ≠ Decision`:** Fatos observados não se confundem com a deliberação do especialista;
3. **`CorrectionRequest ≠ MaterialRevision`:** Prescrição normativa humana difere do fato cadastral;
4. **`WorkflowLifecycleEvent ≠ AuditEvent`:** O ciclo operacional e a auditoria imutável permanecem desacoplados;
5. **`Repository ≠ Projection`:** Repositórios preservam a ordem física dos fatos persistidos; projeções interpretam a estrutura e topologia em memória;
6. **Invariantes pertencem exclusivamente ao Domínio:** A camada Application não duplica, não altera e não afrouxa regras de negócio (ex: justificativa obrigatória para reprovação/correção, validação de timezone, bloqueio de dupla conclusão). A autoridade sobre a transição de estado de um workflow pertence unicamente a `conclude_governance_workflow`;
7. **Proibição de God Service:** Não criar classes genéricas agregadoras como `ApplicationService`. O caso de uso deve ser coeso, autocontido e focado estritamente na operação `RecordHumanDecision`.

---

## 3. Problema e Objetivos

### Problema

A coordenação entre validação de revisão humana, transição de estado de workflow, persistência de auditoria e persistência de conclusão de ciclo de vida existe atualmente apenas dispersa em scripts de teste de integração ([`tests/test_workflow_conclusion_persistence_integration.py`](file:///C:/Users/Administrador/agent-lab-pascoal/tests/test_workflow_conclusion_persistence_integration.py), [`tests/test_workflow_integration.py`](file:///C:/Users/Administrador/agent-lab-pascoal/tests/test_workflow_integration.py)).

### Objetivos

1. Criar o módulo [`src/agent_lab/human_review_use_case.py`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/human_review_use_case.py) contendo a classe de caso de uso `RecordHumanDecisionUseCase` e o read-model de resultado `RecordHumanDecisionResult`;
2. Executar em código de produção a coordenação estrita em duas fases:
   - **Fase 1 (Preparação e Validação Determinística em Memória):** Construção integral de todos os artefatos (`HumanReview`, `AuditEvent`, `GovernanceWorkflow` concluído e `WorkflowConcluded`), assegurando que nenhum erro determinístico ocorra após o início do I/O;
   - **Fase 2 (Persistência Coordenada):** Persistência sequencial em `AuditRepository` e em `WorkflowLifecycleRepository`;
3. Manter a persistência dual-write estritamente **não-atômica** e sem mascaramento de falhas parciais;
4. Oferecer cobertura dedicada dos cenários felizes, violações de domínio e falhas de persistência especificados nesta SPEC sem dependência de UI ou API.

---

## 4. Decisões de Design da API de Aplicação

### 4.1 Função vs. Classe

**Decisão:** Utilizar a classe `RecordHumanDecisionUseCase` com injeção de dependências no construtor (`__init__`) e método de execução `execute(...)`.

**Justificativa:**
- **Injeção Limpa de Dependências:** Permite desacoplar as instâncias dos repositórios (`AuditRepository` e `WorkflowLifecycleRepository`) dos parâmetros da requisição de negócio, viabilizando inicialização única em pontos de entrada (UI/API);
- **Testabilidade:** Facilita a passagem de fakes ou mocks em testes unitários para simulação de falhas de I/O em etapas específicas da persistência;
- **Precedente Arquitetural:** Estabelece o padrão canônico para os futuros casos de uso da camada de aplicação sem criar um God Object agregador.

### 4.2 Dependências Mínimas e Protocolos Existentes

A classe recebe os protocolos canônicos existentes no repositório como contratos estruturais de tipagem estática:
- [`AuditRepository`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/audit_repository.py#L31) em `src/agent_lab/audit_repository.py`;
- [`WorkflowLifecycleRepository`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow_repository.py#L48) em `src/agent_lab/workflow_repository.py`.

*(Nota: Os protocolos `AuditRepository` e `WorkflowLifecycleRepository` não possuem o decorator `@runtime_checkable`. Conforme a governança do projeto, eles não são modificados e são utilizados como contratos estruturais/tipagem estática sem validações `isinstance` em tempo de execução).*

```python
class RecordHumanDecisionUseCase:
    def __init__(
        self,
        *,
        audit_repository: AuditRepository,
        workflow_lifecycle_repository: WorkflowLifecycleRepository,
    ) -> None:
        self._audit_repository = audit_repository
        self._workflow_lifecycle_repository = workflow_lifecycle_repository
```

### 4.3 Parâmetros do Método `execute`

```python
def execute(
    self,
    workflow: GovernanceWorkflow,
    *,
    review_id: str,
    audit_event_id: str,
    lifecycle_event_id: str,
    human_decision: HumanDecision,
    reviewer_identity: VerifiedSpecialistIdentity,
    reviewed_at: datetime,
    justification: str | None = None,
    corrections: Iterable[CorrectionRequest] = (),
) -> RecordHumanDecisionResult: ...
```

- **`workflow`:** Instância de [`GovernanceWorkflow`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow.py#L33) a ser deliberada (validada defensivamente como `isinstance(workflow, GovernanceWorkflow)`);
- **`review_id`:** Identificador da revisão humana;
- **`audit_event_id`:** Identificador único do evento de auditoria;
- **`lifecycle_event_id`:** Identificador único do evento `WorkflowConcluded`;
- **Parâmetros da decisão:** `human_decision`, `reviewer_identity`, `reviewed_at`, `justification`, `corrections`.

### 4.4 Estrutura de Retorno

Dataclass imutável congelada (`frozen=True`, `slots=True`):

```python
@dataclass(frozen=True, slots=True)
class RecordHumanDecisionResult:
    workflow: GovernanceWorkflow
    review: HumanReview
    audit_event: AuditEvent
    lifecycle_event: WorkflowConcluded
```

---

## 5. Ordem Exata de Coordenação e Categorias de Falha

### 5.1 Sequência em Duas Fases (Domain Preparation $\rightarrow$ I/O)

Para garantir que nenhuma falha parcial em disco seja provocada por validações determinísticas tardias, **todos os artefatos de domínio são construídos e validados em memória antes do primeiro append físico**:

```text
[Chamador / UI]
      │
      │ execute(workflow, review_id, audit_event_id, lifecycle_event_id, ...)
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: PREPARAÇÃO E VALIDAÇÃO DETERMINÍSTICA EM MEMÓRIA (Zero I/O)        │
│                                                                             │
│ 1. Validação Estrutural de Entrada (Application)                            │
│    - Valida tipo: isinstance(workflow, GovernanceWorkflow) -> TypeError     │
│                                                                             │
│ 2. Construção e Validação do Parecer Humano e Auditoria (Domain)            │
│    - result = record_human_review(...)                                      │
│    - Se houver violação (justificativa/correções/datas), levanta exceção    │
│                                                                             │
│ 3. Transição de Estado em Memória do Workflow (Domain)                      │
│    - concluded_workflow = conclude_governance_workflow(workflow, review)    │
│    - Se o workflow já estiver revisado, o domínio levanta ValueError         │
│                                                                             │
│ 4. Construção e Validação do Evento de Lifecycle (Domain)                   │
│    - lifecycle_event = WorkflowConcluded(                                   │
│          event_id=lifecycle_event_id,                                       │
│          workflow_id=workflow.workflow_id,                                  │
│          review=result.review                                               │
│      )                                                                      │
│    - Validações de event_id e review executadas em memória                  │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      │ (Todos os artefatos em memória válidos com sucesso)
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: PERSISTÊNCIA COORDENADA (I/O)                                       │
│                                                                             │
│ 5. Persistência de Auditoria (Repository 1)                                  │
│    - audit_repository.append(result.audit_event)                            │
│    - [PONTO DE FALHA]: Propaga exceção imediatamente se falhar.             │
│                                                                             │
│ 6. Persistência de Lifecycle (Repository 2)                                  │
│    - workflow_lifecycle_repository.append_concluded(lifecycle_event)        │
│    - [PONTO DE FALHA]: Propaga exceção imediatamente se falhar.             │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: RETORNO CONSOLIDADO                                                 │
│                                                                             │
│ 7. Retorno do resultado                                                     │
│    - RecordHumanDecisionResult(concluded_workflow, review, audit, lifecycle)│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Categorias de Falha e Semântica de Persistência

As falhas possíveis durante a execução são estritamente categorizadas conforme os contratos comprovados pelo código:

#### Categoria A — Falhas Determinísticas da Fase 1 / Domínio (Zero I/O)
* **Origem:** Violação de invariantes em `record_human_review`, `conclude_governance_workflow`, `WorkflowConcluded` ou validação estrutural de `workflow: GovernanceWorkflow`;
* **Exemplos:** `TypeError` por tipo não-`GovernanceWorkflow`; `ValueError` por `workflow` já revisado; `ValueError` por justificativa ausente em `REJECT`/`REQUEST_CORRECTION`; `ValueError` por ausência de correções em `REQUEST_CORRECTION`; `ValueError` por correções em `APPROVE`; `ValueError` por `lifecycle_event_id` vazio/em branco;
* **Garantia:** Zero I/O ocorreu. Nenhuma chamada a `audit_repository` ou `workflow_lifecycle_repository` é realizada, preservando os arquivos físicos 100% inalterados.

#### Categoria B — Rejeições Determinísticas Pré-Write dos Repositórios (Fase 2)
* **Origem:** Validações em memória executadas pelos repositórios antes de abrir os arquivos físicos em modo append (`open(..., "a")`);
* **Exemplos:**
  - `AuditRepository`: `DuplicateAuditEventError` (verificado via `_read_all_events()` antes da escrita);
  - `WorkflowLifecycleRepository`: `DuplicateWorkflowEventError`, `WorkflowNotOpenedError`, `WorkflowAlreadyConcludedError`, ou mismatch de `material_id` / `system_recommendation` / `reviewed_at` entre conclusão e abertura (verificados via `_read_all()` antes da escrita);
* **Garantia:** O código real dos repositórios comprova que essas validações ocorrem estritamente antes de `open(..., "a")`, garantindo que nenhuma nova linha é gravada no arquivo correspondente caso ocorra rejeição pré-write.

#### Categoria C — Falhas Físicas de I/O na Persistência (Fase 2)
* **Origem:** Erros reais de disco/sistema operacional (`OSError`, disco cheio, permissão negada, interrupção de processo durante `write`/`flush`/`fsync`);
* **Garantia e Semântica:**
  - A exceção propaga imediatamente sem mascaramento;
  - **Sem transação, sem 2PC, sem rollback, sem compensação, sem retry e sem reparo automático;**
  - O estado físico do arquivo em disco pode ser parcial/indeterminado caso a falha ocorra no meio da escrita em nível de sistema operacional;
  - Se a falha ocorrer no `WorkflowLifecycleRepository` após sucesso no `AuditRepository`, o log de auditoria permanece com o evento gravado (imutável) e a divergência física resultante é detectável de forma somente-leitura por [`verify_repositories_consistency`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/consistency.py#L321) (acusando `MISSING_WORKFLOW_CONCLUDED`) ou por leituras *fail-closed* (`WorkflowCorruptionError` / `AuditCorruptionError`).

---

## 6. Escopo Detalhado

### Incluído

1. **Módulo de Aplicação ([`src/agent_lab/human_review_use_case.py`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/human_review_use_case.py)):**
   - Dataclass imutável `RecordHumanDecisionResult`;
   - Classe `RecordHumanDecisionUseCase` com método `execute(...)` implementando a coordenação estrita em duas fases;
   - Validações estruturais de tipo na fronteira de aplicação (`isinstance(workflow, GovernanceWorkflow) -> TypeError`);
2. **Testes Unitários ([`tests/test_human_review_use_case.py`](file:///C:/Users/Administrador/agent-lab-pascoal/tests/test_human_review_use_case.py)):**
   - Teste de fluxo completo de aprovação (`APPROVE`);
   - Teste de fluxo completo de reprovação (`REJECT` com justificativa);
   - Teste de fluxo completo de correção (`REQUEST_CORRECTION` com justificativa e correções);
   - Teste comprovando que workflow já revisado falha pela regra de domínio `conclude_governance_workflow` antes de qualquer I/O;
   - Teste comprovando que violações de regras de `HumanReview` (justificativa ausente, correções inválidas) falham antes de qualquer I/O;
   - Teste comprovando que identificador de lifecycle inválido falha na Fase 1 antes de qualquer I/O no repositório de auditoria;
   - Teste de rejeição defensiva de tipo não-`GovernanceWorkflow` no método `execute`;
   - Teste simulando falha de persistência no `AuditRepository` (comprovando propagação da exceção e que o `WorkflowLifecycleRepository` não é chamado);
   - Teste simulando falha de persistência no `WorkflowLifecycleRepository` (comprovando propagação da exceção após sucesso no `AuditRepository`);
3. **Testes de Integração ([`tests/test_human_review_use_case_integration.py`](file:///C:/Users/Administrador/agent-lab-pascoal/tests/test_human_review_use_case_integration.py)):**
   - Teste de integração vertical com instâncias reais de `JsonlAuditRepository` e `JsonlWorkflowLifecycleRepository` em arquivos JSONL temporários;
   - Comprovação da persistência física de ambas as trilhas após reinicialização;
   - Comprovação de compatibilidade com a verificação de consistência dual-write ([`verify_repositories_consistency`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/consistency.py#L321));
   - Comprovação da reidratação pós-restart do workflow revisado via [`rehydrate_workflow`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow_projection.py#L28).

### Explicitamente Fora de Escopo

- Qualquer outro caso de uso de aplicação (`OpenGovernanceWorkflow`, `OpenCorrectionFollowUp`, `RegisterMaterialRevision`, `InspectRevisionLineage`);
- Fila HITL, mecanismos de prioridade, claim ou SLAs operacionais;
- Interfaces gráficas (Streamlit, `app.py`), APIs REST, endpoints HTTP ou CLI;
- Processamento assíncrono, threads, distributed locks ou concorrência multiprocesso;
- Bancos de dados relacionais, transações ACID ou mecanismos de compensação;
- Otimizações de escala da pressão P-07 (DuckDB, Polars, DataFrames, índices de repositório, duplicate pre-filtering);
- Aplicação automática de `CorrectionRequest` ou criação automática de `MaterialRevision`.

---

## 7. Estratégia TDD Planejada

A implementação seguirá ciclo estrito de micro-TDD em fatias incrementais:

```text
Fatia 1 (RED → GREEN) — Estrutura de Retorno e Inicialização do Caso de Uso
Fatia 2 (RED → GREEN) — Coordenação em Duas Fases do Fluxo Feliz (Domínio → Audit Repo → Lifecycle Repo)
Fatia 3 (RED → GREEN) — Propagação Fail-Closed de Erros do Domínio (Workflow já revisado, justificativa ausente) Antes de I/O
Fatia 4 (RED → GREEN) — Validação de Artefatos em Memória (Lifecycle Event) Antes de I/O de Auditoria
Fatia 5 (RED → GREEN) — Comportamento Explícito de Falhas de Persistência (Audit e Lifecycle)
Fatia 6 (RED → GREEN) — Integração Ponta a Ponta com Repositórios JSONL Reais e Verificação de Consistência
Regressão Geral       — $env:PYTHONPATH="src"; py -3.11 -m unittest discover -s tests -v (412 + novos testes)
```

---

## 8. Critérios de Aceite

- [ ] Suíte existente de 412 testes preservada 100% GREEN (`unittest` / Python 3.11);
- [ ] Implementação de `RecordHumanDecisionUseCase` e `RecordHumanDecisionResult` em `src/agent_lab/human_review_use_case.py`;
- [ ] O caso de uso reutiliza 100% dos contratos existentes ([`audit.py`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/audit.py), [`workflow.py`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow.py), [`human_review.py`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/human_review.py), [`workflow_events.py`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow_events.py), [`audit_repository.py`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/audit_repository.py), [`workflow_repository.py`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/workflow_repository.py)) sem alterar seus arquivos;
- [ ] Nenhum `ApplicationService` genérico ou God Object é introduzido;
- [ ] A coordenação executa estritamente a sequência em duas fases (preparação de domínio com zero I/O $\rightarrow$ persistência sequencial);
- [ ] Invariantes do domínio continuam sendo validadas exclusivamente no domínio;
- [ ] O comportamento de falha parcial do dual-write é mantido explícito, sem promessas de atomicidade ou mascaramento de erros;
- [ ] Cobertura dedicada dos cenários felizes, violações de domínio e falhas de persistência especificados nesta SPEC;
- [ ] `git diff --check` permanece limpo.

---

## 9. Riscos e Mitigações

| Risco | Severidade | Mitigação Arquitetural |
| --- | --- | --- |
| Duplicação de regras de estado na Application | Alta | A Application não checa `workflow.status`; delega a transição para `conclude_governance_workflow`, permitindo que o domínio levante a exceção. |
| Falha parcial por validação tardia de lifecycle | Alta | Todos os artefatos (inclusive `WorkflowConcluded`) são construídos e validados na Fase 1 antes de qualquer I/O em repositórios. |
| Supor atomicidade ou criar rollbacks artificiais | Alta | Proibição explícita na SPEC; falhas propagam exceções sem mascaramento e são diagnosticáveis por `verify_repositories_consistency`. |
| Criar um God Service agregando outros casos de uso | Média | A SPEC delimita exclusivamente a classe `RecordHumanDecisionUseCase`. |
| Acoplamento com interfaces externas (UI/API) | Média | O caso de uso opera com dependências puras injetadas via protocolo, sem referências a web ou CLI. |

---

## 10. Arquivos Envolvidos

* **Novos Arquivos:**
  * [`src/agent_lab/human_review_use_case.py`](file:///C:/Users/Administrador/agent-lab-pascoal/src/agent_lab/human_review_use_case.py)
  * [`tests/test_human_review_use_case.py`](file:///C:/Users/Administrador/agent-lab-pascoal/tests/test_human_review_use_case.py)
  * [`tests/test_human_review_use_case_integration.py`](file:///C:/Users/Administrador/agent-lab-pascoal/tests/test_human_review_use_case_integration.py)
  * [`docs/specs/0074_human_review_application_use_case_v1.md`](file:///C:/Users/Administrador/agent-lab-pascoal/docs/specs/0074_human_review_application_use_case_v1.md)
* **Arquivos Existentes Modificados em `src/`:**
  * Nenhum. Todos os contratos existentes são preservados intactos.
