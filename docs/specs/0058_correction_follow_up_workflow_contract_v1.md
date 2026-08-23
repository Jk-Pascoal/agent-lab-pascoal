# SPEC 0058 — Correction Follow-up Workflow Contract v1 — Vínculo causal em memória de ciclo sucessor pós-solicitação de correção

> Especificação técnica do contrato de domínio puro e em memória para abertura
> de workflows sucessores de governança originados a partir de deliberações de
> solicitação de correção (`HumanDecision.REQUEST_CORRECTION`) no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0058` |
| Status | `Implementada / Concluída` |
| Issue relacionada | `#58` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-23` |
| Última atualização | `2026-08-23` |

---

## 1. Contexto

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais PDM/BOM. O baseline atual integrado na branch `main` possui 284 testes aprovados e consolida:

- fronteira LLM estruturada e tipada com guardrail de identidade e métricas de custo;
- Evidence Engine multiorigem determinístico;
- recommendation pipeline com compulsoriedade constitucional de `requires_human_decision = True`;
- identidade verificável do especialista humano `VerifiedSpecialistIdentity`;
- deliberação humana estruturada via `HumanReview` (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`);
- persistência auditável durável append-only (`AuditEvent` com `schema_version = 1` e `JsonlAuditRepository`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow` com `opened_at`, `closed_at`, `review_lead_time`);
- persistência append-only de abertura e conclusão de ciclo de vida (`WorkflowOpened`, `WorkflowConcluded` com `schema_version = 1` e `JsonlWorkflowLifecycleRepository`);
- projeção determinística de reidratação (`rehydrate_workflow`) reconstruindo `GovernanceWorkflow` nos estados `PENDING_HUMAN_REVIEW` e `REVIEWED`;
- verificação de consistência cruzada entre as trilhas desacopladas de lifecycle e auditoria (`verify_dual_write_consistency` e `verify_repositories_consistency`).

Baseline oficial verificado:

```text
Ran 284 tests in 0.717s
OK
```

Runner oficial:

```powershell
python -m unittest discover -s tests -v
```

Na arquitetura atual, quando um especialista humano conclui uma análise com decisão `HumanDecision.REQUEST_CORRECTION`, o workflow corrente é encerrado regularmente através da função pura `conclude_governance_workflow`, assumindo o status `REVIEWED` e tornando-se imutável.

---

## 2. Problema, evidências e impacto

### Problema

Atualmente, o domínio não possui nenhum mecanismo ou contrato formal para representar o desdobramento natural de uma solicitação de correção: a abertura de um **novo ciclo de revisão (workflow sucessor)** relacionado ao workflow predecessor que requisitou a correção.

Se um operador ou sistema cliente instanciar um novo `GovernanceWorkflow` para o mesmo material após uma correção, esse novo workflow nascerá como uma instância desprovida de qualquer contexto histórico ou vínculo causal em memória (`predecessor_workflow_id = None`, `triggering_review_id = None`), impossibilitando a rastreabilidade da linhagem de revisões do material no domínio.

Além disso, inexiste uma operação canônica de domínio que valide as regras de transição para criação de um workflow sucessor, permitindo que processos inconsistentes sejam gerados (por exemplo, criar um "follow-up" a partir de um workflow que foi aprovado, rejeitado ou que sequer foi concluído).

### Evidências no código atual

1. `GovernanceWorkflow` em `src/agent_lab/workflow.py` possui apenas os campos `workflow_id`, `recommendation`, `opened_at` e `review`, sem suporte a referências de linhagem ou predecessão causal.
2. Apenas a função `conclude_governance_workflow` existe no módulo `src/agent_lab/workflow.py`; não há função especializada ou contrato para `open_correction_follow_up`.
3. Não há validação impedindo a tentativa de abertura de ciclos de follow-up a partir de workflows com deliberações `APPROVE`, `REJECT` ou em estado `PENDING_HUMAN_REVIEW`.

