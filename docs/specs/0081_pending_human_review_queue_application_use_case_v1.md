# SPEC 0081 — Pending Human Review Queue Application Use Case v1

> Especificação técnica do caso de uso da camada de aplicação responsável por consultar
> deterministicamente a fila de workflows pendentes de revisão humana (`PENDING_HUMAN_REVIEW`) no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0081` |
| Status | `Concluída e Integrada na main` |
| Issue relacionada | `#81` |
| PR funcional | `#82` |
| Merge commit | `34bcf7d` |
| Branch funcional | `feature/issue-81-pending-human-review-queue-application-use-case` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-30` |
| Data do ambiente | `2026-08-30` |
| Última atualização | `2026-08-30` |
| Baseline de entrada | `438 testes aprovados` |
| Baseline final | `444 testes aprovados (+6 testes)` |
| Runner oficial | `unittest` / Python 3.11.9 |

---

## 1. Contexto

O **Agent Lab Pascoal** consolidou em seu núcleo normativo contratos estritos de domínio, persistência append-only em disco, projeções determinísticas e os boundaries da camada de aplicação:

- Contratos de decisão humana e auditoria imutável (`HumanReview` em `src/agent_lab/human_review.py`, `AuditEvent` e `record_human_review` em `src/agent_lab/audit.py`);
- Contrato temporal e imutável de workflow (`GovernanceWorkflow`, `conclude_governance_workflow`, `open_correction_follow_up` em `src/agent_lab/workflow.py`);
- Eventos de lifecycle e persistência append-only (`WorkflowOpened`, `WorkflowConcluded` em `src/agent_lab/workflow_events.py`, `WorkflowLifecycleRepository` e `JsonlWorkflowLifecycleRepository` em `src/agent_lab/workflow_repository.py`);
- Projeção pura e determinística da fila ativa de revisão humana (`project_pending_human_review_queue` em `src/agent_lab/workflow_projection.py`, integrada na Issue #77 / SPEC 0077);
- Primeiro boundary explícito de aplicação para deliberação humana (`RecordHumanDecisionUseCase` em `src/agent_lab/human_review_use_case.py`, integrado na Issue #74 / SPEC 0074).

O protocolo `WorkflowLifecycleRepository` já expõe a operação de consulta de fatos brutos:

```python
list_all_events() -> tuple[WorkflowLifecycleEvent, ...]
```

Antes da implementação desta SPEC, para consultar os workflows que aguardavam deliberação de um especialista, um consumidor externo (UI, API ou CLI) precisaria orquestrar manualmente a leitura de eventos no repositório e encaminhá-los para `project_pending_human_review_queue`.

Essa ausência de boundary, existente na baseline de entrada, faria as interfaces externas atuarem como "orquestradores acidentais".

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

1. **`System recommendation ≠ Human authority`:** A recomendação do sistema permanece preservada; a deliberação humana pertence exclusivamente ao especialista;
2. **`Evidence ≠ Decision`:** Evidências observadas não se confundem com a deliberação soberana do revisor;
3. **`CorrectionRequest ≠ MaterialRevision`:** Prescrição normativa humana difere do fato cadastral;
4. **`WorkflowLifecycleEvent ≠ AuditEvent`:** O ciclo operacional e a auditoria imutável permanecem desacoplados;
5. **`Repository ≠ Projection`:** O repositório preserva a ordem física dos fatos persistidos (`WorkflowOpened`, `WorkflowConcluded`); a projeção interpreta a sequência em memória para derivar os workflows em `PENDING_HUMAN_REVIEW` com ordenação canônica;
6. **Invariantes pertencem ao Domínio e à Projeção:** A camada Application não filtra status (`workflow.status == ...`), não reordena itens, não valida transições de ciclo de vida e não reconstrói entidades por conta própria. Toda a agregação e interpretação do read-model pertencem exclusivamente a `project_pending_human_review_queue`;
7. **Proibição de God Service:** Não criar classes genéricas agregadoras como `WorkflowApplicationService`. O caso de uso deve ser coeso, autocontido e focado estritamente na listagem da fila pendente (`ListPendingHumanReviewsUseCase`);
8. **Operação Somente-Leitura (Zero Side Effects):** A execução do caso de uso não realiza nenhuma escrita em disco, não muta o estado dos repositórios e não altera os workflows retornados.

---

## 3. Problema e Objetivos

### Problema

Atualmente, o fluxo de leitura da fila de pendências existe de forma puramente composicional apenas em testes de integração (`tests/test_pending_review_queue_projection_integration.py`):

```text
WorkflowLifecycleRepository.list_all_events()
    ↓
