# SPEC 0077 — Pending Human Review Queue Projection v1

> Especificação técnica da projeção pura, determinística e somente-leitura (`read-only`)
> da fila de workflows pendentes de revisão humana (`PENDING_HUMAN_REVIEW`) no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0077` |
| Status | `Implementada e Validada (Aguardando PR / Integração)` |
| Issue relacionada | `#77` |
| Branch funcional | `feature/issue-77-pending-human-review-queue-projection` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-29` |
| Última atualização | `2026-08-29` |
| Baseline de entrada | `423 testes aprovados` |
| Baseline final | `438 testes aprovados (+15 testes)` |
| Runner oficial | `unittest` / Python 3.11 |

---

## 1. Contexto

O **Agent Lab Pascoal** consolidou em seu núcleo normativo contratos estritos de domínio, persistência append-only em disco e o primeiro boundary da camada de aplicação:

- Contratos de decisão humana e auditoria imutável (`HumanReview` em `src/agent_lab/human_review.py`, `AuditEvent` e `record_human_review` em `src/agent_lab/audit.py`);
- Contrato temporal e imutável de workflow (`GovernanceWorkflow`, `conclude_governance_workflow`, `open_correction_follow_up` em `src/agent_lab/workflow.py`);
- Eventos de lifecycle e repositório append-only (`WorkflowOpened`, `WorkflowConcluded` em `src/agent_lab/workflow_events.py`, `WorkflowLifecycleRepository` e `JsonlWorkflowLifecycleRepository` em `src/agent_lab/workflow_repository.py`);
- Projeção de reidratação de workflow unitário (`rehydrate_pending_workflow`, `rehydrate_workflow` em `src/agent_lab/workflow_projection.py`);
- Verificação somente-leitura de consistência cruzada dual-write (`verify_dual_write_consistency`, `verify_repositories_consistency` em `src/agent_lab/consistency.py`);
- Primeiro boundary explícito de aplicação (`RecordHumanDecisionUseCase` em `src/agent_lab/human_review_use_case.py`).

Baseline oficial verificado:

```powershell
$env:PYTHONPATH="src"; py -3.11 -m unittest discover -s tests -v
# Ran 423 tests
# OK
```

---

## 2. Separação Canônica de Camadas e Princípios

Esta SPEC segue rigorosamente o princípio arquitetural:

```text
Application coordena.
Domain decide.
Repository preserva fatos.
Projection interpreta.
```

- **Domain (`src/agent_lab/workflow.py`):** Define a entidade imutável `GovernanceWorkflow`, o enum `WorkflowStatus` e as regras de transição pura. O domínio não conhece coleções globais, repositórios nem ordenações de fila;
- **Repository (`src/agent_lab/workflow_repository.py`):** Preserva os fatos históricos brutos (`WorkflowOpened`, `WorkflowConcluded`) em ordem física de append em disco, sob o princípio `Repository != Projection`. O repositório não interpreta estados agregados;
- **Projection (`src/agent_lab/workflow_projection.py`):** Interpreta o fluxo de eventos em memória e deriva deterministicamente a visão agregada dos workflows que atualmente aguardam revisão humana;
- **Application:** Consumirá futuramente a projeção pura sem duplicar regras de negócio ou de agregação de estado.

---

## 3. Problema e Objetivos

### Problema

O repositório de ciclo de vida armazena eventos append-only de abertura (`WorkflowOpened`) e conclusão (`WorkflowConcluded`). No entanto, o sistema ainda não possui um read-model ou projeção operacional explícita que represente quais workflows estão atualmente aguardando revisão humana (`PENDING_HUMAN_REVIEW`).

Atualmente:
1. `rehydrate_workflow` opera estritamente sobre o histórico unitário de um único `workflow_id` (1 ou 2 eventos de um mesmo ciclo);
2. `list_all_opened()` lista todas as aberturas da história do repositório, incluindo workflows que já foram concluídos posteriormente;
3. Não existe uma função pura de projeção que processe um fluxo global de eventos de múltiplos workflows e projete a fila ativa de pendências operacionais.

Sem essa projeção, qualquer camada consumidora futura (camada de aplicação, UI Streamlit, CLI ou API) seria forçada a atuar como um "orquestrador acidental", agregando eventos e filtrando estados de forma fragmentada e ad-hoc.

### Objetivos

1. Introduzir a função pura de projeção `project_pending_human_review_queue(events: Sequence[WorkflowLifecycleEvent]) -> tuple[GovernanceWorkflow, ...]` no módulo `src/agent_lab/workflow_projection.py`;
2. Processar uma sequência em memória de eventos de ciclo de vida, agrupando os eventos pelo seu respectivo `workflow_id` e reidratando deterministicamente cada ciclo unitário através da função canônica `rehydrate_workflow`;
3. Filtrar e reter exclusivamente os workflows que resultam no estado operacional `WorkflowStatus.PENDING_HUMAN_REVIEW` (descartando workflows no estado `REVIEWED`);
4. Aplicar ordenação determinística e canônica aos workflows pendentes:
   - Critério primário: FIFO por `opened_at` ascendente;
   - Critério de desempate: `workflow_id` lexicográfico ascendente;
5. Suportar qualquer interleaving global entre workflows distintos que preserve a ordem causal interna dos eventos de cada `workflow_id`, sem que a ordem relativa de chegada entre workflows distintos afete a composição ou a ordenação da fila final projetada;
6. Garantir comportamento estritamente *fail-closed* contra históricos unitários inválidos ou violações de causalidade interna de cada workflow;
7. Validar a projeção em suíte dedicada de testes unitários e em teste de integração vertical pós-restart com `JsonlWorkflowLifecycleRepository`.

---

## 4. Decisões de Design da Projeção

### 4.1 Assinatura da Função e Ausência de Novo Read-Model Redundante na v1

**Decisão:** Utilizar a assinatura funcional pura retornando tupla de instâncias existentes de `GovernanceWorkflow`:

```python
def project_pending_human_review_queue(
    events: Sequence[WorkflowLifecycleEvent],
) -> tuple[GovernanceWorkflow, ...]:
    ...
