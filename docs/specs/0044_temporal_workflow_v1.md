# SPEC 0044 — Workflow Temporal v1 — Ciclo imutável de revisão humana

> Especificação técnica da primeira camada de ciclo de vida temporal de governança
> e transição determinística entre recomendação do sistema e decisão humana no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0044` |
| Status | `Concluída` |
| Issue relacionada | `#44` |
| PR relacionado | `#45` |
| Commit de merge | `4127f09` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-18` |
| Data de conclusão | `2026-08-18` |
| Última atualização | `2026-08-18` |

## 1. Contexto

O Agent Lab Pascoal possui atualmente um pipeline determinístico e auditável que abrange:

- extração de evidências via regras e LLM estruturada;
- geração de recomendações determinísticas `DecisionRecommendation` (`APPROVE`, `REVIEW`, `REJECT`);
- identidade verificável do especialista humano `VerifiedSpecialistIdentity`;
- deliberação humana final estruturada `HumanReview` (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`);
- correlação atômica em memória de revisão e auditoria `record_human_review` -> `HumanReviewResult`;
- persistência append-only durável em JSONL via `JsonlAuditRepository` com `schema_version = 1`.

O baseline de entrada confirmado deste incremento foi de 136 testes e o baseline final após conclusão é:

```text
Ran 152 tests
OK
```

O runner oficial permanece:

```powershell
python -m unittest discover -s tests -v
```

A limitação estrutural anterior era a **atemporalidade do ciclo de vida**.
A recomendação gerada pelo sistema é um parecer instantâneo e estático. A deliberação humana é registrada no momento em que é finalizada. Não existia nenhuma entidade no domínio que representasse o material **em trânsito**, aguardando decisão humana, nem que registrasse o instante de abertura do processo ou calculasse a duração do ciclo de revisão humana (`review_lead_time`).

À época da abertura desta SPEC, a próxima âncora arquitetural definida no `PROJECT_COMPASS.md` era **Workflow Temporal**.

## 2. Problema, evidências e impacto

### Problema

O sistema anterior operava por fatos instantâneos e desconexos no tempo:
- `DecisionRecommendation` não sabe quando foi gerada;
- não havia representação para o estado intermediário *"aguardando revisão do especialista"*;
- o sistema não conseguia calcular o tempo total do ciclo de revisão até a deliberação humana (`review_lead_time = review.reviewed_at - workflow.opened_at`);
- não havia validação temporal garantindo que a decisão humana não tivesse sido tomada antes da própria abertura do workflow;
- não havia um contrato de ciclo de vida que impedisse conclusões repetidas ou estados inconsistentes.

### Evidências

1. `DecisionRecommendation` em `src/agent_lab/decision.py` não contém campos temporais nem identificador de processo;
2. `HumanReview` em `src/agent_lab/human_review.py` valida `reviewer_identity.verified_at <= reviewed_at`, mas não possuía vínculo cronológico com a abertura do workflow;
3. `record_human_review` cria `HumanReviewResult` em uma única invocação pontual, sem passagem por um estado prévio;
4. A suíte inicial de 136 testes não possuía nenhuma asserção sobre duração total do ciclo de revisão ou estados de ciclo de vida pendente.

### Impacto

- Impossibilidade de medir métricas operacionais de governança (duração total do ciclo de revisão humana);
- Falta de modelo formal para futuras integrações (onde filas e interfaces consumirão itens pendentes);
- Risco de aceitar revisões com timestamps incoerentes em relação à abertura do workflow;
- Ausência de barreira explícita contra transições arbitrárias de status no domínio.

## 3. Objetivo

Introduzir o contrato puro, síncrono e imutável `GovernanceWorkflow` e a função pura canônica `conclude_governance_workflow`, representando a menor entrega vertical testável para o ciclo de vida temporal de um item de governança:

1. Iniciar o processo no estado `PENDING_HUMAN_REVIEW` a partir de uma `DecisionRecommendation` e um timestamp timezone-aware `opened_at`;
2. Prover propriedades derivadas (`material_id`, `status`, `closed_at`, `review_lead_time`) para eliminar qualquer duplicação ou descompasso de estado;
3. Fornecer a função pura canônica `conclude_governance_workflow` que receba o workflow anterior e um `HumanReview` válido, valide a coerência do material, a coerência do parecer e a ordem cronológica (`opened_at <= reviewed_at`), retornando uma nova instância imutável em estado `REVIEWED`;
4. Garantir que `__post_init__` barre sumariamente qualquer tentativa de instanciar estados inválidos;
5. Preservar 100% dos contratos e persistência existentes (`HumanReview`, `AuditEvent`, `schema_version = 1`, `JsonlAuditRepository`), sem efeitos colaterais.