### Impacto

- Perda de rastreabilidade de linhagem entre ciclos sucessivos de governança do mesmo material;
- Ausência de garantias de integridade causal no domínio para processos de correção;
- Risco de criação incorreta de workflows sucessores com timestamps cronologicamente incoerentes em relação ao encerramento do predecessor;
- Risco de violação da imutabilidade do predecessor caso componentes externos tentem modificar o workflow existente em vez de instanciar um sucessor.

---

## 3. Hipótese

Um workflow sucessor pode preservar um vínculo causal mínimo e explícito em memória com o workflow que o originou, por meio dos campos opcionais `predecessor_workflow_id: str | None` e `triggering_review_id: str | None` na entidade `GovernanceWorkflow`.

Uma operação de domínio pura e canônica `open_correction_follow_up(...)` pode aplicar defensivamente todas as validações de integridade causal e temporal, retornando uma nova instância imutável de `GovernanceWorkflow` em estado `PENDING_HUMAN_REVIEW` vinculada ao predecessor, mantendo o workflow predecessor completamente intocado e em estado `REVIEWED`.

---

## 4. Objetivo

Definir e implementar o contrato de domínio puro, síncrono e em memória para a abertura de workflows sucessores decorrentes de solicitações de correção (`HumanDecision.REQUEST_CORRECTION`):

1. Estender o contrato `GovernanceWorkflow` para suportar os identificadores de linhagem causal em memória (`predecessor_workflow_id` e `triggering_review_id`);
2. Introduzir a função pura canônica de domínio `open_correction_follow_up(...)` em `src/agent_lab/workflow.py`;
3. Validar rigorosamente todos os invariantes do ciclo de follow-up (estado concluído do predecessor, decisão `REQUEST_CORRECTION`, coerência de `material_id`, unicidade de `workflow_id`, cronologia temporal `opened_at >= closed_at`);
4. Garantir que o predecessor permaneça estritamente inalterado e que o sucessor inicie em `WorkflowStatus.PENDING_HUMAN_REVIEW` com `review = None`;
5. Manter persistência totalmente fora de escopo nesta etapa, preservando todos os esquemas e repositórios existentes intactos.

---

## 5. Escopo

### Incluído

- Extensão do dataclass congelado `GovernanceWorkflow` em `src/agent_lab/workflow.py` com os campos `predecessor_workflow_id: str | None = None` e `triggering_review_id: str | None = None`;
- Validação defensiva no `__post_init__` de `GovernanceWorkflow` para garantir higienização e coerência desses campos quando presentes;
- Criação da função pura canônica `open_correction_follow_up(predecessor: GovernanceWorkflow, workflow_id: str, recommendation: DecisionRecommendation, opened_at: datetime) -> GovernanceWorkflow` em `src/agent_lab/workflow.py`;
- Validação de que `predecessor` é uma instância de `GovernanceWorkflow` em estado `REVIEWED`;
- Validação de que `predecessor.review.human_decision == HumanDecision.REQUEST_CORRECTION`;
- Rejeição de follow-up a partir de decisões `APPROVE` ou `REJECT`;
- Validação de que `workflow_id` do sucessor é não-vazio e diferente do `predecessor.workflow_id`;
- Validação de que `recommendation.material_id == predecessor.material_id`;
- Validação temporal de que `opened_at` do sucessor é timezone-aware e satisfaz `opened_at >= predecessor.closed_at`;
- Testes unitários completos do novo contrato em `tests/test_workflow.py`.

### Fora do escopo