project_pending_human_review_queue(...)
    ↓
tuple[GovernanceWorkflow, ...]
```

Na baseline de entrada desta SPEC, não existia uma entidade formal na camada de aplicação que assumisse o ownership dessa coordenação e a expusesse de forma coesa e testável para consumidores externos.

### Objetivos

1. Criar o módulo `src/agent_lab/pending_human_reviews_use_case.py` contendo a classe de caso de uso `ListPendingHumanReviewsUseCase`;
2. Coordenar a recuperação dos fatos históricos via `self._workflow_lifecycle_repository.list_all_events()` e a sua interpretação imediata via `project_pending_human_review_queue(events)`;
3. Retornar a tupla imutável `tuple[GovernanceWorkflow, ...]`, compatível com o consumo direto por `RecordHumanDecisionUseCase.execute(workflow, ...)`;
4. Propagar exceções de I/O, corrupção ou falhas de projeção de forma estritamente *fail-closed* sem mascaramento;
5. Fornecer cobertura de testes unitários e de integração vertical pós-restart, incluindo a comprovação de composição com `RecordHumanDecisionUseCase`.

---

## 4. Decisões de Design da API de Aplicação

### 4.1 Função vs. Classe

**Decisão:** Utilizar a classe `ListPendingHumanReviewsUseCase` com injeção de dependência no construtor (`__init__`) e método de execução sem parâmetros `execute() -> tuple[GovernanceWorkflow, ...]`.

**Justificativa:**
- **Injeção Limpa de Dependências:** Desacopla a instância do repositório (`WorkflowLifecycleRepository`) do ponto de invocação, permitindo instanciação única na inicialização de UIs/APIs;
- **Testabilidade:** Facilita a passagem de repositórios fake ou fakes estruturais em testes unitários para simular arquivos vazios, históricos corrompidos ou erros de I/O;
- **Simetria com `RecordHumanDecisionUseCase`:** Mantém o padrão estabelecido na SPEC 0074 para os use cases de aplicação.

### 4.2 Dependências e Protocolos

A classe recebe como dependência injetada exclusivamente o protocolo canônico já existente:
- `WorkflowLifecycleRepository` em `src/agent_lab/workflow_repository.py`.

```python
class ListPendingHumanReviewsUseCase:
    def __init__(
        self,
        *,
        workflow_lifecycle_repository: WorkflowLifecycleRepository,
    ) -> None:
        self._workflow_lifecycle_repository = workflow_lifecycle_repository
```

*(Nota: O protocolo `WorkflowLifecycleRepository` permanece inalterado e é utilizado como contrato de tipagem estrutural estática).*

### 4.3 Assinatura do Método `execute`

```python
def execute(self) -> tuple[GovernanceWorkflow, ...]:
    ...