## 4. Decisões arquiteturais deliberadas

As seguintes decisões foram previamente analisadas e aprovadas para a v1:

1. **`DecisionRecommendation` NÃO recebe `recommended_at`:** `DecisionRecommendation` permanece atemporal, pura e determinística. O tempo pertence ao ciclo de vida (`GovernanceWorkflow`).
2. **`GovernanceWorkflow` é a âncora do tempo:** O contrato agrega `workflow_id`, `recommendation`, `opened_at` e `review: HumanReview | None`.
3. **`material_id` é propriedade derivada:** Para garantir fonte única da verdade, `GovernanceWorkflow.material_id` é uma `@property` que expõe `recommendation.material_id`, sem ser parâmetro independente de construtor.
4. **`status` é derivado, não armazenado:**
   - `review is None` -> `WorkflowStatus.PENDING_HUMAN_REVIEW`
   - `review is not None` -> `WorkflowStatus.REVIEWED`
5. **`closed_at` é derivado:** Retorna `review.reviewed_at` quando `review` existir, ou `None`.
6. **`review_lead_time` é derivado:** Retorna `timedelta = review.reviewed_at - opened_at` (medindo o tempo total do ciclo de revisão) quando `review` existir, ou `None`.
7. **Imutabilidade estrita:** `GovernanceWorkflow` é uma dataclass congelada (`frozen=True`, `slots=True`).
8. **Blindagem defensiva no `__post_init__`:** Impede criação de instâncias com strings em branco, timestamps naive, descompasso de material ou recomendação, ou violação temporal `reviewed_at < opened_at`.
9. **Transição exclusivamente por função pura canônica:** Disponibilização da função pura `conclude_governance_workflow(workflow, review)` que valida o estado pendente, rejeita conclusão de workflow já finalizado e retorna uma nova instância imutável. Não criar método de instância `conclude()` para evitar duplicação de API.
10. **`REQUEST_CORRECTION` encerra o ciclo como `REVIEWED`:** A solicitação de correção conclui o ciclo de análise atual. Ciclos posteriores de re-submissão e reanálise ficam explicitamente para futuras versões.
11. **Não criar `WORKFLOW_STARTED` na auditoria:** Não introduzir novos tipos de evento de auditoria nesta v1.
12. **Não alterar `AuditEvent`:** Manter o contrato de auditoria inalterado.
13. **Não alterar `schema_version = 1`:** Manter a serialização JSONL estável e compatível.
14. **Não criar persistência própria para o workflow:** A v1 é um modelo puramente em memória.
15. **Não usar `datetime.now()` implicitamente:** Todos os timestamps devem ser passados explicitamente com timezone, preservando o determinismo e a testabilidade.
16. **Volatilidade temporal deliberada na v1:** O cálculo do lead time e o tracking do workflow residem em memória no domínio; a persistência auditável em disco preserva o `AuditEvent` gerado pela deliberação humana.

## 5. Escopo

### Incluído

- Criação do módulo `src/agent_lab/workflow.py`;
- Enum `WorkflowStatus` (`PENDING_HUMAN_REVIEW`, `REVIEWED`);
- Contrato imutável `GovernanceWorkflow`;
- Propriedades derivadas: `material_id`, `status`, `closed_at`, `review_lead_time`;
- Validações defensivas completas em `__post_init__`;
- Função pura canônica de conclusão `conclude_governance_workflow`;
- Validação temporal estrita `opened_at <= review.reviewed_at`;
- Validação de coerência `review.material_id == workflow.material_id`;
- Validação de coerência do parecer `review.system_recommendation == workflow.recommendation.decision`;
- Rejeição de transição em workflow já concluído;
- Testes unitários do workflow em `tests/test_workflow.py`;
- Testes de integração em `tests/test_workflow_integration.py`;
- Regressão integral de toda a suíte de testes (152 testes GREEN).

### Fora do escopo

