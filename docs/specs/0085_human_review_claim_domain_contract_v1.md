# SPEC 0085 — Human Review Claim Domain Contract v1 — Contrato de domínio puro e em memória para assunção de revisão humana

> Especificação técnica do contrato de domínio puro e em memória para representação
> do ato voluntário de um especialista assumir (*claim*) um workflow pendente de
> revisão humana (`HumanReviewClaim`) no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0085` |
| Status | `APPROVED` |
| Issue relacionada | `#85` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-31` |
| Última atualização | `2026-08-31` |

---

## 1. Contexto

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais PDM/BOM. O baseline atual integrado na branch `main` possui 444 testes aprovados (100% GREEN) e consolida:

- ciclo temporal de governança em memória (`GovernanceWorkflow` nos estados `PENDING_HUMAN_REVIEW` e `REVIEWED`);
- persistência append-only de eventos de ciclo de vida (`WorkflowOpened`, `WorkflowConcluded`) e trilha de auditoria desacoplada (`AuditEvent`);
- proveniência, persistência e projeção de linhagem de revisões de materiais (`MaterialRevision`);
- projeção determinística da fila de pendências (`project_pending_human_review_queue` — Issue #77);
- boundary de aplicação para consulta estruturada da fila pendente (`ListPendingHumanReviewsUseCase` — Issue #81);
- boundary de aplicação para deliberação humana (`RecordHumanDecisionUseCase` — Issue #74).

Baseline oficial verificado:

```text
Ran 444 tests in 1.268s
OK
```

Com a fila de workflows pendentes formalizada na camada de Application, a esteira evolutiva do projeto avança para a **operação de PoC do Human-in-the-Loop (HITL)**. Antes de introduzir persistência, atribuição gerencial (assignment), controle de SLA ou interfaces de usuário, o domínio precisa representar explicitamente o fato de um especialista humano assumir voluntariamente um item pendente para atendimento.

---

## 2. Problema e Justificativa

### Problema

Atualmente, o sistema conhece workflows em `PENDING_HUMAN_REVIEW` e workflows concluídos em `REVIEWED`. No entanto, inexiste no modelo de domínio qualquer representação explícita para o momento intermediário em que um especialista humano manifesta a intenção de analisar um item da fila.

Sem um contrato formal de domínio para o ato de assunção (*claim*):
1. Não é possível associar a responsabilidade operacional de atendimento a uma identidade verificada (`VerifiedSpecialistIdentity`) antes da deliberação final;
2. Há risco de acoplar indevidamente o ato de "pegar para analisar" com o ato de "deliberar/decidir" (`HumanReview`);
3. Há risco de poluir a máquina de estados do ciclo de governança (`WorkflowStatus`) com estados de fila operacional (como criar um falso status `CLAIMED`);
4. Inexiste uma operação canônica e pura que valide os invariantes temporais e de elegibilidade do item antes que ele seja trabalhado.

### Evidências no código atual

1. `src/agent_lab/workflow.py` gerencia apenas `open_governance_workflow`, `open_correction_follow_up` e `conclude_governance_workflow`;
2. `src/agent_lab/human_review.py` define `HumanReview`, que expressa a deliberação concluída (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`), mas não o ato prévio de assunção do trabalho;
3. `src/agent_lab/pending_human_reviews_use_case.py` retorna workflows brutos em `PENDING_HUMAN_REVIEW`, sem vínculo com quem está analisando o item no momento.

---

## 3. Distinções Constitucionais e Princípios Arquiteturais

A modelagem do claim de revisão humana é regida por distinções estritas de engenharia:

1. **`HumanReviewClaim != HumanReview`:**
   - `HumanReviewClaim` representa o compromisso operacional de um especialista em analisar um item.
   - `HumanReview` representa a deliberação substantiva final (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`).
   - Assumir uma tarefa **não** constitui decisão, aprovação, rejeição ou auditoria de governança.

2. **`CLAIMED != REVIEWED`:**
   - O claim **não** encerra o ciclo de governança.
   - O claim **não** é um novo estado em `WorkflowStatus`.

3. **Imutabilidade de `WorkflowStatus` após Claim:**
   - O `GovernanceWorkflow` permanece estritamente em `WorkflowStatus.PENDING_HUMAN_REVIEW` após o claim.
   - O workflow continua formalmente aguardando a deliberação humana; a assunção é um fato operacional ortogonal ao ciclo de vida do workflow.

4. **Imutabilidade do Workflow de Entrada:**
   - A operação de claim recebe uma instância de `GovernanceWorkflow` e retorna um `HumanReviewClaim`.
   - A instância de `GovernanceWorkflow` de entrada não sofre qualquer mutação interna nem tem seus campos alterados.

5. **Independência entre Claimant e Reviewer:**
   - O especialista que assume o claim (`claimant`) e o especialista que eventualmente conclui a revisão (`reviewer`) **não** precisam ser obrigatoriamente a mesma pessoa nesta v1. O domínio não impõe amarração forçada entre o claim e a posterior conclusão.

6. **Responsabilidade sobre Unicidade Global e Concorrência:**
   - Esta Issue **não** garante unicidade global de claim ativo no sistema.
   - Uma futura Projection poderá interpretar ou detectar claims ativos a partir de fatos persistidos, mas **Projection interpreta e não faz enforcement**.
   - Eventual garantia de unicidade global de claim (especialmente sob múltiplos especialistas ou concorrência) dependerá de fatias futuras envolvendo orquestração da camada Application, persistência durável e mecanismos explícitos de controle de consistência/concorrência.
   - Locking, checkout e controle de concorrência permanecem rigorosamente fora da Issue #85.

7. **Caminho Canônico de Criação vs Validação Estrutural:**
   - A função pura `claim_pending_human_review(...)` é a operação canônica de domínio para criar um claim associado a um `GovernanceWorkflow`.
   - O método `HumanReviewClaim.__post_init__` valida apenas invariantes estruturais intrínsecas ao próprio objeto (`claim_id`, `workflow_id`, `specialist`, `claimed_at`).
   - Invariantes relacionais que dependem do workflow (como elegibilidade de `workflow.status == PENDING_HUMAN_REVIEW`, ausência de revisão prévia e coerência cronológica contra `workflow.opened_at`) pertencem à função canônica `claim_pending_human_review`.
   - A instanciação direta do dataclass, isoladamente, não comprova a elegibilidade operacional do workflow.

8. **Ausência Total de I/O e Efeitos Colaterais:**
   - A operação é puramente síncrona, determinística e executada em memória (zero-I/O).
   - Não gera `AuditEvent`, não gera `WorkflowLifecycleEvent` e não acessa repositórios ou sistemas de arquivos.

---

## 4. Objetivo

Definir e implementar o contrato de domínio puro, síncrono e em memória para a assunção (*claim*) de workflows pendentes de revisão humana:

1. Criar o dataclass imutável `HumanReviewClaim` no domínio;
2. Implementar a função pura canônica `claim_pending_human_review(...)`;
3. Validar defensivamente todos os invariantes temporais, de identidade e de elegibilidade do workflow;
4. Assegurar que nenhuma persistência, evento de auditoria, mutação de workflow ou use case seja introduzido nesta fatia;
5. Fornecer cobertura abrangente de testes unitários com `unittest` cobrindo cenários positivos, negativos e boundaries.

---

## 5. Escopo

### Incluído

- Criação do módulo de domínio `src/agent_lab/human_review_claim.py`;
- Definição do dataclass congelado `HumanReviewClaim`:
  - `claim_id: str`
  - `workflow_id: str`
  - `specialist: VerifiedSpecialistIdentity`
  - `claimed_at: datetime`
- Definição da função pura canônica de domínio:
  ```python
  def claim_pending_human_review(
      workflow: GovernanceWorkflow,
      *,
      claim_id: str,
      specialist: VerifiedSpecialistIdentity,
      claimed_at: datetime,
  ) -> HumanReviewClaim:
      ...
  ```
- Validações defensivas estritas:
  - `workflow` deve ser instância válida de `GovernanceWorkflow`;
  - `workflow.status` deve ser obrigatoriamente `WorkflowStatus.PENDING_HUMAN_REVIEW`;
  - `workflow.review` deve ser obrigatoriamente `None` (fail-closed diante de inconsistências de estado);
  - `claim_id` deve ser string não-vazia (rejeitando strings em branco ou compostas apenas por whitespace);
  - `specialist` deve ser instância válida de `VerifiedSpecialistIdentity`;
  - `claimed_at` deve ser `datetime` timezone-aware (rejeitando datetimes ingênuos/naive);
  - `claimed_at >= workflow.opened_at` (o claim não pode ocorrer antes da abertura do workflow);
  - `specialist.verified_at <= claimed_at` (a identidade do especialista deve ter sido verificada antes ou no momento do claim);
- Exportação dos novos símbolos em `src/agent_lab/__init__.py`;
- Suíte completa de testes unitários em `tests/test_human_review_claim.py`.

### Fora do escopo

- Persistência de claims em disco ou em arquivos JSONL;
- Criação de `WorkflowClaimed` ou novos eventos de ciclo de vida (`WorkflowLifecycleEvent`);
- Criação de novos eventos de auditoria (`AuditEvent`);
- Repositórios, serializadores ou esquemas versionados para claim;
- Projeção de claims ativos (`project_active_claims` ou similar);
- Casos de uso na camada Application (`ClaimHumanReviewUseCase` ou similar);
- Garantia de unicidade concorrente ou global de claim ativo;
- Operações de `unclaim`, `release`, expiração de claim ou transferência de titularidade;
- Atribuição automática ou gerencial (*assignment / supervisor policy*);
- SLAs, prazos, tempos de fila (*queue lead time*) ou priorização de atendimento;
- Interfaces de usuário (UI/CLI/Web/API);
- Modificação de `WorkflowStatus` (a inclusão de status `CLAIMED` permanece explicitamente rejeitada).

---

## 6. Invariantes de Domínio

### Invariantes Específicas da Issue #85

1. **Elegibilidade de Workflow:** Apenas workflows com `workflow.status == WorkflowStatus.PENDING_HUMAN_REVIEW` e `workflow.review is None` podem ser objeto de claim na operação canônica `claim_pending_human_review`.
2. **Rejeição de Workflow Concluído:** Workflows com `workflow.status == WorkflowStatus.REVIEWED` ou com `workflow.review is not None` são sumariamente rejeitados com exceção explícita (`ValueError`).
3. **Identidade do Workflow:** O `claim.workflow_id` gerado é estritamente idêntico ao `workflow.workflow_id` do workflow fornecido.
4. **Identificador de Claim Válido:** O `claim_id` deve ser uma string não-vazia após remoção de espaços nas extremidades (`strip()`).
5. **Identidade Verificada Obrigatória:** O parâmetro `specialist` deve ser obrigatoriamente uma instância de `VerifiedSpecialistIdentity`.
6. **Consciência de Timezone:** O timestamp `claimed_at` deve conter informações explícitas de fuso horário (`tzinfo is not None` e `utcoffset() is not None`). Datetimes ingênuos são rejeitados com `ValueError`.
7. **Cronologia de Abertura:** O timestamp do claim não pode ser anterior à abertura do workflow (`claimed_at >= workflow.opened_at`). Igualdade temporal é permitida.
8. **Cronologia de Identidade:** A verificação da identidade do especialista não pode ser posterior ao claim (`specialist.verified_at <= claimed_at`). Igualdade temporal é permitida.
9. **Imutabilidade e Pureza:** A instância de `GovernanceWorkflow` recebida permanece inalterada. A função retorna um objeto novo e congelado `HumanReviewClaim`.
10. **Comportamento Fail-Closed:** Qualquer tipo incorreto de argumento gera `TypeError` ou `ValueError` defensivo, impedindo a criação de instâncias corrompidas ou estados indeterminados.

---

## 7. Requisitos

### Requisitos Funcionais

- `RF-01`: Fornecer a classe imutável `HumanReviewClaim` com os atributos `claim_id`, `workflow_id`, `specialist` e `claimed_at`.
- `RF-02`: Fornecer a função de domínio `claim_pending_human_review(workflow, *, claim_id, specialist, claimed_at)` que instancia `HumanReviewClaim`.
- `RF-03`: Rejeitar tentativa de claim sobre workflow cujo status seja diferente de `WorkflowStatus.PENDING_HUMAN_REVIEW`.
- `RF-04`: Rejeitar tentativa de claim sobre workflow que contenha `review is not None`.
- `RF-05`: Rejeitar `claim_id` vazio, nulo ou composto exclusivamente por whitespaces.
- `RF-06`: Rejeitar `claimed_at` ingênuo (*naive datetime* sem timezone).
- `RF-07`: Rejeitar `claimed_at` estritamente anterior ao `opened_at` do workflow.
- `RF-08`: Permitir `claimed_at` exatamente igual ao `opened_at` do workflow.
- `RF-09`: Rejeitar `specialist.verified_at` estritamente posterior ao `claimed_at`.
- `RF-10`: Permitir `specialist.verified_at` exatamente igual ao `claimed_at`.
- `RF-11`: Preservar intacta a instância original de `GovernanceWorkflow`.

### Requisitos Não-Funcionais

- `RNF-01` (Determinismo): Execução puramente em memória, síncrona e sem efeitos colaterais ou I/O.
- `RNF-02` (Imutabilidade): `HumanReviewClaim` implementado com `@dataclass(frozen=True, slots=True)`.
- `RNF-03` (Tipagem Estrita): Tipagem estrita com anotações Python 3.11 (`from __future__ import annotations`).
- `RNF-04` (Testabilidade e Rigor): Os testes devem cobrir explicitamente os cenários positivos, negativos e boundaries definidos nesta SPEC, utilizando `unittest`, e a suíte completa do projeto deve permanecer GREEN.

---

## 8. Proposta Técnica

### Modelo Conceitual

```text
┌────────────────────────────────────────────────────────┐
│ GovernanceWorkflow (em memória)                        │
│ - workflow_id: "wf-100"                                │
│ - status: PENDING_HUMAN_REVIEW                         │
│ - opened_at: 2026-08-31T09:00:00Z                      │
│ - review: None                                         │
└───────────────────────────┬────────────────────────────┘
                            │
                            │ + claim_id: "claim-01"
                            │ + specialist: VerifiedSpecialistIdentity
                            │ + claimed_at: 2026-08-31T09:05:00Z
                            ▼
           claim_pending_human_review(...)
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ HumanReviewClaim (Imutável)                            │
│ - claim_id: "claim-01"                                 │
│ - workflow_id: "wf-100"                                │
│ - specialist: VerifiedSpecialistIdentity               │
│ - claimed_at: 2026-08-31T09:05:00Z                     │
└────────────────────────────────────────────────────────┘

* O GovernanceWorkflow original permanece PENDING_HUMAN_REVIEW e inalterado.
```

### Contrato de Dados e Assinatura

```python
# src/agent_lab/human_review_claim.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus


@dataclass(frozen=True, slots=True)
class HumanReviewClaim:
    claim_id: str
    workflow_id: str
    specialist: VerifiedSpecialistIdentity
    claimed_at: datetime

    def __post_init__(self) -> None:
        # Validações estruturais intrínsecas do objeto (tipos, claim_id não-vazio, claimed_at aware, specialist.verified_at <= claimed_at)
        ...


def claim_pending_human_review(
    workflow: GovernanceWorkflow,
    *,
    claim_id: str,
    specialist: VerifiedSpecialistIdentity,
    claimed_at: datetime,
) -> HumanReviewClaim:
    # Validações relacionais com o workflow (elegibilidade PENDING_HUMAN_REVIEW, review is None, claimed_at >= workflow.opened_at)
    ...
```

### Arquivos Envolvidos

* **Novo Módulo:** `src/agent_lab/human_review_claim.py`
* **Novo Arquivo de Testes:** `tests/test_human_review_claim.py`
* **Módulo Modificado (Exportação):** `src/agent_lab/__init__.py`
* **Documentação:** `docs/specs/0085_human_review_claim_domain_contract_v1.md`

---

## 9. Estratégia de Testes (TDD)

### Testes RED Planejados (`tests/test_human_review_claim.py`)

1. **Happy Path:**
   - `test_claim_pending_human_review_success`: cria um `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW`, executa o claim com dados válidos e valida todos os campos do `HumanReviewClaim` retornado.
   - `test_claim_preserves_input_workflow_unmodified`: garante que o workflow de entrada não é mutado de forma alguma.
   - `test_claim_allows_claimed_at_equal_to_opened_at`: validação boundary de timestamp igual à abertura.
   - `test_claim_allows_claimed_at_equal_to_specialist_verified_at`: validação boundary de timestamp igual à verificação do especialista.

2. **Rejeição por Estado e Elegibilidade do Workflow:**
   - `test_claim_rejects_reviewed_workflow`: rejeição quando `workflow.status == WorkflowStatus.REVIEWED`.
   - `test_claim_rejects_workflow_with_existing_review`: rejeição defensiva quando `workflow.review is not None` mesmo que o status fosse pendente.
   - `test_claim_rejects_invalid_workflow_type`: rejeição quando `workflow` não é instância de `GovernanceWorkflow`.

3. **Rejeição por Identificadores Inválidos:**
   - `test_claim_rejects_empty_claim_id`: rejeição de string vazia `""`.
   - `test_claim_rejects_whitespace_claim_id`: rejeição de string com apenas espaços `"   "`.
   - `test_claim_rejects_non_string_claim_id`: rejeição quando `claim_id` não é string.
   - `test_claim_rejects_empty_workflow_id`: rejeição estrutural de instanciação direta com `workflow_id` vazio.

4. **Rejeição por Inconsistências de Especialista:**
   - `test_claim_rejects_invalid_specialist_type`: rejeição quando `specialist` não é `VerifiedSpecialistIdentity`.
   - `test_claim_rejects_specialist_verified_after_claim`: rejeição quando `specialist.verified_at > claimed_at`.

5. **Rejeição por Inconsistências Temporais:**
   - `test_claim_rejects_naive_claimed_at`: rejeição de datetime sem timezone.
   - `test_claim_rejects_claimed_at_before_opened_at`: rejeição quando `claimed_at < workflow.opened_at`.
   - `test_claim_rejects_invalid_claimed_at_type`: rejeição quando `claimed_at` não é `datetime`.

6. **Imutabilidade Estrutural:**
   - `test_human_review_claim_is_immutable`: valida que atribuições diretas de atributos em `HumanReviewClaim` levantam `FrozenInstanceError`.

---

## 10. Riscos e Mitigações

| Risco | Severidade | Mitigação Arquitetural |
| :--- | :--- | :--- |
| **Tentativa de adicionar status `CLAIMED` ao `WorkflowStatus`** | Alta | A SPEC proíbe categoricamente alteração em `WorkflowStatus`. O claim é modelado como entidade ortogonal ao ciclo de vida do workflow. |
| **Confusão entre Claim e Deliberação (`HumanReview`)** | Alta | `HumanReviewClaim` não possui campo de decisão (`HumanDecision`) nem de correções (`CorrectionRequest`). São contratos estanques. |
| **Acoplamento prematuro com persistência / eventos** | Média | O escopo é estritamente limitado ao domínio em memória (`src/agent_lab/human_review_claim.py`). Nenhum JSONL ou serializer é modificado. |
| **Suposição de que claimant é o único que pode revisar** | Média | A SPEC explicita que claimant e reviewer são desacoplados no modelo de domínio. |
| **Expectativa de unicidade global concorrente nesta função** | Média | A SPEC esclarece que a unicidade de claim ativo dependerá de orquestração futura de Application + persistência; a função pura valida apenas o contrato do item fornecido. |

---

## 11. Critérios de Aceitação

- [ ] SPEC 0085 aprovada antes de qualquer código de produção;
- [ ] Módulo `src/agent_lab/human_review_claim.py` criado contendo `HumanReviewClaim` e `claim_pending_human_review`;
- [ ] `HumanReviewClaim` é congelado (`frozen=True`, `slots=True`);
- [ ] `GovernanceWorkflow` permanece inalterado e seu status continua `PENDING_HUMAN_REVIEW`;
- [ ] Workflows concluídos (`REVIEWED`) ou com revisão presente são rejeitados com `ValueError`;
- [ ] `claim_id` vazio ou whitespace é rejeitado;
- [ ] `claimed_at` ingênuo (*naive*) é rejeitado;
- [ ] `claimed_at < workflow.opened_at` é rejeitado;
- [ ] `specialist.verified_at > claimed_at` é rejeitado;
- [ ] Nenhum I/O, arquivo, serializador, evento persistido ou caso de uso de aplicação é criado;
- [ ] Suíte de testes automatizados passa com 100% de aprovação no runner nativo `unittest`;
- [ ] `git diff --check` permanece limpo.