- Persistência em disco do vínculo causal (`predecessor_workflow_id`, `triggering_review_id`);
- Alteração das entidades de evento de persistência (`WorkflowOpened`, `WorkflowConcluded`);
- Alteração do contrato de auditoria (`AuditEvent`);
- Alteração do número de versão de schema (`schema_version = 1`);
- Criação de novos tipos de evento de ciclo de vida (`WorkflowLifecycleEvent`);
- Alteração dos formatos serializados ou dos arquivos JSONL (`workflow_events.jsonl`, `audit_events.jsonl`);
- Reabertura de workflows existentes ou mutação de estado em instâncias existentes;
- Aplicação automática das correções sugeridas em `CorrectionRequest` sobre `MaterialRecord`;
- Semântica de confirmação de correção aplicada (`CORRECTION_APPLIED`);
- Versionamento formal de `MaterialRecord` ou entidades de catálogo PDM/BOM;
- Reexecução automática de regras determinísticas ou reinvocação automática de LLM;
- Filas operacionais, schedulers, cron jobs ou mensageria;
- Alertas, SLAs ou timeouts de revisão;
- Interface gráfica (UI) ou APIs HTTP/REST;
- Controle de acesso baseado em papéis (RBAC);
- Integrações diretas com sistemas ERP;
- Reconciliação automática ou transações distribuídas (2PC) para dual-write.

---

## 6. Invariantes

### Invariantes específicas da Issue #58

1. **Predecessor Concluído:** Somente um workflow com revisão humana concluída (`status == WorkflowStatus.REVIEWED` e `review is not None`) pode originar um correction follow-up.
2. **Decisão Exclusiva de Correção:** A `HumanReview` do predecessor deve obrigatoriamente possuir `human_decision == HumanDecision.REQUEST_CORRECTION`.
3. **Impossibilidade de Follow-up para Aprovação/Rejeição:** Workflows concluídos com `HumanDecision.APPROVE` ou `HumanDecision.REJECT` não podem originar correction follow-up.
4. **Imutabilidade do Predecessor:** O workflow predecessor permanece completamente imutável e inalterado após a abertura do sucessor, preservando seu `workflow_id`, `status`, `review` e histórico.
5. **Diferenciação de Identidade:** O workflow sucessor deve possuir `workflow_id` diferente do workflow predecessor (`successor.workflow_id != predecessor.workflow_id`).
6. **Coerência de Material:** O workflow sucessor deve referenciar o mesmo material do predecessor (`successor.material_id == predecessor.material_id`).
7. **Consistência Cronológica:** O timestamp `opened_at` do sucessor deve ser timezone-aware e satisfazer `successor.opened_at >= predecessor.closed_at`.
8. **Ausência Inicial de Revisão:** O workflow sucessor nasce sem deliberação humana (`successor.review is None`).
9. **Estado Inicial Pendente:** O workflow sucessor inicia obrigatoriamente em `WorkflowStatus.PENDING_HUMAN_REVIEW`.
10. **Linhagem Causal Estrita:** O vínculo causal em memória do sucessor deve apontar com exatidão para:
    - `successor.predecessor_workflow_id == predecessor.workflow_id`
    - `successor.triggering_review_id == predecessor.review.review_id`
11. **Ausência de Semântica de Aplicação Automática:** A abertura do follow-up registra unicamente que *"um novo ciclo de governança foi provocado pela solicitação de correção anterior"*. Não há garantia, validação ou semântica de que os `CorrectionRequest` foram efetivamente aplicados ao material (`CORRECTION_APPLIED` permanece fora do escopo).

### Invariantes constitucionais permanentes do Agent Lab

- **Compulsoriedade de Decisão Humana:** Todas as recomendações mantêm `requires_human_decision = True`.
- **Separação IA vs Humano:** A IA recomenda (`DecisionRecommendation`); o especialista humano decide (`HumanReview`).
- **Imutabilidade de Contratos:** Dataclasses de domínio são congeladas (`frozen=True`, `slots=True`).
- **Determinismo Temporal:** Não há uso de timestamps implícitos ou `datetime.now()` sem timezone explicitamente fornecido.

---

## 7. Responsabilidade humana e limites do agente