- Método de instância redundante `GovernanceWorkflow.conclude()`;
- Medição separada de tempo de fila e tempo de análise efetiva (exigiria timestamps adicionais de claim/atribuição);
- Identificador forte único por recomendação (`recommendation_id`);
- Filas operacionais (in-memory, Celery, SQS, RabbitMQ);
- Schedulers, timers, cron ou execução periódica;
- SLAs com alertas de atraso ou timeout automático;
- Notificações (e-mail, webhook, mensageria);
- Banco de dados relacional ou NoSQL;
- Repositório persistente de workflow em disco;
- Event sourcing completo ou novo schema de auditoria;
- Autenticação e gestão de senhas/tokens;
- Autorização, papéis e RBAC;
- API web (HTTP/REST/FastAPI) e interface gráfica;
- Múltiplos ciclos de workflow ou re-submissão de correções;
- Integração ou injeção automática em ERP;
- Modificações em `DecisionRecommendation`, `AuditEvent`, `audit_serialization.py` ou `audit_repository.py`.

## 6. Responsabilidade humana e limites do agente

- O sistema emite recomendações determinísticas através de `DecisionRecommendation`.
- A criação de um `GovernanceWorkflow` registra formalmente que um material está aguardando revisão humana (`PENDING_HUMAN_REVIEW`).
- O sistema **jamais** transita o workflow para `REVIEWED` de forma automática.
- A transição para `REVIEWED` requer obrigatoriamente a submissão de um `HumanReview` com `VerifiedSpecialistIdentity` válida através de `conclude_governance_workflow`.
- As invariantes `requires_human_decision = True` e a separação estrita entre recomendação da IA e decisão do especialista permanecem invioláveis.

## 7. Invariantes

1. **A recomendação da IA nunca é uma decisão humana:** O workflow não pode ser concluído sem um `HumanReview`.
2. **`requires_human_decision` permanece `True`:** A recomendação encapsulada deve exigir decisão humana.
3. **Imutabilidade:** Instâncias de `GovernanceWorkflow` são estritamente congeladas (`frozen=True`).
4. **Fonte única de verdade para `material_id`:** `GovernanceWorkflow.material_id` deriva exclusivamente de `recommendation.material_id`.
5. **Consistência do material:** Um `HumanReview` só pode concluir um workflow se `review.material_id == workflow.material_id`.
6. **Consistência e coerência do parecer:** Um `HumanReview` só pode concluir um workflow se `review.system_recommendation == workflow.recommendation.decision`. (Garante coerência semântica com o parecer do sistema, sem constituir identidade de instância).
7. **Consistência cronológica do workflow:** `workflow.opened_at <= review.reviewed_at`. Decisões humanas retroativas em relação à abertura do workflow são proibidas.
8. **Consistência cronológica da identidade:** `reviewer_identity.verified_at <= review.reviewed_at` (invariante independente garantida por `HumanReview`, sem exigência de relação temporal com `workflow.opened_at`).
9. **Lead time não-negativo:** Quando concluído, `workflow.review_lead_time >= timedelta(0)`.
10. **Timestamps timezone-aware:** `opened_at` deve obrigatoriamente conter informação de fuso horário (`tzinfo` válido).
11. **Bloqueio de conclusão dupla:** Um workflow que já possua `review` (status `REVIEWED`) não pode ser concluído novamente.
12. **Não-sobrescrita:** A recomendação original contida em `workflow.recommendation` permanece preservada e inalterada após a conclusão do ciclo.

## 8. Requisitos

### Requisitos funcionais