```

- Não recebe parâmetros de filtro ou paginação nesta v1 (mantendo o escopo mínimo e determinístico);
- Retorna diretamente `tuple[GovernanceWorkflow, ...]`, preservando a ordenação canônica FIFO por `(opened_at ASC, workflow_id ASC)` garantida pela projeção.

### 4.4 Ausência de DTO Intermediário Redundante

**Decisão:** Retornar diretamente `tuple[GovernanceWorkflow, ...]`.

**Justificativa:**
- `GovernanceWorkflow` já é uma entidade imutável congelada (`frozen=True`, `slots=True`), que expõe todas as propriedades necessárias para apresentação e deliberação (`workflow_id`, `material_id`, `opened_at`, `status`, `recommendation`, `predecessor_workflow_id`, `triggering_review_id`);
- Não criar `ListPendingHumanReviewsResult` ou `PendingReviewItem` nesta v1 para evitar abstrações redundantes.

---

## 5. Ordem de Coordenação e Tratamento de Falhas

### 5.1 Sequência de Execução

```text
[Consumidor Externo / UI / API]
      │
      │ execute()
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Leitura de Fatos Persistidos (Repository)                                │
│    - events = self._workflow_lifecycle_repository.list_all_events()         │
│    - [PONTO DE FALHA]: Se houver erro de I/O ou corrupção, propaga.         │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      │ events: tuple[WorkflowLifecycleEvent, ...]
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Projeção Determinística da Fila Ativa (Projection / Zero I/O)            │
│    - queue = project_pending_human_review_queue(events)                     │
│    - Agrupa por workflow_id, reidrata, filtra PENDING e ordena FIFO         │
│    - [PONTO DE FALHA]: Se houver anomalia na sequência, propaga.            │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      │ queue: tuple[GovernanceWorkflow, ...]
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. Retorno ao Chamador                                                      │
│    - return queue                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Categorias de Falha

#### Categoria A — Erros de Persistência e Corrupção (Repository)
- **Origem:** `WorkflowPersistenceError` ou `WorkflowCorruptionError` levantados por `list_all_events()`;
- **Comportamento:** A exceção propaga imediatamente de forma *fail-closed* sem captura genérica, sem retries e sem reparo silencioso.

#### Categoria B — Violações Estruturais de Tipos ou Causalidade (Projection)
- **Origem:** `TypeError` ou `ValueError` levantados por `project_pending_human_review_queue` caso os eventos retornados violem contratos estruturais ou integridade de ciclo de vida;
- **Comportamento:** A exceção propaga imediatamente sem mascaramento.

---

## 6. Escopo Detalhado

### Incluído

1. **Módulo de Aplicação (`src/agent_lab/pending_human_reviews_use_case.py`):**
   - Implementação da classe `ListPendingHumanReviewsUseCase` com construtor injetado e método `execute()`.
2. **Testes Unitários (`tests/test_pending_human_reviews_use_case.py`):**
   - **Princípio Arquitetural de Testes:** Testes da Application devem validar comportamento observável e propagação de falhas. Não usar mocks ou spies para verificar detalhes internos de coordenação quando entradas e saídas fornecem evidência suficiente;
   - **Delimitação de Responsabilidades:** Filtragem, ordenação, reidratação e preservação de lineage são comportamentos da Projection e não constituem novas responsabilidades da Application. A SPEC 0081 não replica sua cobertura exaustiva;
   - Execução com repositório vazio retornando tupla vazia `()`;
   - Execução com repositório contendo eventos de lifecycle reais/fakes, comprovando por composição que o resultado da Projection atravessa a Application sem transformação em um único cenário representativo;
   - Propagação *fail-closed* de erros de persistência e corrupção do repositório (`WorkflowPersistenceError`, `WorkflowCorruptionError`);
   - Propagação *fail-closed* de erros de integridade da projeção (`TypeError`, `ValueError`).
3. **Testes de Integração Vertical (`tests/test_pending_human_reviews_use_case_integration.py`):**
   - Integração real com `JsonlWorkflowLifecycleRepository` em arquivo JSONL temporário após restart de processo;
   - Integração composicional com `RecordHumanDecisionUseCase`:
     1. Listagem inicial contendo o workflow pendente;
     2. Deliberação e conclusão via `RecordHumanDecisionUseCase.execute(...)`;
     3. Nova listagem via `ListPendingHumanReviewsUseCase.execute()` comprovando que o workflow concluído deixa de figurar na fila pendente.

### Explicitamente Fora de Escopo