- A deliberação de solicitar correções (`REQUEST_CORRECTION`) é de responsabilidade estrita e exclusiva do especialista humano verificado (`VerifiedSpecialistIdentity`).
- A abertura de um follow-up (`open_correction_follow_up`) instancia um novo processo de governança que dependerá, novamente, de uma deliberação humana independente para ser concluído.
- O sistema não modifica cadastros, não aplica correções por inferência e não encerra automaticamente o novo ciclo.

---

## 8. Requisitos

### Requisitos funcionais

- `RF-01`: Permitir instanciar `GovernanceWorkflow` raiz com `predecessor_workflow_id=None` e `triggering_review_id=None` mantendo compatibilidade total retroativa.
- `RF-02`: Permitir instanciar `GovernanceWorkflow` sucessor informando `predecessor_workflow_id` e `triggering_review_id` válidos (strings não-vazias).
- `RF-03`: Fornecer a função pura canônica `open_correction_follow_up(predecessor, workflow_id, recommendation, opened_at)` que produz um novo `GovernanceWorkflow`.
- `RF-04`: Validar que `open_correction_follow_up` rejeita predecessor que ainda esteja em `PENDING_HUMAN_REVIEW` (não concluído).
- `RF-05`: Validar que `open_correction_follow_up` rejeita predecessor concluído com `HumanDecision.APPROVE` ou `HumanDecision.REJECT`.
- `RF-06`: Validar que `open_correction_follow_up` rejeita sucessor com `workflow_id` idêntico ao do predecessor.
- `RF-07`: Validar que `open_correction_follow_up` rejeita sucessor com `recommendation.material_id` divergente do `predecessor.material_id`.
- `RF-08`: Validar que `open_correction_follow_up` rejeita `opened_at` anterior ao `closed_at` do predecessor.
- `RF-09`: Assegurar que o `GovernanceWorkflow` retornado por `open_correction_follow_up` possua `status == PENDING_HUMAN_REVIEW`, `review == None`, `predecessor_workflow_id == predecessor.workflow_id` e `triggering_review_id == predecessor.review.review_id`.

### Requisitos de qualidade e não-funcionais

- `RQ-01` (Imutabilidade): Todas as entidades envolvidas permanecem congeladas e livres de mutação acidental.
- `RQ-02` (Determinismo): Todas as operações são puras, síncronas e dependentes apenas dos argumentos explicitamente passados.
- `RQ-03` (Compatibilidade): Nenhuma alteração é realizada em contratos de persistência, schemas JSONL ou auditoria existente.
- `RQ-04` (Testabilidade): 100% dos fluxos válidos e exceções defensivas cobertos por testes unitários com o framework nativo `unittest`.
- `RQ-05` (Tipagem estrita): Tipagem completa com anotações Python 3.11 (`from __future__ import annotations`).

---

## 9. Proposta técnica

### Visão geral e modelo conceitual

```text
Workflow A (predecessor)
[status: PENDING_HUMAN_REVIEW]
          │
          ▼ conclude_governance_workflow(workflow_A, review_A)
            [human_decision: REQUEST_CORRECTION]
[status: REVIEWED] (imutável)
          │
          ▼ open_correction_follow_up(workflow_A, workflow_id="wf-B", recommendation=rec_B, opened_at=t_B)
Workflow B (successor)
[status: PENDING_HUMAN_REVIEW]
[predecessor_workflow_id: "wf-A"]
[triggering_review_id: "rev-A"]
[review: None]
```

### Contrato de dados e assinatura

```python
@dataclass(frozen=True, slots=True)
class GovernanceWorkflow:
    workflow_id: str
    recommendation: DecisionRecommendation
    opened_at: datetime
    review: HumanReview | None = None
    predecessor_workflow_id: str | None = None
    triggering_review_id: str | None = None
    ...

def open_correction_follow_up(
    predecessor: GovernanceWorkflow,
    *,
    workflow_id: str,
    recommendation: DecisionRecommendation,
    opened_at: datetime,
) -> GovernanceWorkflow:
    ...
```