- `RF-01` — Deve existir um enum `WorkflowStatus` com os valores `PENDING_HUMAN_REVIEW` e `REVIEWED`.
- `RF-02` — Deve existir um contrato imutável `GovernanceWorkflow` contendo `workflow_id: str`, `recommendation: DecisionRecommendation`, `opened_at: datetime` e `review: HumanReview | None = None`.
- `RF-03` — `GovernanceWorkflow.material_id` deve ser uma propriedade derivada que retorna `self.recommendation.material_id`.
- `RF-04` — `GovernanceWorkflow.status` deve ser uma propriedade derivada que retorna `WorkflowStatus.PENDING_HUMAN_REVIEW` quando `self.review is None` e `WorkflowStatus.REVIEWED` quando `self.review is not None`.
- `RF-05` — `GovernanceWorkflow.closed_at` deve ser uma propriedade derivada que retorna `self.review.reviewed_at` quando `self.review is not None`, e `None` caso contrário.
- `RF-06` — `GovernanceWorkflow.review_lead_time` deve ser uma propriedade derivada que retorna `self.review.reviewed_at - self.opened_at` (do tipo `timedelta`, representando a duração total do ciclo de revisão) quando `self.review is not None`, e `None` caso contrário.
- `RF-07` — `workflow_id` deve rejeitar strings vazias ou compostas apenas por espaços em branco.
- `RF-08` — `opened_at` deve exigir datetime com fuso horário (timezone-aware).
- `RF-09` — `recommendation` deve ser obrigatoriamente uma instância de `DecisionRecommendation`.
- `RF-10` — Quando `review` for fornecido na inicialização ou transição, deve exigir uma instância válida de `HumanReview`.
- `RF-11` — Quando `review` for fornecido, `GovernanceWorkflow.__post_init__` deve validar:
  - `review.material_id == self.recommendation.material_id`;
  - `review.system_recommendation == self.recommendation.decision` (coerência do parecer);
  - `review.reviewed_at >= self.opened_at`.
- `RF-12` — Deve existir a função pura canônica `conclude_governance_workflow(workflow: GovernanceWorkflow, review: HumanReview) -> GovernanceWorkflow` que valida que o workflow está pendente e retorna uma nova instância imutável com `review` associado.
- `RF-13` — A função `conclude_governance_workflow` deve lançar erro se executada sobre um workflow já concluído.
- `RF-14` — O desfecho `REQUEST_CORRECTION` deve ser aceito na conclusão, encerrando o ciclo atual com status `REVIEWED`.

### Requisitos de qualidade

- `RQ-01` — O contrato `GovernanceWorkflow` deve ser estritamente imutável (`frozen=True`, `slots=True`).
- `RQ-02` — A implementação deve utilizar exclusivamente a biblioteca padrão do Python (`dataclasses`, `datetime`, `enum`).
- `RQ-03` — Nenhuma chamada a `datetime.now()` deve ser realizada internamente; todos os instantes temporais devem ser fornecidos explicitamente.
- `RQ-04` — O baseline de testes existentes deve permanecer integralmente aprovado.
- `RQ-05` — Nenhuma alteração deve ser introduzida em `src/agent_lab/decision.py`, `src/agent_lab/human_review.py`, `src/agent_lab/audit.py`, `src/agent_lab/audit_serialization.py` ou `src/agent_lab/audit_repository.py`.
- `RQ-06` — O runner canônico permanece `unittest`.

## 9. Proposta técnica

### Contratos propostos

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from agent_lab.decision import DecisionRecommendation
from agent_lab.human_review import HumanReview


class WorkflowStatus(str, Enum):
    """Lifecycle state of a governance workflow."""

    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    REVIEWED = "REVIEWED"


@dataclass(frozen=True, slots=True)
class GovernanceWorkflow:
    """Immutable temporal container for a material governance review cycle."""

    workflow_id: str
    recommendation: DecisionRecommendation
    opened_at: datetime
    review: HumanReview | None = None

    def __post_init__(self) -> None:
        # 1. Validação de workflow_id
        # 2. Validação de recommendation
        # 3. Validação de opened_at timezone-aware
        # 4. Validação de review (se fornecido):
        #    - isinstance HumanReview
        #    - review.material_id == recommendation.material_id
        #    - review.system_recommendation == recommendation.decision
        #    - review.reviewed_at >= opened_at
        ...

    @property
    def material_id(self) -> str:
        return self.recommendation.material_id

    @property
    def status(self) -> WorkflowStatus:
        if self.review is None:
            return WorkflowStatus.PENDING_HUMAN_REVIEW
        return WorkflowStatus.REVIEWED

    @property
    def closed_at(self) -> datetime | None:
        if self.review is None:
            return None
        return self.review.reviewed_at

    @property
    def review_lead_time(self) -> timedelta | None:
        if self.review is None:
            return None
        return self.review.reviewed_at - self.opened_at