- Qualquer mecanismo de claim, lock, reserva ou checkout de workflows por especialista;
- Atribuição de responsabilidade (*assignment / assignee / specialist_id*);
- Atributos operacionais de fila (*claimed_at, priority, urgency*);
- Cálculo de SLAs operacionais ou prazos;
- Interfaces de usuário (Streamlit / `app.py`), APIs REST (FastAPI) ou CLI;
- Processamento assíncrono, threads, concorrência ou paginação;
- Cache de resultados em memória;
- Otimizações de escala da pressão P-07 (DuckDB, Polars, índices de repositório);
- Alterações no domínio (`GovernanceWorkflow`, `WorkflowStatus`), repositório ou projeção existentes;
- Criação de novo schema version ou novo formato persistente;
- Criação de nova função de Projection ou novo read-model;
- Mecanismos de retry, rollback ou reparo automático.

---

## 7. Estratégia Micro-TDD Executada

```text
Fatia 1 (RED → GREEN) — Boundary mínimo: ListPendingHumanReviewsUseCase instanciado com WorkflowLifecycleRepository vazio retornando ()
Fatia 2 (GREEN por composição) — Composição Repository → Projection: cenário representativo comprovando que o resultado da Projection atravessa a Application sem transformação
Fatia 3 (GREEN por composição) — Propagação fail-closed de erros do repositório (WorkflowPersistenceError) e de integridade da projeção (ValueError)
Fatia 4 (GREEN por integração/composição) — Teste de integração vertical pós-restart com JsonlWorkflowLifecycleRepository em arquivo JSONL real
Fatia 5 (GREEN por integração/composição) — Teste de integração vertical composicional de ciclo completo: List → RecordHumanDecision → List
Regressão Geral — $env:PYTHONPATH="src"; py -3.11 -m unittest discover -s tests -v (444/444 GREEN)
```

---

## 8. Critérios de Aceite

- [x] Suíte preexistente de 438 testes mantida 100% GREEN (`unittest` / Python 3.11.9);
- [x] Implementação de `ListPendingHumanReviewsUseCase` em `src/agent_lab/pending_human_reviews_use_case.py`;
- [x] Zero alterações em módulos de domínio, repositórios, serialização ou projeções existentes em `src/`;
- [x] O caso de uso recebe `WorkflowLifecycleRepository` por injeção e retorna `tuple[GovernanceWorkflow, ...]`;
- [x] Nenhuma lógica de filtragem, ordenação ou inferência de estado é implementada na classe (delegação integral para `project_pending_human_review_queue`);
- [x] Comportamento *fail-closed* preservado para qualquer falha de leitura ou anomalia estrutural;
- [x] Testes unitários focados no contrato observável e na propagação de erros aprovados;
- [x] Testes de integração vertical aprovados (pós-restart e ciclo completo com `RecordHumanDecisionUseCase`);
- [x] `git diff --check` permanece limpo.

---

## 9. Riscos e Mitigações

| Risco | Severidade | Mitigação Arquitetural |
| :--- | :--- | :--- |
| **Duplicação de regras de filtragem/ordenação na Application** | Alta | O método `execute()` repassa integralmente o retorno de `list_all_events()` para `project_pending_human_review_queue()`, sem intervenção ou pós-processamento. |
| **Mascaramento indevido de erros de I/O ou corrupção** | Alta | A Application não possui blocos `except Exception`; permite que `WorkflowPersistenceError` e `WorkflowCorruptionError` propaguem *fail-closed*. |
| **Introdução prematura de atributos de fila (claim/SLA)** | Média | O escopo permanece estritamente delimitado a `tuple[GovernanceWorkflow, ...]`, sem campos operacionais nesta v1. |
| **Criação de God Service agregador** | Média | A classe `ListPendingHumanReviewsUseCase` é coesa e autocontida, com responsabilidade única de consulta. |

---

## 10. Arquivos Envolvidos

* **Novos Arquivos:**
  * `docs/specs/0081_pending_human_review_queue_application_use_case_v1.md`
  * `src/agent_lab/pending_human_reviews_use_case.py`
  * `tests/test_pending_human_reviews_use_case.py`
  * `tests/test_pending_human_reviews_use_case_integration.py`
* **Arquivos Existentes Modificados em `src/`:**
  * Nenhum. Todos os contratos existentes são preservados intactos.