### Arquivos previstos

- `src/agent_lab/workflow.py` — extensão de `GovernanceWorkflow` e criação de `open_correction_follow_up`;
- `tests/test_workflow.py` — suíte de testes unitários do novo contrato e das validações defensivas;
- `docs/specs/0058_correction_follow_up_workflow_contract_v1.md` — esta especificação técnica.

---

## 10. Estratégia de testes e TDD

### Fase 1: Micro-TDD RED (Escopo exclusivo desta etapa)

Criar o primeiro teste representativo em `tests/test_workflow.py` cobrindo o happy path mínimo:
- Construir workflow predecessor;
- Concluir predecessor com `HumanDecision.REQUEST_CORRECTION` e `CorrectionRequest`;
- Executar `open_correction_follow_up(...)`;
- Verificar que o successor possui `workflow_id` novo, mesmo `material_id`, `status == PENDING_HUMAN_REVIEW`, `predecessor_workflow_id` e `triggering_review_id` corretos;
- Verificar que o predecessor permaneceu `REVIEWED` e inalterado.

O teste falhará demonstrando a ausência do contrato esperado (`AttributeError` no módulo `workflow`).

### Fase 2: Implementação GREEN (Etapa subsequente)

Implementar a menor modificação suficiente em `src/agent_lab/workflow.py` para tornar o teste verde.

### Fase 3: Casos de borda e rejeições defensivas (GREEN)

Adicionar testes para cada invariante e violação de regra de negócio:
- Rejeição de predecessor pendente;
- Rejeição de predecessor com `APPROVE` / `REJECT`;
- Rejeição de `workflow_id` idêntico;
- Rejeição de `material_id` divergente;
- Rejeição de `opened_at` anterior a `closed_at`;
- Rejeição de argumentos inválidos / tipos incorretos.

### Fase 4: Regressão total

Executar toda a suíte de testes do projeto via `unittest`.

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
| Confusão entre sucessor em memória e persistência | Média | Baixo | Deixar explicitado na SPEC e nos testes que a persistência do vínculo causal não faz parte da v1 da Issue #58. |
| Violação acidental de retrocompatibilidade de `GovernanceWorkflow` | Baixa | Médio | Definir valores default (`None`) para os novos campos opcionais, preservando todas as instanciações existentes. |
| Incoerência temporal entre abertura e encerramento | Baixa | Alto | Validação defensiva explícita `opened_at >= predecessor.closed_at`. |

---

## 13. Plano de reversão

Por tratar-se de alteração puramente em código de domínio síncrono e sem modificações em schemas persistidos em disco:
1. Reverter o commit correspondente via `git revert`;
2. Executar a suíte de testes para validar o retorno ao baseline de 284 testes GREEN.

---

## 14. Versionamento e release

### Impacto SemVer

- `MINOR`: Adição de nova capacidade ao modelo de domínio (`open_correction_follow_up` e campos opcionais em `GovernanceWorkflow`), preservando total retrocompatibilidade com a API anterior.

---

## 15. Critérios de aceite

- [x] SPEC 0058 criada e documentada;
- [x] Primeiro teste micro-TDD RED adicionado em `tests/test_workflow.py` demonstrando a necessidade do contrato;
- [x] Implementação de `GovernanceWorkflow` com suporte a `predecessor_workflow_id` e `triggering_review_id`;
- [x] Implementação da função `open_correction_follow_up` em `src/agent_lab/workflow.py`;
- [x] Invariantes funcionais previstas na SPEC cobertas pelo conjunto de testes unitários da Issue #58;
- [x] Suíte completa de testes aprovada sem regressões;
- [x] Nenhum item fora de escopo (persistência, eventos, JSONL) modificado.

---

