# SPEC 0097 — Pending Human Review Queue with Claim State Application Use Case v1

> Especificação técnica do caso de uso da camada de aplicação responsável por compor deterministicamente a fila de workflows pendentes de revisão humana (`PENDING_HUMAN_REVIEW`) com seus respectivos estados factuais de claim (`HumanReviewClaimState`) no Agent Lab Pascoal.

---

## 1. Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0097` |
| Status | `APPROVED` |
| Issue relacionada | `#97` |
| Título da Issue | `Pending Human Review Queue with Claim State Application Use Case v1` |
| Branch funcional | `feature/issue-97-pending-human-review-queue-with-claim-state` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-09-04` |
| Data do ambiente | `2026-09-04` |
| Última atualização | `2026-09-04` |
| Baseline de entrada | `531 testes aprovados` |
| Runner oficial | `unittest` / Python 3.11.9 |

---

## 2. Contexto Arquitetural

O **Agent Lab Pascoal** consolidou em seu núcleo normativo contratos estritos de domínio, persistência append-only em disco, projeções determinísticas e os boundaries da camada de aplicação:

- **Issue #81 / SPEC 0081:** Introduziu `ListPendingHumanReviewsUseCase` em `src/agent_lab/pending_human_reviews_use_case.py`, estabelecendo o boundary da Application Layer para consulta pura da fila ativa de workflows pendentes de revisão (`PENDING_HUMAN_REVIEW`), reutilizando a projeção pura `project_pending_human_review_queue` (Issue #77 / SPEC 0077);
- **Issue #85 / SPEC 0085:** Introduziu o contrato de domínio puro em memória `HumanReviewClaim` e a operação pura `claim_pending_human_review` em `src/agent_lab/human_review_claim.py`, representando o fato operacional de um especialista verificado assumir voluntariamente um workflow pendente;
- **Issue #88 / SPEC 0088:** Introduziu a persistência append-only desacoplada `JsonlHumanReviewClaimRepository` com `schema_version = 1` e escrita durável em `src/agent_lab/human_review_claim_repository.py`;
- **Issue #91 / SPEC 0091:** Introduziu o boundary da camada de aplicação para gravação `RecordHumanReviewClaimUseCase` em `src/agent_lab/human_review_claim_use_case.py`;
- **Issue #94 / SPEC 0094:** Introduziu a projeção pura em memória `project_human_review_claim_state` e o read-model imutável `HumanReviewClaimState` em `src/agent_lab/human_review_claim_projection.py`, classificando factual e deterministicamente os claims de um workflow em `NO_CLAIM`, `SINGLE_CLAIM` e `MULTIPLE_CLAIMS`.

Atualmente, o sistema possui a capacidade de consultar workflows pendentes de forma isolada e a capacidade de projetar o estado de claims de um workflow de forma isolada.

---

## 3. Problema

Não existe atualmente um boundary na camada de aplicação que componha a fila de workflows pendentes com o respectivo estado factual de claims.

A composição conceitual necessária é:

```text
WorkflowLifecycleRepository.list_all_events()
    ↓
project_pending_human_review_queue(...)  →  pending_workflows (FIFO)
    +
HumanReviewClaimRepository.list_all()
    ↓
project_human_review_claim_state(...)    →  HumanReviewClaimState por workflow
    ↓