def conclude_governance_workflow(
    workflow: GovernanceWorkflow,
    review: HumanReview,
) -> GovernanceWorkflow:
    """Produce a new GovernanceWorkflow with the human review applied."""
    if not isinstance(workflow, GovernanceWorkflow):
        raise TypeError("workflow must be a GovernanceWorkflow")
    if workflow.review is not None:
        raise ValueError(
            f"Workflow {workflow.workflow_id} is already reviewed"
        )
    return GovernanceWorkflow(
        workflow_id=workflow.workflow_id,
        recommendation=workflow.recommendation,
        opened_at=workflow.opened_at,
        review=review,
    )
```

### Arquivos criados

```text
src/agent_lab/workflow.py                  # Novo módulo de workflow
tests/test_workflow.py                    # Testes unitários do contrato e transições
tests/test_workflow_integration.py        # Testes de integração (fluxo completo)
docs/specs/0044_temporal_workflow_v1.md   # Esta SPEC técnica
```

Arquivos que **NÃO** foram alterados:

```text
src/agent_lab/decision.py
src/agent_lab/human_review.py
src/agent_lab/audit.py
src/agent_lab/audit_serialization.py
src/agent_lab/audit_repository.py
tests/test_decision.py
tests/test_human_review.py
tests/test_audit_serialization.py
tests/test_audit_repository.py
```

## 10. Estratégia de testes e TDD

### Etapa 1 — Criação do workflow pendente (RED -> GREEN)

- **Testes criados em `tests/test_workflow.py`:**
  - Instanciação de `GovernanceWorkflow` válido em estado inicial (`review=None`);
  - `status == WorkflowStatus.PENDING_HUMAN_REVIEW`;
  - `material_id == recommendation.material_id`;
  - `closed_at is None`;
  - `review_lead_time is None`;
  - Rejeição de `workflow_id` vazio ou composto apenas por espaços;
  - Rejeição de `opened_at` naive (sem timezone);
  - Rejeição de `recommendation` inválida;
  - Imutabilidade da classe (`FrozenInstanceError`).

### Etapa 2 — Conclusão e validações de transição (RED -> GREEN)

- **Testes criados em `tests/test_workflow.py`:**
  - Conclusão com sucesso via `conclude_governance_workflow(workflow, review)`;
  - `status == WorkflowStatus.REVIEWED`;
  - `closed_at == review.reviewed_at`;
  - `review_lead_time == review.reviewed_at - opened_at`;
  - Rejeição de conclusão com `review.material_id` divergente de `recommendation.material_id`;
  - Rejeição de conclusão com `review.system_recommendation` divergente de `recommendation.decision` (descompasso de coerência do parecer);
  - Rejeição de conclusão com `review.reviewed_at < opened_at` (ordem cronológica invertida);
  - Rejeição de conclusão em workflow que já possui `review` (tentativa de conclusão dupla);
  - Conclusão com decisões `APPROVE` (e suporte estrutural a qualquer `HumanReview` válido, incluindo `REQUEST_CORRECTION`).

### Etapa 3 — Integração ponta a ponta (RED -> GREEN)

- **Testes criados em `tests/test_workflow_integration.py`:**
  - Fluxo completo:
    1. Avaliação e geração de `DecisionRecommendation`;
    2. Abertura de `GovernanceWorkflow` (`opened_at = t0`);
    3. Construção de `VerifiedSpecialistIdentity` (`verified_at = t1`);
    4. Execução de `record_human_review` gerando `HumanReviewResult` com `reviewed_at = t2`, satisfazendo as invariantes independentes `t1 <= t2` e `t0 <= t2` (sem acoplamento temporal entre `t0` e `t1`);
    5. Conclusão do workflow via `conclude_governance_workflow(workflow, result.review)`;
    6. Verificação do `review_lead_time` exato (`t2 - t0`);
    7. Persistência do `result.audit_event` em `JsonlAuditRepository` mantendo conformidade total com o repositório auditável;
    8. Comprovação de que nenhum estado de `GovernanceWorkflow` é gravado no arquivo persistido JSONL.

### Etapa 4 — Regressão completa

Execução obrigatória de toda a suíte:

```powershell
python -m unittest discover -s tests -v
```

Resultado final comprovado: 152 testes GREEN (136 anteriores + 16 novos testes entre unitários e de integração).

## 11. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Volatilidade temporal (lead time existe apenas em memória na v1) | Alta | Baixo | Documentar explicitamente a limitação; persistência do workflow fica para incremento posterior. |
| Incompatibilidade de fusos horários em timestamps | Baixa | Médio | Validação estrita de `tzinfo` em `__post_init__`; operações nativas de `datetime` em Python tratam fusos conhecidos. |
| Tentativa de reutilizar workflow concluído | Média | Médio | Função `conclude_governance_workflow` rejeita sumariamente instâncias não pendentes; classe é estritamente imutável. |
| Ausência de `recommendation_id` e semântica do parecer | Baixa | Baixo | A v1 não possui identificador único por instância de recomendação. A coerência do parecer é validada por `review.system_recommendation == recommendation.decision` e `review.material_id == recommendation.material_id`, garantindo consistência de conteúdo sem criar acoplamento de chaves na v1. |
| Escopo expandido para re-submissão de correções | Média | Alto | Delimitação explícita de que `REQUEST_CORRECTION` encerra o ciclo como `REVIEWED`. |

## 12. Versionamento e release

### Impacto SemVer

- `MINOR` — Nova funcionalidade de domínio compatível, sem quebra de contratos prévios.

### Publicação prevista

- Versão planejada: `Unreleased`
- Criação de tag: Não
- Criação de Release: Não
- Atualização do `CHANGELOG.md`: No encerramento da release

## 13. Critérios de aceite

- [x] Módulo `src/agent_lab/workflow.py` criado com `WorkflowStatus` e `GovernanceWorkflow`;
- [x] `GovernanceWorkflow` é uma dataclass estritamente imutável (`frozen=True`, `slots=True`);
- [x] `material_id` é propriedade derivada de `recommendation.material_id`;
- [x] `status` é propriedade derivada (`PENDING_HUMAN_REVIEW` quando `review is None`, `REVIEWED` quando presente);
- [x] `closed_at` é propriedade derivada (`review.reviewed_at` ou `None`);
- [x] `review_lead_time` é propriedade derivada (`review.reviewed_at - opened_at` ou `None`);
- [x] `__post_init__` valida `workflow_id` não vazio e `opened_at` timezone-aware;
- [x] `__post_init__` valida que `recommendation` é `DecisionRecommendation`;
- [x] `__post_init__` rejeita inconsistências quando `review` estiver presente:
  - `review.material_id != recommendation.material_id`;
  - `review.system_recommendation != recommendation.decision` (coerência do parecer);
  - `review.reviewed_at < opened_at`;
- [x] Função pura canônica `conclude_governance_workflow` opera retornando nova instância imutável;
- [x] Tentativa de concluir workflow já revisado é rejeitada com erro;
- [x] Ciclos com `REQUEST_CORRECTION` concluem com status `REVIEWED` (garantido estruturalmente pelo contrato genérico de `HumanReview`, sem teste unitário dedicado nesta v1);
- [x] Módulos existentes (`decision.py`, `human_review.py`, `audit.py`, `audit_serialization.py`, `audit_repository.py`) permanecem 100% inalterados;
- [x] Schema de auditoria `schema_version = 1` permanece inalterado;
- [x] Testes unitários e de integração criados e aprovados;
- [x] Suíte completa de testes (136 anteriores + 16 novos = 152 testes) passa integralmente via `python -m unittest discover -s tests -v`;
- [x] Nenhum erro em `git diff --check`.

## 14. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| 2026-08-18 | `DecisionRecommendation` permanece atemporal | Preservar pureza e determinismo da recomendação lógica; o tempo pertence ao workflow | Jk-Pascoal |
| 2026-08-18 | `material_id`, `status`, `closed_at` e `review_lead_time` são propriedades derivadas | Eliminar qualquer possibilidade de descompasso de estado ou fontes redundantes de verdade | Jk-Pascoal |
| 2026-08-18 | Workflow puro e em memória na v1 | Evitar acoplamento prematuro com filas, bancos de dados e schedulers na v1 | Jk-Pascoal |
| 2026-08-18 | Operação canônica exclusiva via função pura `conclude_governance_workflow` | API única e explícita de transição; `GovernanceWorkflow` permanece objeto imutável de estado | Jk-Pascoal |
| 2026-08-18 | `AuditEvent` e `schema_version = 1` inalterados | Garantir compatibilidade reversa total com o repositório JSONL auditável existente | Jk-Pascoal |
| 2026-08-18 | `REQUEST_CORRECTION` encerra ciclo como `REVIEWED` | Limitar o escopo da v1 a um ciclo único de revisão, adiando re-submissões para v2 | Jk-Pascoal |