```

**Justificativa:**
- **Simplicidade e Reuso:** `GovernanceWorkflow` já encapsula perfeitamente todas as propriedades do workflow em `PENDING_HUMAN_REVIEW` (`workflow_id`, `recommendation`, `opened_at`, `material_id`, `status`, `predecessor_workflow_id`, `triggering_review_id`);
- **Sem Superengenharia:** Não introduzir `PendingReviewItem`, `PendingHumanReviewQueue` class ou similares nesta fatia v1. Atributos operacionais futuros (*claim, assignee, claimed_at, SLA, priority*) poderão justificar contratos próprios em incrementos posteriores quando houver necessidade concreta.

### 4.2 Distinção Mandatória sobre a Ordem dos Eventos

A projeção estabelece uma distinção conceitual e técnica explícita entre duas dimensões de ordenação:

#### A) Interleaving Global entre Workflows Distintos
- A projeção suporta qualquer interleaving global entre workflows distintos que preserve a ordem causal interna dos eventos de cada `workflow_id`;
- Qualquer permutação na ordem relativa de chegada de eventos pertencentes a `workflow_id`s diferentes produz rigorosamente a mesma composição e a mesma ordenação canônica final `(opened_at, workflow_id)` da fila.

#### B) Ordem Causal Interna de Cada `workflow_id`
- A ordem lifecycle interna dos eventos de um mesmo workflow continua semanticamente relevante e mandatória;
- A sequência `WorkflowOpened -> WorkflowConcluded` é válida;
- Uma sequência invertida `WorkflowConcluded -> WorkflowOpened` é inválida e **NÃO** deve ser silenciosamente reorganizada pela projeção;
- **Princípio:** O determinismo da Projection não autoriza reparo implícito de fatos persistidos. Históricos unitários corrompidos ou causalmente invertidos falham imediatamente de forma *fail-closed* através de `rehydrate_workflow`.

### 4.3 Algoritmo de Projeção

1. **Validação de Entrada:**
   - Valida se `events` é `Sequence` (rejeita com `TypeError`);
   - Valida se cada elemento é instância de `WorkflowLifecycleEvent` (`WorkflowOpened` ou `WorkflowConcluded`), rejeitando tipos desconhecidos com `ValueError`;
2. **Agrupamento Preservando Ordem Causal:**
   - Agrupa os eventos por `workflow_id` mantendo a ordem relativa em que aparecem na sequência de entrada para cada workflow individual;
3. **Reidratação Unitária:**
   - Para cada `workflow_id`, delega a sequência unitária de eventos para `rehydrate_workflow(workflow_events)`;
   - Se o histórico unitário for inválido (conclusão antes de abertura, duplicidades, etc.), `rehydrate_workflow` levanta `ValueError` de forma *fail-closed*;
4. **Filtragem de Pendências:**
   - Seleciona apenas os workflows reidratados cujo `status == WorkflowStatus.PENDING_HUMAN_REVIEW` (ou seja, `review is None`);
5. **Ordenação Canônica:**
   - Ordena os workflows pendentes pela chave `(workflow.opened_at, workflow.workflow_id)` em ordem ascendente;
6. **Retorno Imutável:**
   - Retorna `tuple(ordered_pending_workflows)`.

---

## 5. Invariantes

1. **Pureza e Zero-I/O:** A projeção opera estritamente em memória sobre sequências de eventos já carregadas, sem dependência de disco, rede ou estado global;
2. **Imutabilidade e Idempotência:** A saída é uma tupla imutável. Múltiplas execuções sobre os mesmos eventos produzem resultados idênticos;
3. **Independência de Interleaving Global:** A ordenação final da fila é determinada unicamente por `(opened_at, workflow_id)` e independe da ordem relativa entre eventos de workflows distintos;
4. **Preservação Causal Interna:** Violações na ordem cronológica/causal de um mesmo workflow não são mascaradas nem corrigidas;
5. **Preservação de Linhagem Causal:** Workflows de follow-up (`open_correction_follow_up`) preservam `predecessor_workflow_id` e `triggering_review_id` intactos;
6. **Sem Mutação de Entidades:** Nenhum workflow ou evento é mutado durante a projeção.

---

## 6. Escopo Detalhado

### Incluído

1. **Módulo de Projeção (`src/agent_lab/workflow_projection.py`):**
   - Implementação da função pura `project_pending_human_review_queue(events: Sequence[WorkflowLifecycleEvent]) -> tuple[GovernanceWorkflow, ...]`;
2. **Testes Unitários (`tests/test_workflow_projection.py`):**
   - Entrada vazia `()` retornando tupla vazia `()`;
   - Projeção de múltiplos `WorkflowOpened` resultando em workflows `PENDING_HUMAN_REVIEW`;
   - Exclusão precisa de workflows que possuem `WorkflowConcluded`;
   - Ordenação canônica FIFO por `opened_at` ascendente;
   - Desempate canônico por `workflow_id` lexicográfico ascendente;
   - Imunidade ao interleaving global entre workflows distintos que preserve a ordem causal interna de cada workflow_id;
   - Rejeição *fail-closed* de sequência causalmente invertida dentro de um mesmo workflow (`WorkflowConcluded` antes de `WorkflowOpened`);
   - Rejeição *fail-closed* de duplicidades e anomalias históricas de um mesmo workflow;
   - Preservação da linhagem causal de correction follow-up (`predecessor_workflow_id` e `triggering_review_id`);
   - Validação defensiva de tipos de entrada (`TypeError` para não-`Sequence`, `ValueError` para elementos inválidos);
3. **Teste de Integração Vertical (`tests/test_pending_review_queue_projection_integration.py`):**
   - Persistência física de múltiplos eventos (`WorkflowOpened` e `WorkflowConcluded`) em arquivo JSONL real via `JsonlWorkflowLifecycleRepository`;
   - Simulação de reinicialização de processo através de uma nova instância do repositório;
   - Leitura de todos os eventos via `repository.list_all_events()`;
   - Projeção da fila via `project_pending_human_review_queue`, comprovando filtragem correta, integridade de dados e ordenação canônica pós-restart.

### Explicitamente Fora de Escopo

- Mecanismos de claim, lock, reserva ou checkout de workflows por especialista;
- Atribuição de responsabilidade (*assignment / assignee / specialist_id* associado ao item);
- Atributos operacionais de fila (*claimed_at, priority, urgency*);
- Cálculo de SLAs, prazos de vencimento ou alertas de tempo de atendimento;
- Interfaces de usuário (Streamlit / `app.py`), APIs REST, endpoints HTTP ou CLI;
- Processamento assíncrono, concorrência, multi-threading ou distributed locks;
- Otimizações de escala da pressão P-07 (DuckDB, Polars, DataFrames, índices de busca em repositório);
- Mutação ou reparo automático de registros em disco.

---

## 7. Estratégia Micro-TDD Executada

```text
Fatia 1 (RED → GREEN) [Concluída] — Validação estrutural de entrada (TypeError / ValueError) e caso base vazio (events=() -> ()) (+3 testes unitários)
Fatia 2 (RED → GREEN) [Concluída] — Projeção de WorkflowOpened isolados retornando GovernanceWorkflow em PENDING_HUMAN_REVIEW (+2 testes unitários)
Fatia 3 (RED → GREEN) [Concluída] — Exclusão correta de workflows concluídos (+2 testes unitários)
Fatia 4 (RED → GREEN) [Concluída] — Ordenação determinística canônica FIFO por opened_at com tie-break por workflow_id (+2 testes unitários)
Fatia 5 [Caracterização GREEN] — Invariância a interleaving global entre workflows distintos preservando causalidade interna (+1 teste unitário)
Fatia 6 [Caracterização GREEN] — Preservação de correction follow-up lineage por reutilização de rehydrate_pending_workflow (+1 teste unitário)
Fatia 7 (RED → GREEN) [Concluída] — Fail-closed para históricos inválidos, delegando semântica de lifecycle a rehydrate_workflow (+3 testes unitários)
Fatia 8 [Integração GREEN por composição] — Integração vertical pós-restart com JsonlWorkflowLifecycleRepository (+1 teste de integração)
Regressão Geral [Concluída] — $env:PYTHONPATH="src"; py -3.11 -m unittest discover -s tests -v (438/438 GREEN — 100%)
```

> **Nota de Composição e Caracterização:**
> - As Fatias 5 e 6 foram propriedades emergentes da arquitetura, comprovadas por caracterização nos testes unitários;
> - A Fatia 8 foi comprovada por composição vertical dos boundaries existentes (`JsonlWorkflowLifecycleRepository.list_all_events()` → `project_pending_human_review_queue()`);
> - Nenhuma delas exigiu código adicional de produção.

---

## 8. Critérios de Aceite

- [x] Suíte existente de 423 testes preexistentes preservada + 15 novos testes = 438/438 GREEN (`unittest` / Python 3.11);
- [x] Implementação de `project_pending_human_review_queue` em `src/agent_lab/workflow_projection.py`;
- [x] A função opera com pureza estrita (zero I/O) e retorna `tuple[GovernanceWorkflow, ...]`;
- [x] Nenhum novo read-model redundante (`PendingReviewItem`, etc.) é introduzido na v1;
- [x] A ordenação da fila é canônica por `(opened_at, workflow_id)` ascendente;
- [x] Interleaving global arbitrário entre workflows distintos que preserve a ordem causal interna produz a mesma fila (invariância de interleaving);
- [x] Históricos unitários com inversão causal ou corrupção falham fechado sem reparo implícito (fail-closed via `rehydrate_workflow`);
- [x] Teste de integração vertical pós-restart com `JsonlWorkflowLifecycleRepository` aprovado (`tests/test_pending_review_queue_projection_integration.py`);
- [x] `git diff --check` permanece limpo.

---

## 9. Riscos e Mitigações

| Risco | Severidade | Mitigação Arquitetural |
| :--- | :--- | :--- |
| **Reparo implícito de histórico corrompido** | Alta | A projeção agrupa eventos preservando a ordem física de chegada para cada workflow e delega a validação estrita para `rehydrate_workflow`, garantindo que inversões de eventos falhem fechado. |
| **Dependência da ordem física do arquivo entre workflows** | Alta | A composição e a ordenação final são independentes do interleaving físico entre eventos de workflows distintos, desde que a ordem causal interna dos eventos de cada `workflow_id` seja preservada. |
| **Vazamento de I/O na Projeção** | Alta | A assinatura aceita exclusivamente `Sequence[WorkflowLifecycleEvent]`, sem acoplamento com repositórios. |
| **Acoplamento com Claim/SLA** | Média | A saída é estritamente `tuple[GovernanceWorkflow, ...]`, sem campos operacionais prematuros. |

---

## 10. Arquivos Envolvidos

* **Novos Arquivos:**
  * `docs/specs/0077_pending_human_review_queue_projection_v1.md`
  * `tests/test_pending_review_queue_projection_integration.py`
* **Arquivos Existentes a Modificar:**
  * `src/agent_lab/workflow_projection.py`
  * `tests/test_workflow_projection.py`