tuple[PendingHumanReviewWithClaimStateItem, ...]
```

Sem um caso de uso dedicado na Application Layer:
1. Futuros consumidores externos (UI, API, CLI ou jobs) precisariam conhecer simultaneamente dois repositórios independentes e duas projeções puras distintas para inspecionar as pendências associadas a seus claims;
2. As camadas de apresentação ou transporte seriam forçadas a atuar como "orquestradores acidentais", violando a separação canônica de responsabilidades;
3. Haveria o risco de chamadores implementarem composições despadronizadas, reordenando itens ou inventando desempates operacionais diretamente nas bordas do sistema.

---

## 4. Objetivo

Introduzir na camada de aplicação o caso de uso somente-leitura `ListPendingHumanReviewsWithClaimStateUseCase` e o read-model de item composto `PendingHumanReviewWithClaimStateItem` no módulo `src/agent_lab/pending_human_reviews_with_claim_state_use_case.py`.

A nova classe deve orquestrar a obtenção dos dados a partir de snapshots locais únicos por execução dos dois repositórios existentes, delegar a interpretação integralmente às projeções puras existentes e retornar a lista ordenada de workflows pendentes enriquecida com o estado factual de claims correspondente de cada item.

---

## 5. Não Objetivos / Fora de Escopo

Esta SPEC explicitamente **NÃO** autoriza:

- Active claim / claim ativo;
- Winner / eleição de vencedor;
- Ownership / titularidade operacional;
- Assignment / despacho gerencial de tarefas;
- Desempate / Last-Claim-Wins;
- Exclusividade / locking / lease / mutex;
- Release / unclaim / desistência de claim;
- Transfer / reassignment entre especialistas;
- TTL / lease / expiry / SLA;
- Claimant $\rightarrow$ reviewer enforcement (deliberação continua desacoplada de claim);
- UI / Streamlit / API REST / CLI;
- Concorrência multiprocesso / transação distribuída / 2PC;
- Cache / retries / reparo automático / compensação;
- Pressão P-07 e Scale Reconnaissance;
- Alterações no pipeline de materiais ou duplicate detection;
- Qualquer otimização prematura de performance.

---

## 6. Contratos Existentes Reutilizados

A implementação não cria novas entidades de domínio ou de projeção, reutilizando estritamente:

1. `WorkflowLifecycleRepository` (`src/agent_lab/workflow_repository.py`): protocolo de ciclo de vida com `list_all_events()`;
2. `HumanReviewClaimRepository` (`src/agent_lab/human_review_claim_repository.py`): protocolo de claims com `list_all()`;
3. `project_pending_human_review_queue` (`src/agent_lab/workflow_projection.py`): projeção pura da fila ativa em `PENDING_HUMAN_REVIEW` com ordenação `(opened_at ASC, workflow_id ASC)`;
4. `project_human_review_claim_state` (`src/agent_lab/human_review_claim_projection.py`): projeção pura do estado de claims `(workflow_id, claims) -> HumanReviewClaimState`;
5. `GovernanceWorkflow` (`src/agent_lab/workflow.py`): entidade de ciclo de vida temporal;
6. `HumanReviewClaimState` (`src/agent_lab/human_review_claim_projection.py`): read-model imutável de estado de claims;
7. `HumanReviewClaimFactState` (`src/agent_lab/human_review_claim_projection.py`): enum com os estados `NO_CLAIM`, `SINGLE_CLAIM` e `MULTIPLE_CLAIMS`.

---

## 7. Boundary de Application Proposto

O caso de uso será encapsulado em um módulo dedicado da camada de aplicação:

```text
src/agent_lab/pending_human_reviews_with_claim_state_use_case.py
```

### Contrato da Classe

```python
class ListPendingHumanReviewsWithClaimStateUseCase:
    """Application use case to list pending human reviews with their factual claim state."""

    def __init__(
        self,
        *,
        workflow_lifecycle_repository: WorkflowLifecycleRepository,
        claim_repository: HumanReviewClaimRepository,
    ) -> None:
        self._workflow_lifecycle_repository = workflow_lifecycle_repository
        self._claim_repository = claim_repository

    def execute(self) -> tuple[PendingHumanReviewWithClaimStateItem, ...]:
        ...
```

---

## 8. Read-Model Composto

Para transportar o resultado da composição de forma tipada, expressiva e imutável, define-se o dataclass congelado no próprio módulo de aplicação:

```python
@dataclass(frozen=True, slots=True)
class PendingHumanReviewWithClaimStateItem:
    """Immutable composite read-model pairing a pending workflow with its factual claim state."""

    workflow: GovernanceWorkflow
    claim_state: HumanReviewClaimState

    def __post_init__(self) -> None:
        ...
```

---

## 9. Invariante Relacional Obrigatória

O item composto deve garantir rigorosamente que o estado de claims corresponde exatamente à identidade do workflow envelopado:

```text
workflow.workflow_id == claim_state.workflow_id
```

Qualquer tentativa de instanciar `PendingHumanReviewWithClaimStateItem` com identificadores divergentes deve falhar imediatamente com `ValueError` de forma *fail-closed*.

---

## 10. Semântica do `execute()`

A execução do método `execute()` deve seguir uma ordem estrita e explícita:

```text
1. events_snapshot = self._workflow_lifecycle_repository.list_all_events()
2. pending_workflows = project_pending_human_review_queue(events_snapshot)
3. claims_snapshot = self._claim_repository.list_all()
4. items = []
5. para cada workflow em pending_workflows:
       claim_state = project_human_review_claim_state(
           workflow.workflow_id,
           claims_snapshot
       )
       items.append(PendingHumanReviewWithClaimStateItem(workflow, claim_state))