## 16. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| 2026-08-23 | Adotar modelo de sucessão de workflows em vez de reabertura | Preservar a imutabilidade estrita e a auditabilidade de ciclos encerrados. | `Jk-Pascoal` |
| 2026-08-23 | Restringir o escopo da Issue #58 ao contrato puro em memória | Manter entregas verticais pequenas, seguras e testáveis antes de avançar para persistência. | `Jk-Pascoal` |

---

## 17. Evidências de fechamento

A implementação da SPEC 0058 foi construída incrementalmente por micro-TDD, com ciclos RED → GREEN para as invariantes funcionais e um teste positivo final de boundary para proteger a igualdade temporal permitida pelo contrato:

- **Baseline de entrada (`main`):** 284 testes GREEN.
- **Baseline final da branch:** 291 testes GREEN.
- **Delta:** +7 testes.
- **Comando oficial:** `python -m unittest discover -s tests`
- **Resultado:** `Ran 291 tests in 0.523s — OK` (0 failures, 0 errors, 0 skipped).
- **Quality gate:** `git diff --check` limpo.

### Testes introduzidos pela Issue #58 (`tests/test_workflow.py`)

1. `test_open_correction_follow_up_creates_pending_successor_linked_to_predecessor` — Happy path mínimo do ciclo de sucessão causal;
2. `test_open_correction_follow_up_rejects_pending_predecessor` — Rejeição de predecessor em estado `PENDING_HUMAN_REVIEW`;
3. `test_open_correction_follow_up_rejects_non_correction_decisions` — Rejeição de predecessor com deliberações `APPROVE` e `REJECT`;
4. `test_open_correction_follow_up_rejects_predecessor_workflow_id_reuse` — Rejeição de reutilização do `workflow_id` do predecessor;
5. `test_open_correction_follow_up_rejects_material_id_mismatch` — Rejeição de descontinuidade do objeto de governança (`material_id` divergente);
6. `test_open_correction_follow_up_rejects_opened_at_before_predecessor_closed_at` — Rejeição de timestamps cronologicamente anteriores ao fechamento do predecessor;
7. `test_open_correction_follow_up_allows_opened_at_equal_to_predecessor_closed_at` — Validação positiva de boundary para `opened_at == predecessor.closed_at`.

### Resumo da cobertura funcional

Os 7 novos métodos de teste cobrem coletivamente o contrato de sucessão causal e as invariantes da SPEC:
- Predecessor precisa estar revisado (`WorkflowStatus.REVIEWED`);
- Decisão humana precisa ser `HumanDecision.REQUEST_CORRECTION`;
- `APPROVE` e `REJECT` não originam correction follow-up;
- Predecessor permanece imutável e inalterado;
- Successor usa novo `workflow_id` (`successor.workflow_id != predecessor.workflow_id`);
- Successor mantém o mesmo `material_id` (`successor.material_id == predecessor.material_id`);
- `successor.opened_at >= predecessor.closed_at` (com igualdade temporal permitida);
- Successor nasce com `review = None` e status `WorkflowStatus.PENDING_HUMAN_REVIEW`;
- `predecessor_workflow_id` preserva vínculo com o predecessor;
- `triggering_review_id` preserva vínculo com a review causadora.

### Preservação fora de escopo

Permanece estritamente fora do escopo desta entrega:
- `CORRECTION_APPLIED` (semântica ou confirmação de correção aplicada);
- Persistência da lineage causal em disco;
- Alterações em `WorkflowOpened` ou `WorkflowConcluded`;
- Serializadores (`workflow_serialization.py`, `audit_serialization.py`);
- Repositórios (`workflow_repository.py`, `audit_repository.py`);
- Nenhum contrato de `schema_version` foi modificado;
- Arquivos JSONL (`workflow_events.jsonl`, `audit_events.jsonl`);
- Auditoria (`AuditEvent`, `JsonlAuditRepository`);
- Verificação de consistência e dual-write (`consistency.py`).