6. retornar tuple(items)
```

### Regra de Coerência Factual de Consulta (Anti-N+1)

- **Exatamente UMA leitura de lifecycle:** `workflow_lifecycle_repository.list_all_events()` é invocada uma única vez;
- **Exatamente UMA leitura global de claims:** `claim_repository.list_all()` é invocada uma única vez;
- **Zero chamadas a `list_by_workflow_id()` em loop:** É expressamente proibido fazer chamadas iterativas ao repositório de claims dentro do loop de workflows.

> [!IMPORTANT]
> A leitura em lote único por execução **não é uma otimização de performance da pressão P-07**. Trata-se de uma decisão de **coerência factual da consulta**: cada fonte deve representar um único snapshot local no momento da execução, evitando que consultas sucessivas em disco vejam estados temporais diferentes para workflows adjacentes na mesma listagem.

---

## 11. Semântica Temporal da Leitura

A coordenação entre os dois repositórios possui as seguintes características explícitas:

1. **Snapshots Locais Independentes:** `events_snapshot` e `claims_snapshot` são leituras desacopladas obtidas de dois arquivos JSONL físicos distintos;
2. **Ausência de Atomicidade Distribuída:** A operação **NÃO** constitui transação atômica distribuída ou snapshot multi-repositório consistente no tempo físico. Pode ocorrer concorrência em disco entre a leitura de lifecycle e a leitura de claims;
3. **Aceitação Consciente:** A v1 aceita formalmente essa semântica desacoplada, alinhada com a arquitetura geral do laboratório;
4. **Proibições:** Não introduzir transactions, locks de arquivo, retries, caches, 2PC, compensações ou tentativas de reparo automático.

---

## 12. Semântica Factual dos Claims

O estado de claims exposto no resultado é estritamente factual e derivado das propriedades de `HumanReviewClaimFactState`:

- `NO_CLAIM`: Existem exatamente zero fatos de claim registrados para o workflow;
- `SINGLE_CLAIM`: Existe exatamente um fato de claim registrado para o workflow;
- `MULTIPLE_CLAIMS`: Existem dois ou mais fatos de claim registrados para o workflow.

> [!CAUTION]
> **`sole_claim` é Cardinalidade Factual, NÃO Política Operacional.**
>
> Quando `claim_state.state == SINGLE_CLAIM`, a propriedade `sole_claim` expõe a única instância de `HumanReviewClaim` persistida no histórico.
>
> `sole_claim` **NÃO** significa:
> - Active claim (claim ativo);
> - Owner (dono);
> - Assignment (atribuição de tarefa);
> - Responsável operacional;
> - Winner (vencedor de disputa);
> - Exclusividade de atendimento;
> - Last-Claim-Wins;
> - Autorização soberana para emitir parecer humano.
>
> `SINGLE_CLAIM` representa apenas que há um único fato gravado. O laboratório não atribui autoridade ou exclusividade a essa contagem nesta v1.

---

## 13. Semântica do Conjunto Condutor

A **pending queue** dirige exclusivamente a cardinalidade e a composição do resultado:

1. **Cardinalidade 1:1 com a fila pendente:** Cada workflow presente na fila produz exatamente um `PendingHumanReviewWithClaimStateItem` no resultado;
2. **Zero claims preserva o workflow:** Um workflow pendente sem claims gera um item com `claim_state.state == NO_CLAIM`;
3. **Workflows concluídos ignorados:** Claims pertencentes a workflows que já foram concluídos (`REVIEWED`) são filtrados naturalmente e **NÃO** geram itens no resultado;
4. **Claims órfãos ignorados:** Claims associados a identificadores de workflows inexistentes na fila ativa **NÃO** geram itens no resultado;
5. **Fila vazia:** Se não houver workflows pendentes, o resultado é a tupla vazia `()`, independentemente da existência de claims em disco.

---

## 14. Ordenação

A camada de aplicação **NÃO** reordena o resultado.

A ordenação canônica é definida integralmente pela projeção pura `project_pending_human_review_queue`:
```text
(opened_at ASC, workflow_id ASC)
```

O caso de uso deve preservar de forma idêntica e estável a sequência gerada pela projeção de fila.

---

## 15. Comportamento Fail-Closed

O caso de uso opera sob a política estrita de falha fechada:

1. **Sem mascaramento:** Nenhuma exceção de I/O, persistência ou integridade é capturada por blocos genéricos `except Exception`;
2. **Sem retries ou fallbacks:** Falhas em qualquer repositório interrompem a execução imediatamente;
3. **Sem resultados parciais:**
   - Se a leitura de `workflow_lifecycle_repository` falhar, `claim_repository` sequer deve ser consultado;
   - Se a leitura de `workflow_lifecycle_repository` tiver sucesso, mas a leitura de `claim_repository` falhar, nenhum resultado parcial de workflows deve ser emitido.

---

## 16. Validação Defensiva do Read-Model Composto

O construtor e o `__post_init__` de `PendingHumanReviewWithClaimStateItem` devem validar:

1. `workflow`: deve ser obrigatoriamente instância de `GovernanceWorkflow` (`TypeError` para outros tipos ou booleanos);
2. `claim_state`: deve ser obrigatoriamente instância de `HumanReviewClaimState` (`TypeError` para outros tipos ou booleanos);
3. `workflow_id`: comparação exata `self.workflow.workflow_id == self.claim_state.workflow_id` (`ValueError` em caso de divergência);
4. Imutabilidade estrita via `frozen=True` e `slots=True`.

---

## 17. Casos de Teste Planejados

Os testes devem ser organizados em testes unitários com repositórios em memória / dublês e testes de integração vertical com JSONL real em disco:

### 17.1 Testes Unitários de Aplicação (`tests/test_pending_human_reviews_with_claim_state_use_case.py`)

1. **Validação defensiva do item composto:** Rejeição de tipos não-`GovernanceWorkflow`, não-`HumanReviewClaimState` e verificação da invariante relacional de `workflow_id` idêntico;
2. **Fila pendente vazia:** Nenhum workflow pendente retorna `()` mesmo se houver claims no repositório;
3. **Composição com zero claims:** Workflow pendente associado a `NO_CLAIM` (`is_unclaimed=True`, `sole_claim=None`);
4. **Composição com exatamente um claim:** Workflow pendente associado a `SINGLE_CLAIM` (`has_claims=True`, `sole_claim=claim`);
5. **Composição com múltiplos claims:** Workflow pendente associado a `MULTIPLE_CLAIMS` (`has_multiple_claims=True`, `sole_claim=None`);
6. **Múltiplos workflows preservando ordem canônica:** Workflows abertos em instantes distintos mantêm a sequência FIFO `(opened_at ASC, workflow_id ASC)`;
7. **Isolamento de claims de workflows concluídos:** Workflows em estado `REVIEWED` presentes no lifecycle não aparecem na fila, e seus respectivos claims não vazam para o resultado;
8. **Isolamento de claims órfãos:** Claims com `workflow_id` desconhecido ou inexistente na fila pendente são ignorados;
9. **Single-read invariant (Anti-N+1):** O caso de uso deve chamar `list_all_events()` exatamente uma vez e `list_all()` exatamente uma vez por execução;
10. **Propagação fail-closed de lifecycle:** Falha de persistência no repositório de lifecycle propaga imediatamente sem chamar o repositório de claims;
11. **Propagação fail-closed de claims:** Falha de persistência no repositório de claims propaga imediatamente sem retornar workflows parciais;
12. **Invariante conceitual de `sole_claim`:** Demonstração de que a presença de `sole_claim` não altera o status do workflow nem define titularidade.

### 17.2 Testes de Integração Vertical Pós-Restart (`tests/test_pending_human_reviews_with_claim_state_use_case_integration.py`)

1. **Ciclo completo com JSONL real pós-restart:**
   - Persistir abertura de workflows via `JsonlWorkflowLifecycleRepository`;
   - Persistir múltiplos claims via `JsonlHumanReviewClaimRepository`;
   - Persistir conclusão de um dos workflows via `append_concluded`;
   - Reinicializar o processo criando novas instâncias dos repositórios sobre os mesmos arquivos físicos em disco;
   - Executar `ListPendingHumanReviewsWithClaimStateUseCase`;
   - Comprovar que o workflow concluído deixou de constar na lista e que os workflows pendentes restantes exibem fielmente seus estados factuais de claim (`NO_CLAIM`, `SINGLE_CLAIM`, `MULTIPLE_CLAIMS`).

---

## 18. Invariantes Constitucionais

Esta especificação subordina-se às seguintes invariantes fundamentais:

```text
Application coordena | Domain decide | Repository preserva | Projection interpreta
```

1. **`HumanReviewClaim ≠ HumanReview`:** Assumir voluntariamente uma pendência não equivale a proferir decisão humana;
2. **`CLAIMED ≠ REVIEWED`:** O registro de um claim não altera o ciclo temporal do workflow; ele permanece estritamente em `PENDING_HUMAN_REVIEW`;
3. **`Projection factual ≠ Policy operacional`:** Descrever os fatos persistidos não cria direitos, autorizações, reservas ou autoridade operacional;
4. **`Repository ≠ Projection`:** Os repositórios preservam a ordem física dos logs; as projeções calculam o read-model determinístico em memória.

---

## 19. Critérios de Aceite

A Issue #97 será considerada aceita quando a suíte de testes demonstrar que:

1. `ListPendingHumanReviewsWithClaimStateUseCase` recebe `WorkflowLifecycleRepository` e `HumanReviewClaimRepository` por injeção de dependência no construtor;
2. `execute()` obtém um único snapshot local de cada repositório por execução (`list_all_events()` e `list_all()`);
3. A derivação de workflows pendentes delega integralmente para `project_pending_human_review_queue(events)`;
4. A derivação do estado de claims delega integralmente para `project_human_review_claim_state(workflow_id, claims)`;
5. O método retorna uma `tuple[PendingHumanReviewWithClaimStateItem, ...]`;
6. Cada item composto satisfaz `item.workflow.workflow_id == item.claim_state.workflow_id`;
7. Todos os três estados factuais (`NO_CLAIM`, `SINGLE_CLAIM`, `MULTIPLE_CLAIMS`) são suportados e comprovados;
8. Claims pertencentes a workflows concluídos ou inexistentes na fila ativa não geram itens no resultado;
9. A ordenação canônica FIFO `(opened_at ASC, workflow_id ASC)` é preservada estritamente;
10. Erros de persistência e corrupção física propagam de forma *fail-closed*;
11. Teste vertical de integração comprova o funcionamento sobre arquivos JSONL reais pós-restart de processo;
12. Regressão completa com a suíte canônica de testes aprovada (100% GREEN).

---

## 20. Estratégia de Micro-TDD Futura

A implementação deverá ocorrer em fatias atômicas e incrementais no ciclo **Red $\rightarrow$ Green $\rightarrow$ Refactor**:

- **Fatia 1 (Contrato e Validação Defensiva do Item Composto):**
  - Teste unitário para `PendingHumanReviewWithClaimStateItem` (tipos, imutabilidade, post-init validation de `workflow_id`);
  - Implementação do dataclass imutável.
- **Fatia 2 (Orquestração do Caso de Uso — Casos Básicos e Ordenação):**
  - Testes unitários para `ListPendingHumanReviewsWithClaimStateUseCase` cobrindo fila vazia, zero claims (`NO_CLAIM`), um claim (`SINGLE_CLAIM`) e múltiplos claims (`MULTIPLE_CLAIMS`);
  - Implementação do caso de uso com injeção de dependência e delegação às projeções existentes.
- **Fatia 3 (Isolamento de Escopo e Invariante de Snapshot Único):**
  - Testes comprovando que claims de workflows fora da fila são ignorados e que cada repositório é lido exatamente uma vez;
  - Testes de propagação *fail-closed*.
- **Fatia 4 (Integração Vertical Real Pós-Restart):**
  - Teste vertical em arquivo temporário JSONL validando sobrevivência a reinicializações.

---

## 21. Riscos e Limitações Explícitas

1. **Janela de Consistência entre Leituras:** Por não haver transação distribuída entre os dois arquivos JSONL, eventos de claim gravados exatamente durante a execução podem ser observados ou omitidos. Essa limitação é aceita conscientemente e não oferece risco de corrupção física;
2. **Inexistência de Lock Concorrente:** Múltiplos especialistas continuam podendo registrar claims simultâneos para o mesmo workflow. A consulta expõe essa multiplicidade através de `MULTIPLE_CLAIMS`, sem resolver a concorrência na camada de leitura;
3. **Desacoplamento entre Claimant e Reviewer:** A emissão de parecer humano via `RecordHumanDecisionUseCase` continua desacoplada do estado de claim, preservando a independência do ciclo de deliberação.

---

## 22. Definition of Done

A Issue #97 será considerada concluída somente quando:

- [ ] SPEC 0097 revisada e aprovada;
- [ ] Implementação de código e testes concluída via micro-TDD na branch `feature/issue-97-pending-human-review-queue-with-claim-state`;
- [ ] Suíte completa de testes executada localmente via `python -m unittest discover -s tests -v` e 100% aprovada (GREEN);
- [ ] Verificação de formato e whitespace via `git diff --check` sem pendências;
- [ ] Auditoria humana de diff garantindo ausência de escopo não autorizado;
- [ ] PR funcional aberto com CI GREEN e merged na `main`;
- [ ] PR documental de closeout aprovado com `PROJECT_COMPASS.md` e status da SPEC atualizado para `Concluída e Integrada na main`;
- [ ] Branch `main` local sincronizada com `origin/main` e working tree limpo.
