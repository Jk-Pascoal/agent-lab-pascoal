# SPEC 0052 — Workflow Conclusion Persistence v1 — Conclusão durável e reidratação de workflow revisado

> Especificação técnica da persistência append-only do evento de conclusão de
> workflow (`WorkflowConcluded`), serialização versionada com round-trip integral de `HumanReview`,
> validação de sequência de ciclo de vida (`Opened → Concluded`) e reidratação determinística
> de `GovernanceWorkflow` nos estados `PENDING_HUMAN_REVIEW` e `REVIEWED` no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0052` |
| Status | `Proposta` |
| Issue relacionada | `#52` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-21` |
| Última atualização | `2026-08-21` |

## 1. Contexto

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais PDM/BOM. O baseline atual versionado (`v0.1.0 — Governed Agent Workflow Baseline`) integra uma linha de base fundacional composta por:

- extração determinística de evidências via regras e LLM estruturada com guardrail de identidade (`EvidenceEngine`);
- geração de recomendações determinísticas `DecisionRecommendation` (`APPROVE`, `REVIEW`, `REJECT`) com compulsoriedade de `requires_human_decision = True`;
- identidade verificável do especialista humano `VerifiedSpecialistIdentity`;
- deliberação humana estruturada via `HumanReview` (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`);
- correlação atômica em memória de revisão e auditoria (`HumanReviewResult`);
- persistência auditável durável append-only (`AuditEvent` com `schema_version = 1` e `JsonlAuditRepository`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow` com transição canônica pura via `conclude_governance_workflow`);
- persistência append-only de abertura de workflow (`WorkflowOpened` com `schema_version = 1` e `JsonlWorkflowLifecycleRepository`, introduzida na Issue #47 / SPEC 0047);
- projeção pura de reidratação pendente (`rehydrate_pending_workflow`).

O baseline de entrada deste incremento está rigorosamente verificado:

```text
Ran 206 tests
OK
```

O ambiente e runner oficiais permanecem:
- **Linguagem:** Python 3.11
- **Runner oficial:** `python -m unittest discover -s tests -v`

Embora a persistência de abertura (`WorkflowOpened`) tenha resolvido a sobrevivência do estado `PENDING_HUMAN_REVIEW` a reinicializações de processo, o fechamento do ciclo de governança (`conclude_governance_workflow`) continua existindo **exclusivamente em memória volátil**.

Esta SPEC estabelece a formalização técnica para a Issue #52, implementando o evento de domínio mínimo `WorkflowConcluded`, sua serialização versionada com round-trip integral de `HumanReview`, a evolução do `WorkflowLifecycleRepository` para persistir e consultar conclusões com regras rígidas de integridade de sequência (`Opened → Concluded`), e a projeção pura capaz de reconstituir workflows tanto no estado `PENDING_HUMAN_REVIEW` quanto no estado `REVIEWED`.

---

## 2. Problema, evidências e impacto

### Problema

Quando um workflow é aberto (`WorkflowOpened`), o evento é gravado duravelmente no log de ciclo de vida em disco. Quando o especialista humano conclui a revisão através de `conclude_governance_workflow`, a instância em memória de `GovernanceWorkflow` passa ao estado `REVIEWED`, e um evento de auditoria `AuditEvent` é gravado no repositório de auditoria desacoplado.

Contudo, **o fato da conclusão do workflow não é persistido no log de ciclo de vida (`WorkflowLifecycleRepository`)**.

Como consequência, após o restart da aplicação ou encerramento do processo:
1. O repositório de ciclo de vida contém unicamente o registro de `WorkflowOpened`.
2. A projeção `rehydrate_pending_workflow` restaura o workflow como `PENDING_HUMAN_REVIEW`.
3. Um workflow que já havia sido revisado e finalizado pelo especialista é incorretamente reidratado como pendente, expondo o item novamente para deliberação ou gerando inconsistências no controle operacional.
4. Os detalhes da decisão humana (`HumanReview`, parecer, justificativa, correções solicitadas, identidade do especialista, instante de conclusão e o `review_lead_time` resultante) são perdidos do ponto de vista do ciclo de vida do workflow.

### Evidências

1. `src/agent_lab/workflow_events.py` define apenas a dataclass `WorkflowOpened`, inexistindo o evento `WorkflowConcluded`.
2. `src/agent_lab/workflow_repository.py` implementa `append_opened`, `get_opened_by_id`, `get_opened_by_workflow_id`, `list_opened_by_material` e `list_all_opened`, sem métodos correspondentes para conclusão (`append_concluded`, etc.).
3. `src/agent_lab/workflow_projection.py` possui apenas a função `rehydrate_pending_workflow(event: WorkflowOpened)`, que força `review=None` e status `PENDING_HUMAN_REVIEW`.
4. `src/agent_lab/workflow_serialization.py` serializa e desserializa apenas envelopes de `WorkflowOpened` e sua recomendação atemporal.
5. Em caso de encerramento do processo após uma chamada a `conclude_governance_workflow`, a única persistência que sobrevive é o arquivo de auditoria (`audit.jsonl`), o qual **não é nem deve ser** um repositório de ciclo de vida operacional (ver Seção 4).

### Impacto

- **Inconsistência de Estado Pós-Restart:** Itens já decididos reaparecem em filas de trabalho operacionais como pendentes.
- **Risco de Dupla Deliberação:** Especialistas podem deliberar novamente sobre materiais cujo ciclo já fora formalmente concluído.
- **Perda de Rastreabilidade Operacional:** Inviabilidade de reconstruir o lead time de revisão (`review_lead_time`) e a cronologia do processo sem recalcular ou inspecionar logs forenses externos.
- **Degradação de Integridade:** Quebra da garantia de que o ciclo de vida operacional reflita exatamente as deliberações ocorridas.

---

## 3. Objetivo

Implementar a persistência append-only do evento de conclusão de workflow (`WorkflowConcluded`), a serialização versionada com round-trip integral de `HumanReview`, a integridade relacional e sequencial no repositório de ciclo de vida (`WorkflowLifecycleRepository`) e a projeção pura capaz de reconstruir deterministicamente `GovernanceWorkflow` nos estados `PENDING_HUMAN_REVIEW` e `REVIEWED`, garantindo:

1. **Evento Imutável e Mínimo `WorkflowConcluded`:** criação do contrato de domínio para o fato de fechamento do ciclo de governança contendo apenas `event_id`, `workflow_id` e `review: HumanReview`, tendo `review.reviewed_at` como fonte única da verdade temporal da conclusão.
2. **Round-Trip Integral de `HumanReview`:** preservação exata de todos os atributos da deliberação humana (`review_id`, `material_id`, `system_recommendation`, `human_decision`, `reviewer_identity` com seus 5 campos de proveniência, `reviewed_at`, `justification` e a coleção completa de `CorrectionRequest`).
3. **Validação Estrita de Sequência (`Opened → Concluded`):**
   - Rejeição de conclusão sem abertura prévia (`WorkflowNotOpenedError`);
   - Rejeição de dupla conclusão para o mesmo `workflow_id` (`WorkflowAlreadyConcludedError`);
   - Rejeição de `event_id` duplicado (`DuplicateWorkflowEventError`);
   - Rejeição de descompasso de material, descompasso de parecer ou violação temporal (`opened.opened_at <= concluded.review.reviewed_at`).
4. **Discriminação Explícita e Compatibilidade Reversa:**
   - Preservação integral dos registros existentes `WorkflowOpened` `schema_version = 1` com a ausência do campo `event_type` como sua única representação válida;
   - Adição do discriminador explícito `event_type = "WORKFLOW_CONCLUDED"` para `WorkflowConcluded`;
   - Tratamento estritamente fail-closed para qualquer presença de `event_type` diferente de `"WORKFLOW_CONCLUDED"`.
5. **Princípio `Repository != Projection`:** o repositório realiza I/O durável append-only (`flush` + `os.fsync`) e validação de schema fail-closed; as funções de projeção puras em `workflow_projection.py` reconstroem o agregado `GovernanceWorkflow`.
6. **API Pública Mínima e Justificada:** inclusão exclusiva de `append_concluded`, `get_events_by_workflow_id` e `list_all_events` no repositório, preservando todas as APIs existentes da Issue #47.
7. **Separação Rigorosa `Workflow Lifecycle ≠ Audit Persistence`:** o repositório de auditoria e `AuditEvent` permanecem 100% desacoplados e intocados.
8. **Propriedades Derivadas Preservadas:** `closed_at` e `review_lead_time` continuam sendo computados dinamicamente pelo domínio em `GovernanceWorkflow` a partir de `opened_at` e `review.reviewed_at`, sem campos redundantes desnormalizados no arquivo de persistência.
9. **Zero Recomputação:** a reidratação do workflow opera exclusivamente a partir dos fatos persistidos, sem invocar regras de negócio, heurísticas cadastrais ou modelos LLM.

---

## 4. Decisões arquiteturais deliberadas

### 4.1 Separação Mandatória: `Workflow Lifecycle ≠ Audit Persistence`

O sistema mantém duas trilhas persistentes com finalidades, semânticas e exigências de round-trip distintas:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                         TRILHA DE LIFECYCLE                              │
│                                                                          │
│  WorkflowOpened  ──► WorkflowConcluded                                   │
│         │                    │                                           │
│         ▼                    ▼                                           │
│  workflow_serialization (v1)                                             │
│         │                                                                │
│         ▼                                                                │
│  JsonlWorkflowLifecycleRepository (workflow_events.jsonl)                │
│         │                                                                │
│         ▼                                                                │
│  workflow_projection (rehydrate_workflow)                                │
│         │                                                                │
│         ▼                                                                │
│  GovernanceWorkflow (PENDING_HUMAN_REVIEW ou REVIEWED)                   │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                         TRILHA DE AUDITORIA                              │
│                                                                          │
│  HumanReviewResult ──► AuditEvent (HUMAN_REVIEW_RECORDED)                │
│                              │                                           │
│                              ▼                                           │
│                       audit_serialization (v1)                           │
│                              │                                           │
│                              ▼                                           │
│                       JsonlAuditRepository (audit_events.jsonl)          │
│                              │                                           │
│                              ▼                                           │
│                       Trilha forense imutável pós-decisão                │
└──────────────────────────────────────────────────────────────────────────┘
```

**Por que `AuditEvent` NÃO substitui `WorkflowConcluded`:**
1. **Semântica e Responsabilidade:** `AuditEvent` é um registro forense de auditoria gerado por `record_human_review`. `WorkflowConcluded` é um evento de transição de estado operacional de ciclo de vida.
2. **Incompletude Estrutural de `AuditEvent` para Round-Trip de Domínio:** O schema de `AuditEvent` grava metadados resumidos (ex.: `correction_count: int`, `agrees_with_system: bool`). Ele **não** persiste a lista detalhada de objetos `CorrectionRequest` (com `field_name`, `reason`, `suggested_value`) nem o campo `justification`. Portanto, é impossível reconstituir fielmente a entidade de domínio `HumanReview` a partir de um `AuditEvent`.
3. **Isolamento de Falha e Evolução:** Mutações no ciclo operacional de workflow não devem alterar o schema forense de auditoria e vice-versa.

### 4.2 Contrato Mínimo do Evento `WorkflowConcluded`

O evento `WorkflowConcluded` reside em `src/agent_lab/workflow_events.py` e possui os seguintes campos:

```python
@dataclass(frozen=True, slots=True)
class WorkflowConcluded:
    event_id: str
    workflow_id: str
    review: HumanReview
```

- `event_id`: identificador universal único deste registro/fato de conclusão;
- `workflow_id`: identificador do ciclo de workflow sendo concluído;
- `review`: instância completa e imutável de `HumanReview`.
- **Eliminação de redundância temporal:** O evento não possui campo `concluded_at`. A data/hora da conclusão é fornecida exclusivamente por `review.reviewed_at`, evitando duplicação e garantindo fonte única da verdade temporal.

### 4.3 Discriminação Explícita de Registros e Compatibilidade Reversa

A persistência em arquivo JSONL compartilhado utiliza `schema_version = 1` e diferencia os registros de forma explícita e determinística:

1. **`WorkflowOpened` (Legado e Atual):** Não possui campo `event_type`. Sua estrutura permanece 100% idêntica à produzida por `workflow_opened_to_record`:
   ```json
   {
     "schema_version": 1,
     "event_id": "evt-open-001",
     "workflow_id": "wf-mat-001-20260819-01",
     "opened_at": "2026-08-19T08:30:00+00:00",
     "recommendation": { ... }
   }
   ```
2. **`WorkflowConcluded`:** Grava obrigatoriamente o discriminador explícito `"event_type": "WORKFLOW_CONCLUDED"` no envelope JSON:
   ```json
   {
     "schema_version": 1,
     "event_type": "WORKFLOW_CONCLUDED",
     "event_id": "evt-conc-20260821-001",
     "workflow_id": "wf-mat-001-20260821-01",
     "review": { ... }
   }
   ```
3. **Regra de desserialização em `workflow_event_from_record`:**
   - Se a chave `"event_type"` estiver ausente no registro (`"event_type" not in record`), o registro é tratado como `WorkflowOpened` legado `schema_version = 1` (delegando a `workflow_opened_from_record`);
   - Se `"event_type"` estiver presente e `event_type == "WORKFLOW_CONCLUDED"`, o registro é tratado como `WorkflowConcluded` (delegando a `workflow_concluded_from_record`);
   - Qualquer outro caso de chave `"event_type"` presente (incluindo `None`, `"WORKFLOW_OPENED"`, strings vazias, valores arbitrários ou tipos incorretos) é sumariamente rejeitado de forma *fail-closed* (`ValueError` -> `WorkflowCorruptionError`).

### 4.4 Payload Mínimo e Round-Trip Integral de `HumanReview`

Para que um workflow revisado seja reconstituído perfeitamente sem perda de fidelidade, a serialização de `WorkflowConcluded` em `schema_version = 1` deve serializar deterministicamente a estrutura completa de `HumanReview`:

1. `review_id: str`
2. `material_id: str`
3. `system_recommendation: str` (valor de `GovernanceDecision`: `"APPROVE"`, `"REVIEW"`, `"REJECT"`)
4. `human_decision: str` (valor de `HumanDecision`: `"APPROVE"`, `"REJECT"`, `"REQUEST_CORRECTION"`)
5. `reviewer_identity: dict` (`VerifiedSpecialistIdentity`):
   - `specialist_id: str`
   - `identity_provider: str`
   - `identity_subject: str`
   - `verification_id: str`
   - `verified_at: str` (ISO 8601 com timezone)
6. `reviewed_at: str` (ISO 8601 com timezone)
7. `justification: str | None`
8. `corrections: list[dict]` (lista de `CorrectionRequest`):
   - `field_name: str`
   - `reason: str`
   - `suggested_value: str | None`

### 4.5 Princípio `Repository != Projection`

A separação estrita de responsabilidades entre persistência e recomposição do domínio é mantida:

- **`WorkflowLifecycleRepository` (I/O e Integridade Estrutural):**
  - Gerencia a gravação física append-only durável em JSONL;
  - Assegura unicidade de `event_id`, valida se o workflow já foi aberto, bloqueia dupla conclusão e verifica compatibilidade material/decisão/tempo no momento da gravação;
  - Retorna eventos puros (`WorkflowOpened`, `WorkflowConcluded`, `WorkflowLifecycleEvent`);
  - Não constrói nem conhece o agregado de domínio `GovernanceWorkflow`.
- **`workflow_projection.py` (Projeção Pura de Domínio):**
  - Módulo sem dependência de I/O em disco;
  - `rehydrate_pending_workflow(opened: WorkflowOpened) -> GovernanceWorkflow`
  - `rehydrate_reviewed_workflow(opened: WorkflowOpened, concluded: WorkflowConcluded) -> GovernanceWorkflow`
  - `rehydrate_workflow(events: Iterable[WorkflowLifecycleEvent]) -> GovernanceWorkflow`
  - Instancia `GovernanceWorkflow`, deixando que as propriedades derivadas (`material_id`, `status`, `closed_at`, `review_lead_time`) sejam calculadas pelas regras puras do domínio.

### 4.6 Regras de Sequência de Ciclo de Vida (`Opened → Concluded`)

O log de ciclo de vida obedece à máquina de estados estrita:

```text
[Inexistente] ──(append_opened)──► [OPENED / PENDING] ──(append_concluded)──► [CONCLUDED / REVIEWED]
```

Regras obrigatórias validadas pelo repositório:
1. **Unicidade Universal de Evento:** todo `event_id` deve ser único no arquivo. Se já existir (seja de abertura ou conclusão), lança `DuplicateWorkflowEventError`.
2. **Rejeição de Conclusão sem Abertura:** tentar registrar `WorkflowConcluded` para um `workflow_id` sem `WorkflowOpened` prévio lança `WorkflowNotOpenedError`.
3. **Rejeição de Dupla Conclusão:** tentar registrar um segundo `WorkflowConcluded` para um `workflow_id` que já possui conclusão lança `WorkflowAlreadyConcludedError`.
4. **Consistência de Material:** `concluded.review.material_id` deve ser idêntico a `opened.recommendation.material_id`.
5. **Consistência do Parecer:** `concluded.review.system_recommendation` deve ser idêntico a `opened.recommendation.decision`.
6. **Consistência Cronológica:** `concluded.review.reviewed_at >= opened.opened_at`.

### 4.7 API Pública Mínima do Repositório na Issue #52

Para manter a superfície de API enxuta e alinhada à necessidade operacional da Issue #52:

1. **APIs Existentes Preservadas (Issue #47):**
   - `append_opened(self, event: WorkflowOpened) -> None`
   - `get_opened_by_id(self, event_id: str) -> WorkflowOpened | None`
   - `get_opened_by_workflow_id(self, workflow_id: str) -> WorkflowOpened | None`
   - `list_opened_by_material(self, material_id: str) -> tuple[WorkflowOpened, ...]`
   - `list_all_opened(self) -> tuple[WorkflowOpened, ...]`
2. **Novas APIs Obrigatórias:**
   - `append_concluded(self, event: WorkflowConcluded) -> None`: persiste o fechamento do workflow;
   - `get_events_by_workflow_id(self, workflow_id: str) -> tuple[WorkflowLifecycleEvent, ...]`: recupera todos os eventos de um workflow específico (em ordem física de gravação) para subsidiar `rehydrate_workflow`.
3. **Nova API de Consulta Geral Mantida:**
   - `list_all_events(self) -> tuple[WorkflowLifecycleEvent, ...]`: mantida com a justificativa arquitetural de permitir inspeção global do histórico de ciclo de vida, testes de integridade e suporte à reidratação em lote.
4. **APIs Descartadas da v1 (fora de escopo):**
   - `get_concluded_by_id`, `get_concluded_by_workflow_id`, `list_all_concluded` não são necessárias na v1, pois a recuperação e reidratação do workflow operam a partir do aggregate de eventos via `get_events_by_workflow_id` ou `list_all_events`.

### 4.8 Limitação Explícita de Dual-Write (Auditoria vs Lifecycle)

O sistema possui duas trilhas de persistência duráveis e desacopladas (`JsonlAuditRepository` e `JsonlWorkflowLifecycleRepository`).

**Limitação:** Nesta v1, a escrita no repositório de auditoria e a escrita no repositório de ciclo de vida são operações independentes. Não existe transação atômica coordenada em disco entre os dois arquivos JSONL. Uma falha de processo ou de I/O entre a gravação de auditoria e a gravação de ciclo de vida pode gerar **divergência potencialmente persistente** entre as duas trilhas. O sistema na v1 **não possui mecanismo automático de reconciliação ou autocura**. Mecanismos avançados de resiliência transacional (Transactional Outbox, 2-Phase Commit, reconciliação periódica em background ou recuperação idempotente) permanecem explicitamente fora do escopo da v1.

### 4.9 Propriedades Derivadas: `closed_at` e `review_lead_time`

Em alinhamento rigoroso com a SPEC 0044:
- `closed_at` e `review_lead_time` **não são persistidos como campos duplicados** no arquivo JSONL;
- No domínio (`GovernanceWorkflow`):
  - `closed_at` é uma `@property` que deriva `self.review.reviewed_at`;
  - `review_lead_time` é uma `@property` que deriva `self.review.reviewed_at - self.opened_at`.
- Isso preserva a fonte única da verdade e elimina risco de discrepâncias entre timestamps gravados e valores calculados.

### 4.10 Modo Fail-Closed e Escrita Durável

- **Fail-Closed:** Se qualquer linha contiver JSON truncado/inválido, campos obrigatórios ausentes, tipos incorretos, enums desconhecidos, datetimes naive (sem fuso horário) ou versão de schema incompatível, o repositório aborta imediatamente levantando `WorkflowCorruptionError` com o número exato da linha (`line_number`).
- **Escrita Durável:** Todas as operações de append chamam `file.write(...)`, `file.flush()` e `os.fsync(file.fileno())` antes de retornar.

---

## 5. Escopo

### Incluído

- Definição do evento imutável e mínimo de domínio `WorkflowConcluded` em `src/agent_lab/workflow_events.py` contendo apenas `event_id`, `workflow_id` e `review`;
- Definição do Type Alias de evento de ciclo de vida `WorkflowLifecycleEvent = WorkflowOpened | WorkflowConcluded` em `src/agent_lab/workflow_events.py`;
- Serialização e desserialização de `HumanReview`, `VerifiedSpecialistIdentity` e `CorrectionRequest` em `src/agent_lab/workflow_serialization.py` (`schema_version = 1`);
- Serialização e desserialização de `WorkflowConcluded` (`workflow_concluded_to_record`, `workflow_concluded_from_record`, `workflow_event_to_record`, `workflow_event_from_record`) em `src/agent_lab/workflow_serialization.py` com discriminador explícito `event_type = "WORKFLOW_CONCLUDED"`;
- Criação das exceções de persistência `WorkflowNotOpenedError` e `WorkflowAlreadyConcludedError` em `src/agent_lab/workflow_repository.py`;
- Evolução do protocolo `WorkflowLifecycleRepository` e da implementação `JsonlWorkflowLifecycleRepository` para suportar:
  - `append_concluded(event: WorkflowConcluded) -> None`
  - `get_events_by_workflow_id(workflow_id: str) -> tuple[WorkflowLifecycleEvent, ...]`
  - `list_all_events() -> tuple[WorkflowLifecycleEvent, ...]`
- Preservação integral de todas as APIs do repositório entregues na Issue #47;
- Validação estrita de integridade e sequência (`Opened → Concluded`, material, parecer, `opened.opened_at <= review.reviewed_at`) em `JsonlWorkflowLifecycleRepository`;
- Projeção e reidratação em `src/agent_lab/workflow_projection.py`:
  - `rehydrate_reviewed_workflow(opened: WorkflowOpened, concluded: WorkflowConcluded) -> GovernanceWorkflow`
  - `rehydrate_workflow(events: Iterable[WorkflowLifecycleEvent]) -> GovernanceWorkflow`
  - Preservação intacta de `rehydrate_pending_workflow(event: WorkflowOpened) -> GovernanceWorkflow`;
- Testes unitários para eventos, serialização, projeção e repositório com `unittest`;
- Testes de integração end-to-end simulando um único ciclo completo com dois restarts;
- Regressão integral garantindo aprovação dos 206 testes do baseline.

### Fora do escopo

- Métodos não essenciais de repositório (`get_concluded_by_id`, `get_concluded_by_workflow_id`, `list_all_concluded`);
- Atomicidade transacional entre auditoria e lifecycle (outbox, 2PC, reconciliação);
- Múltiplos ciclos de reabertura para o mesmo `workflow_id` (re-submissão após correção pertence a uma futura v2);
- Banco de dados relacional (PostgreSQL, SQLite) ou NoSQL;
- Alteração ou mutação de registros no JSONL (operações de update/delete permanecem expressamente proibidas);
- Concorrência de múltiplos processos e distributed locking;
- Filas operacionais de mensageria (RabbitMQ, SQS, Redis);
- APIs HTTP / REST / FastAPI ou interfaces web;
- Qualquer alteração nos módulos de auditoria (`src/agent_lab/audit.py`, `src/agent_lab/audit_serialization.py`, `src/agent_lab/audit_repository.py`);
- Qualquer alteração no módulo atemporal de recomendação (`src/agent_lab/decision.py`).

---

## 6. Responsabilidade humana e limites do agente

- O sistema persiste e projeta representações computacionais de deliberações de governança.
- O evento `WorkflowConcluded` encapsula uma instância estruturalmente válida de `HumanReview` associada a uma `VerifiedSpecialistIdentity`.
- A existência e persistência da dataclass `WorkflowConcluded` preservam no log operacional a autoridade decisória modelada pelo domínio, não constituindo por si sós prova física irrefutável de presença humana no mundo real.
- O sistema **jamais** conclui um workflow de forma autônoma ou gera um `WorkflowConcluded` sintético sem uma instância válida de `HumanReview`.
- A reidratação de um workflow nos estados `PENDING_HUMAN_REVIEW` ou `REVIEWED` é uma operação pura de reconstituição de estado, sem autoridade decisória.
- As invariantes fundamentais `requires_human_decision = True` e a soberania da decisão humana sobre a recomendação do agente permanecem estritamente preservadas.

---

## 7. Invariantes

1. **Separação Ontológica de Eventos:** `WorkflowConcluded ≠ AuditEvent`. O repositório de ciclo de vida preserva o estado operacional do processo; o repositório de auditoria preserva a evidência forense de conformidade.
2. **Distinção de Identidade:** `event_id` identifica unicamente o registro/fato de conclusão; `workflow_id` identifica o ciclo de vida do workflow.
3. **Imutabilidade e Minimalismo:** `WorkflowConcluded` é uma dataclass congelada (`frozen=True`, `slots=True`) contendo exclusivamente `event_id`, `workflow_id` e `review`.
4. **Fonte Única Temporal de Conclusão:** A data e hora da conclusão é exclusivamente `review.reviewed_at`.
5. **Sequência Obrigatória (`Opened → Concluded`):** Um evento de conclusão não pode existir sem um evento de abertura correspondente com o mesmo `workflow_id`.
6. **Bloqueio de Dupla Conclusão:** É impossível registrar mais de uma conclusão para o mesmo `workflow_id`.
7. **Consistência Material e Decisória:** `concluded.review.material_id == opened.recommendation.material_id` e `concluded.review.system_recommendation == opened.recommendation.decision`.
8. **Consistência Cronológica:** `opened.opened_at <= concluded.review.reviewed_at`.
9. **Timezone Awareness Compulsório:** Todos os timestamps (`opened_at`, `reviewed_at`, `verified_at`) devem conter `tzinfo` explícito e válido. Timestamps naive são sumariamente rejeitados.
10. **Fidelidade Total no Round-Trip de `HumanReview`:** A reconstituição de `HumanReview` a partir de `WorkflowConcluded` preserva 100% dos dados, incluindo identificador, pareceres, justificativas e coleções de `CorrectionRequest`.
11. **Princípio `Repository != Projection`:** O repositório lida apenas com eventos de I/O em disco (`WorkflowOpened`, `WorkflowConcluded`); a projeção é uma função pura que reconstrói `GovernanceWorkflow`.
12. **Derivação Pura de Propriedades Temporais:** `closed_at` e `review_lead_time` são derivados dinamicamente em `GovernanceWorkflow`, não persistidos de forma redundante.
13. **Determinismo e Não-Recomputação:** A reidratação não reexecuta motores de regras, validações cadastrais ou agentes LLM.
14. **Comportamento Fail-Closed:** Qualquer corrupção, valor de `event_type` desconhecido ou incompatibilidade no arquivo JSONL bloqueia operações e acusa o número exato da linha.
15. **Escrita Durável:** Todas as operações de persistência executam `flush` e `os.fsync`.

---

## 8. Requisitos

### Requisitos funcionais

- `RF-01` — Deve existir o contrato imutável `WorkflowConcluded` em `src/agent_lab/workflow_events.py` contendo exclusivamente `event_id: str`, `workflow_id: str` e `review: HumanReview`.
- `RF-02` — `WorkflowConcluded.__post_init__` deve validar:
  - `event_id` e `workflow_id` são strings não vazias (rejeitando strings compostas apenas por espaços);
  - `review` é instância de `HumanReview`.
- `RF-03` — Deve existir o type alias `WorkflowLifecycleEvent = WorkflowOpened | WorkflowConcluded` em `src/agent_lab/workflow_events.py`.
- `RF-04` — `src/agent_lab/workflow_serialization.py` deve fornecer:
  - `workflow_concluded_to_record(event: WorkflowConcluded) -> dict[str, object]` (produzindo envelope com `"event_type": "WORKFLOW_CONCLUDED"`);
  - `workflow_concluded_from_record(record: Mapping[str, object]) -> WorkflowConcluded`;
  - `workflow_event_to_record(event: WorkflowLifecycleEvent) -> dict[str, object]`;
  - `workflow_event_from_record(record: Mapping[str, object]) -> WorkflowLifecycleEvent` (tratando exclusivamente a ausência da chave `"event_type"` como `WorkflowOpened` legado `schema_version = 1`, `event_type == "WORKFLOW_CONCLUDED"` como `WorkflowConcluded` e falhando *fail-closed* para qualquer outro caso com a chave presente).
- `RF-05` — A serialização de `WorkflowConcluded` deve preservar 100% da estrutura de `HumanReview`, incluindo `VerifiedSpecialistIdentity` completa, `justification` e todas as `CorrectionRequest` (com `field_name`, `reason`, `suggested_value`).
- `RF-06` — `workflow_concluded_from_record` deve validar tipo, campos obrigatórios, enums e datetime timezone-aware de forma fail-closed com mensagens claras.
- `RF-07` — Deve existir a exceção `WorkflowNotOpenedError(WorkflowPersistenceError)` lançada ao tentar concluir um workflow inexistente no repositório.
- `RF-08` — Deve existir a exceção `WorkflowAlreadyConcludedError(WorkflowPersistenceError)` lançada ao tentar concluir um workflow que já possui evento de conclusão.
- `RF-09` — O repositório `JsonlWorkflowLifecycleRepository` deve implementar as novas operações:
  - `append_concluded(event: WorkflowConcluded) -> None`;
  - `get_events_by_workflow_id(workflow_id: str) -> tuple[WorkflowLifecycleEvent, ...]`;
  - `list_all_events() -> tuple[WorkflowLifecycleEvent, ...]`.
- `RF-10` — `append_concluded` deve validar a integridade de sequência:
  - `event_id` não pode existir no log (`DuplicateWorkflowEventError`);
  - `workflow_id` deve possuir `WorkflowOpened` prévio (`WorkflowNotOpenedError`);
  - `workflow_id` não pode possuir `WorkflowConcluded` prévio (`WorkflowAlreadyConcludedError`);
  - `event.review.material_id == opened.recommendation.material_id`;
  - `event.review.system_recommendation == opened.recommendation.decision`;
  - `event.review.reviewed_at >= opened.opened_at`.
- `RF-11` — `src/agent_lab/workflow_projection.py` deve fornecer:
  - `rehydrate_reviewed_workflow(opened: WorkflowOpened, concluded: WorkflowConcluded) -> GovernanceWorkflow`;
  - `rehydrate_workflow(events: Iterable[WorkflowLifecycleEvent]) -> GovernanceWorkflow`.
- `RF-12` — A reidratação de workflow concluído deve produzir uma instância de `GovernanceWorkflow` onde:
  - `status == WorkflowStatus.REVIEWED`;
  - `review == concluded.review`;
  - `closed_at == concluded.review.reviewed_at`;
  - `review_lead_time == concluded.review.reviewed_at - opened.opened_at`.
- `RF-13` — A função `rehydrate_workflow` deve receber os eventos de um `workflow_id` e reidratar corretamente para `PENDING_HUMAN_REVIEW` (se contiver apenas `WorkflowOpened`) ou `REVIEWED` (se contiver `WorkflowOpened` seguido de `WorkflowConcluded`).

### Requisitos de qualidade

- `RQ-01` — Todas as classes de evento (`WorkflowConcluded`, `WorkflowOpened`) devem ser imutáveis com `frozen=True` e `slots=True`.
- `RQ-02` — O princípio `Repository != Projection` deve ser rigorosamente respeitado: nenhuma dependência de disco ou I/O em `workflow_projection.py` ou `workflow_events.py`.
- `RQ-03` — O repositório deve operar exclusivamente de forma append-only, com `flush` e `os.fsync` em cada escrita para persistência durável.
- `RQ-04` — O repositório deve ser fail-closed: qualquer corrupção em linha JSON, schema version inválido, discriminador `event_type` desconhecido ou erro estrutural deve lançar `WorkflowCorruptionError` contendo o `line_number`.
- `RQ-05` — Usar exclusivamente a biblioteca padrão do Python 3.11 (`dataclasses`, `datetime`, `enum`, `json`, `os`, `pathlib`, `typing`).
- `RQ-06` — Os módulos de auditoria (`audit.py`, `audit_serialization.py`, `audit_repository.py`) e suas suítes de testes devem permanecer 100% inalterados.
- `RQ-07` — O baseline de 206 testes deve permanecer 100% aprovado sob `python -m unittest discover -s tests -v`.

---

## 9. Proposta técnica

### Contratos e Estruturas Propostas

#### 1. Evento de Domínio (`src/agent_lab/workflow_events.py`)

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypeAlias

from agent_lab.decision import DecisionRecommendation
from agent_lab.human_review import HumanReview


@dataclass(frozen=True, slots=True)
class WorkflowOpened:
    """Immutable domain event representing the opening of a governance workflow."""

    event_id: str
    workflow_id: str
    recommendation: DecisionRecommendation
    opened_at: datetime

    def __post_init__(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class WorkflowConcluded:
    """Immutable domain event representing the conclusion of a governance workflow."""

    event_id: str
    workflow_id: str
    review: HumanReview

    def __post_init__(self) -> None:
        sanitized_event_id = _require_non_blank(self.event_id, "event_id")
        object.__setattr__(self, "event_id", sanitized_event_id)

        sanitized_workflow_id = _require_non_blank(
            self.workflow_id, "workflow_id"
        )
        object.__setattr__(self, "workflow_id", sanitized_workflow_id)

        if not isinstance(self.review, HumanReview):
            raise ValueError("review must be a HumanReview instance")


WorkflowLifecycleEvent: TypeAlias = WorkflowOpened | WorkflowConcluded
```

#### 2. Serialização e Desserialização Versionada (`src/agent_lab/workflow_serialization.py`)

```python
# Contratos de serialização em schema_version = 1

EVENT_TYPE_WORKFLOW_CONCLUDED = "WORKFLOW_CONCLUDED"


def workflow_concluded_to_record(event: WorkflowConcluded) -> dict[str, object]:
    """Serialize a WorkflowConcluded domain event into a versioned dictionary record with explicit event_type."""
    if not isinstance(event, WorkflowConcluded):
        raise ValueError(
            f"Expected WorkflowConcluded instance, got {type(event).__name__}"
        )

    # Serialização integral de HumanReview (incluindo reviewer_identity e corrections)
    ...
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "event_type": EVENT_TYPE_WORKFLOW_CONCLUDED,
        "event_id": event.event_id,
        "workflow_id": event.workflow_id,
        "review": review_dict,
    }


def workflow_concluded_from_record(
    record: Mapping[str, object],
) -> WorkflowConcluded:
    """Deserialize a versioned dictionary record into a WorkflowConcluded domain event."""
    ...


def workflow_event_to_record(
    event: WorkflowLifecycleEvent,
) -> dict[str, object]:
    """Serialize any workflow lifecycle event into its versioned record representation."""
    if isinstance(event, WorkflowOpened):
        return workflow_opened_to_record(event)
    if isinstance(event, WorkflowConcluded):
        return workflow_concluded_to_record(event)
    raise ValueError(f"Unsupported event type: {type(event).__name__}")


def workflow_event_from_record(
    record: Mapping[str, object],
) -> WorkflowLifecycleEvent:
    """Deserialize a versioned dictionary record into the corresponding workflow lifecycle event."""
    if not isinstance(record, Mapping):
        raise ValueError(
            f"Expected mapping record, got {type(record).__name__}"
        )

    if "event_type" not in record:
        return workflow_opened_from_record(record)

    event_type = record["event_type"]
    if event_type == EVENT_TYPE_WORKFLOW_CONCLUDED:
        return workflow_concluded_from_record(record)

    raise ValueError(f"Unsupported or unknown event_type: '{event_type}'")
```

**Envelope JSON Persistido para `WorkflowConcluded` (`schema_version = 1`):**

```json
{
  "schema_version": 1,
  "event_type": "WORKFLOW_CONCLUDED",
  "event_id": "evt-conc-20260821-001",
  "workflow_id": "wf-mat-001-20260821-01",
  "review": {
    "review_id": "rev-mat-001-001",
    "material_id": "MAT-001",
    "system_recommendation": "REVIEW",
    "human_decision": "REQUEST_CORRECTION",
    "reviewer_identity": {
      "specialist_id": "spec-042",
      "identity_provider": "CORP_IDP",
      "identity_subject": "analyst@company.com",
      "verification_id": "ver-auth-987",
      "verified_at": "2026-08-21T08:00:00+00:00"
    },
    "reviewed_at": "2026-08-21T09:15:00+00:00",
    "justification": "Correção necessária na descrição curta e unidade de medida.",
    "corrections": [
      {
        "field_name": "description",
        "reason": "Texto fora do padrão PDM",
        "suggested_value": "PARAFUSO SEXTAVADO M8X20 A2-70"
      },
      {
        "field_name": "base_unit",
        "reason": "Unidade inválida no cadastro de entrada",
        "suggested_value": "UN"
      }
    ]
  }
}
```

#### 3. Projeção e Reidratação (`src/agent_lab/workflow_projection.py`)

```python
from __future__ import annotations

from collections.abc import Iterable

from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus
from agent_lab.workflow_events import (
    WorkflowConcluded,
    WorkflowLifecycleEvent,
    WorkflowOpened,
)


def rehydrate_pending_workflow(event: WorkflowOpened) -> GovernanceWorkflow:
    """Project a WorkflowOpened event into a pending GovernanceWorkflow."""
    if not isinstance(event, WorkflowOpened):
        raise TypeError("event must be a WorkflowOpened instance")

    return GovernanceWorkflow(
        workflow_id=event.workflow_id,
        recommendation=event.recommendation,
        opened_at=event.opened_at,
        review=None,
    )


def rehydrate_reviewed_workflow(
    opened: WorkflowOpened,
    concluded: WorkflowConcluded,
) -> GovernanceWorkflow:
    """Project opened and concluded events into a reviewed GovernanceWorkflow."""
    if not isinstance(opened, WorkflowOpened):
        raise TypeError("opened must be a WorkflowOpened instance")
    if not isinstance(concluded, WorkflowConcluded):
        raise TypeError("concluded must be a WorkflowConcluded instance")

    if opened.workflow_id != concluded.workflow_id:
        raise ValueError(
            f"workflow_id mismatch: opened '{opened.workflow_id}' vs concluded '{concluded.workflow_id}'"
        )

    return GovernanceWorkflow(
        workflow_id=opened.workflow_id,
        recommendation=opened.recommendation,
        opened_at=opened.opened_at,
        review=concluded.review,
    )


def rehydrate_workflow(
    events: Iterable[WorkflowLifecycleEvent],
) -> GovernanceWorkflow:
    """Project an ordered sequence of lifecycle events for a single workflow into its current GovernanceWorkflow state."""
    event_list = list(events)
    if not event_list:
        raise ValueError("events sequence cannot be empty")

    opened: WorkflowOpened | None = None
    concluded: WorkflowConcluded | None = None

    for event in event_list:
        if isinstance(event, WorkflowOpened):
            if opened is not None:
                raise ValueError(
                    f"Multiple WorkflowOpened events detected for workflow '{event.workflow_id}'"
                )
            opened = event
        elif isinstance(event, WorkflowConcluded):
            if opened is None:
                raise ValueError(
                    f"WorkflowConcluded encountered before WorkflowOpened for workflow '{event.workflow_id}'"
                )
            if concluded is not None:
                raise ValueError(
                    f"Multiple WorkflowConcluded events detected for workflow '{event.workflow_id}'"
                )
            if event.workflow_id != opened.workflow_id:
                raise ValueError(
                    f"workflow_id mismatch: opened '{opened.workflow_id}' vs concluded '{event.workflow_id}'"
                )
            concluded = event
        else:
            raise TypeError(f"Unsupported event type: {type(event).__name__}")

    if opened is None:
        raise ValueError("No WorkflowOpened event found in sequence")

    if concluded is None:
        return rehydrate_pending_workflow(opened)

    return rehydrate_reviewed_workflow(opened, concluded)
```

#### 4. Repositório e Exceções (`src/agent_lab/workflow_repository.py`)

```python
class WorkflowPersistenceError(Exception):
    """Base error for workflow lifecycle persistence."""


class DuplicateWorkflowEventError(WorkflowPersistenceError):
    """Raised when event_id already exists."""


class WorkflowAlreadyOpenedError(WorkflowPersistenceError):
    """Raised when a second WorkflowOpened uses the same workflow_id."""


class WorkflowNotOpenedError(WorkflowPersistenceError):
    """Raised when appending WorkflowConcluded for a workflow_id that was never opened."""


class WorkflowAlreadyConcludedError(WorkflowPersistenceError):
    """Raised when a second WorkflowConcluded uses the same workflow_id."""


class WorkflowCorruptionError(WorkflowPersistenceError):
    """Raised when persisted lifecycle history is corrupted."""

    def __init__(self, message: str, *, line_number: int) -> None:
        super().__init__(message)
        self.line_number = line_number


class WorkflowLifecycleRepository(Protocol):
    """Protocol defining the repository contract for workflow lifecycle events."""

    def append_opened(self, event: WorkflowOpened) -> None: ...
    def append_concluded(self, event: WorkflowConcluded) -> None: ...
    def get_opened_by_id(self, event_id: str) -> WorkflowOpened | None: ...
    def get_opened_by_workflow_id(
        self, workflow_id: str
    ) -> WorkflowOpened | None: ...
    def get_events_by_workflow_id(
        self, workflow_id: str
    ) -> tuple[WorkflowLifecycleEvent, ...]: ...
    def list_opened_by_material(
        self, material_id: str
    ) -> tuple[WorkflowOpened, ...]: ...
    def list_all_opened(self) -> tuple[WorkflowOpened, ...]: ...
    def list_all_events(self) -> tuple[WorkflowLifecycleEvent, ...]: ...
```

---

### Arquivos previstos

```text
src/agent_lab/workflow_events.py                  # Adição de WorkflowConcluded e WorkflowLifecycleEvent
src/agent_lab/workflow_serialization.py           # Serialização de HumanReview, WorkflowConcluded e dispatcher
src/agent_lab/workflow_repository.py              # Exceções (WorkflowNotOpenedError, WorkflowAlreadyConcludedError) e métodos append_concluded, queries
src/agent_lab/workflow_projection.py              # Funções rehydrate_reviewed_workflow e rehydrate_workflow
tests/test_workflow_events.py                    # Testes unitários do evento WorkflowConcluded
tests/test_workflow_serialization.py             # Testes de serialização, round-trip e fail-closed de WorkflowConcluded
tests/test_workflow_projection.py                # Testes unitários de rehydrate_reviewed_workflow e rehydrate_workflow
tests/test_workflow_repository.py                # Testes de append_concluded, integridade de sequência e consultas
tests/test_workflow_conclusion_integration.py   # Testes de integração ponta a ponta com persistência durável e 2 restarts
docs/specs/0052_workflow_conclusion_persistence_v1.md # Esta especificação técnica
```

Arquivos que **NÃO** serão alterados:

```text
src/agent_lab/domain.py
src/agent_lab/decision.py
src/agent_lab/human_review.py
src/agent_lab/audit.py
src/agent_lab/audit_serialization.py
src/agent_lab/audit_repository.py
tests/test_domain.py
tests/test_decision.py
tests/test_human_review.py
tests/test_audit_serialization.py
tests/test_audit_repository.py
tests/test_audit_persistence_integration.py
```

---

## 10. Estratégia de testes e TDD

### Etapa 1 — Evento `WorkflowConcluded` (RED → GREEN)

- Criação de instância válida de `WorkflowConcluded`;
- Rejeição de `event_id` ou `workflow_id` vazios ou com espaços em branco;
- Rejeição de `review` que não seja `HumanReview`;
- Asserção de imutabilidade (`frozen=True`).

### Etapa 2 — Serialização e Round-Trip de `HumanReview` e `WorkflowConcluded` (RED → GREEN)

- Serialização de `WorkflowConcluded` com decisão `APPROVE`;
- Serialização de `WorkflowConcluded` com decisão `REJECT` e `justification`;
- Serialização de `WorkflowConcluded` com decisão `REQUEST_CORRECTION`, múltiplas `CorrectionRequest` e `suggested_value` preenchidos e nulos;
- Round-trip 100% idêntico de `VerifiedSpecialistIdentity` e `HumanReview`;
- Preservação da leitura de registros legados `WorkflowOpened` (onde a ausência da chave `"event_type"` é a única representação válida);
- Rejeição fail-closed de payloads corrompidos:
  - `schema_version` ausente, inválido ou diferente de `1`;
  - chave `"event_type"` presente com valor inválido ou desconhecido (incluindo `None`, `"WORKFLOW_OPENED"`, strings vazias ou tipos incorretos);
  - campos obrigatórios ausentes no envelope ou no objeto `review`;
  - strings em branco ou tipos incorretos;
  - valores inválidos de enum em `system_recommendation` ou `human_decision`;
  - datetimes sem timezone ou formato ISO 8601 malformado.

### Etapa 3 — Projeções `rehydrate_reviewed_workflow` e `rehydrate_workflow` (RED → GREEN)

- Reidratação de workflow concluído a partir de `(WorkflowOpened, WorkflowConcluded)`:
  - `status == WorkflowStatus.REVIEWED`;
  - `material_id == recommendation.material_id`;
  - `closed_at == review.reviewed_at`;
  - `review_lead_time == review.reviewed_at - opened_at`;
- Rejeição de reidratação com `workflow_id` divergente entre abertura e conclusão;
- Rejeição de descompasso de material ou recomendação em `GovernanceWorkflow`;
- Reidratação via `rehydrate_workflow(events)`:
  - Lista com `[WorkflowOpened]` → retorna workflow `PENDING_HUMAN_REVIEW`;
  - Lista com `[WorkflowOpened, WorkflowConcluded]` → retorna workflow `REVIEWED`;
  - Lista vazia → levanta `ValueError`;
  - Lista com múltiplos `WorkflowOpened` ou múltiplos `WorkflowConcluded` → levanta `ValueError`;
  - Lista iniciando por `WorkflowConcluded` → levanta `ValueError`.

### Etapa 4 — Repositório `JsonlWorkflowLifecycleRepository` (RED → GREEN)

- `append_concluded` grava evento como linha JSON com `event_type = "WORKFLOW_CONCLUDED"`;
- Verificação de chamada a `flush` e `os.fsync` após escrita;
- Rejeição de duplicidade de `event_id` contra histórico global (`DuplicateWorkflowEventError`);
- Rejeição de conclusão de workflow inexistente (`WorkflowNotOpenedError`);
- Rejeição de conclusão de workflow já concluído (`WorkflowAlreadyConcludedError`);
- Rejeição de incompatibilidade de material entre abertura e conclusão;
- Rejeição de incompatibilidade de parecer entre recomendação e parecer revisado;
- Rejeição de inversão temporal (`opened.opened_at <= review.reviewed_at`);
- `get_events_by_workflow_id(workflow_id)`:
  - Retorna tupla vazia se workflow não existe;
  - Retorna `(WorkflowOpened,)` para workflow aberto e não concluído;
  - Retorna `(WorkflowOpened, WorkflowConcluded)` na ordem de escrita para workflow concluído;
- `list_all_events()`:
  - Retorna todos os eventos do repositório em ordem física de gravação;
  - Retorna coleção vazia para arquivo inexistente ou vazio;
- Fail-closed com `WorkflowCorruptionError` indicando `line_number` em caso de corrupção na linha de conclusão ou `event_type` inválido.

### Etapa 5 — Integração E2E com dois restarts de processo (RED → GREEN)

- Teste ponta a ponta `tests/test_workflow_conclusion_integration.py` cobrindo o ciclo completo de vida operacional com dois restarts em instâncias limpas do repositório:
  1. Abertura do workflow (`append_opened`) no repositório `repo1`;
  2. Primeiro restart: novo repositório `repo2` recupera eventos via `get_events_by_workflow_id` e reidrata `GovernanceWorkflow` com status `PENDING_HUMAN_REVIEW`;
  3. Revisão humana realizada e conclusão gravada (`append_concluded`) via `repo2`;
  4. Segundo restart: novo repositório `repo3` recupera eventos via `get_events_by_workflow_id` e reidrata `GovernanceWorkflow` com status `REVIEWED`, validando `closed_at`, `review_lead_time` e todas as correções humanas intactas;
  5. Auditoria executada em paralelo e gravada no repositório de auditoria independente.

### Etapa 6 — Regressão Completa e Validação dos Gates (GREEN)

- Execução da suíte completa de testes: `python -m unittest discover -s tests -v` garantindo 100% de aprovação (todos os 206 testes do baseline v0.1.0 + novos testes da Issue #52);
- Validação estrita de formatação: `git diff --check`.

---

## 11. Plano de implantação

1. Execução do pipeline de testes locais (`python -m unittest discover -s tests -v`);
2. Verificação de inexistência de erros de formatação (`git diff --check`);
3. Criação de commits semânticos atômicos para cada etapa do TDD;
4. Integração na branch de trabalho da Issue #52.

---

## 12. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Confundir `WorkflowConcluded` com `AuditEvent` | Média | Alto | Separação explícita de módulos, schemas e repositórios; documentação da distinção operacional vs forense. |
| Divergência por Dual-Write (falha parcial entre auditoria e lifecycle gerando divergência potencialmente persistente sem autocura na v1) | Baixa | Médio | Documentação explícita da limitação na v1; ausência de mecanismo automático de reconciliação ou autocura registrada formalmente; persistência append-only síncrona com `fsync`; evolução com outbox/reconciliação reservada para versões futuras. |
| Inconsistência no round-trip de `HumanReview` | Baixa | Alto | Testes unitários exaustivos cobrindo `APPROVE`, `REJECT` (com justificativa) e `REQUEST_CORRECTION` (com múltiplas correções). |
| Tentativa de conclusão de workflow não aberto | Média | Médio | Validação fail-closed no repositório com lançamento de `WorkflowNotOpenedError`. |
| Tentativa de conclusão múltipla | Média | Médio | Validação fail-closed no repositório com lançamento de `WorkflowAlreadyConcludedError`. |
| Concorrência multiprocesso | Baixa | Médio | Fora do escopo da v1 (sistema monoprocesso síncrono); documentado explicitamente. |
| Múltiplos ciclos de workflow após correção | Baixa | Baixo | Fora do escopo da v1 (ciclo único com conclusão); evolução reservada para v2. |

---

## 13. Plano de reversão

Em caso de necessidade de reversão:
1. Reverter as modificações em `src/agent_lab/workflow_events.py`, `src/agent_lab/workflow_serialization.py`, `src/agent_lab/workflow_projection.py` e `src/agent_lab/workflow_repository.py`;
2. Remover os testes específicos da Issue #52 (`tests/test_workflow_conclusion_integration.py` e acréscimos nos testes unitários);
3. Executar o comando canônico de testes para verificar a integridade dos 206 testes do baseline da v0.1.0.

---

## 14. Versionamento e release

### Impacto SemVer

- `MINOR` — Nova funcionalidade compatível de persistência e reidratação de conclusão de workflow, sem quebra de contratos vigentes.

### Publicação prevista

- Versão planejada: `Unreleased` (consolidação da esteira pós-v0.1.0)
- Criação de tag: Não neste incremento
- Criação de GitHub Release: Não neste incremento
- Atualização do `CHANGELOG.md`: No encerramento da release

---

## 15. Critérios de aceite

- [ ] Contrato mínimo `WorkflowConcluded` implementado como dataclass imutável (`frozen=True`, `slots=True`) em `src/agent_lab/workflow_events.py` contendo apenas `event_id`, `workflow_id` e `review`;
- [ ] Type alias `WorkflowLifecycleEvent` definido em `src/agent_lab/workflow_events.py`;
- [ ] Serialização versionada `schema_version = 1` implementada em `src/agent_lab/workflow_serialization.py` garantindo round-trip integral de `HumanReview` (incluindo `VerifiedSpecialistIdentity`, `justification` e `CorrectionRequest`);
- [ ] Registros legados `WorkflowOpened` com ausência da chave `"event_type"` são a única representação válida de abertura e `WorkflowConcluded` grava `"event_type": "WORKFLOW_CONCLUDED"`, falhando *fail-closed* diante de qualquer chave `"event_type"` presente inválida (incluindo `None` e `"WORKFLOW_OPENED"`);
- [ ] Exceções `WorkflowNotOpenedError` e `WorkflowAlreadyConcludedError` implementadas em `src/agent_lab/workflow_repository.py`;
- [ ] Repositório `JsonlWorkflowLifecycleRepository` estendido exclusivamente com os métodos `append_concluded`, `get_events_by_workflow_id` e `list_all_events`;
- [ ] Gravação de `WorkflowConcluded` realiza `flush` e `os.fsync` (escrita durável);
- [ ] `append_concluded` rejeita conclusão sem abertura (`WorkflowNotOpenedError`), dupla conclusão (`WorkflowAlreadyConcludedError`), `event_id` duplicado (`DuplicateWorkflowEventError`), descompasso de material, descompasso de recomendação e inversão cronológica (`opened.opened_at <= review.reviewed_at`);
- [ ] Funções puras `rehydrate_reviewed_workflow` e `rehydrate_workflow` implementadas em `src/agent_lab/workflow_projection.py`;
- [ ] Reidratação de workflow concluído produz `GovernanceWorkflow` com status `REVIEWED`, `closed_at` e `review_lead_time` derivados e dados intactos sem reexecutar regras ou LLM;
- [ ] Módulos de auditoria (`audit.py`, `audit_serialization.py`, `audit_repository.py`) e recomendação (`decision.py`) permanecem 100% inalterados;
- [ ] Testes unitários e de integração (cobrindo um único ciclo completo com 2 restarts) implementados com `unittest`;
- [ ] Suíte completa de testes (206 anteriores + novos testes da Issue #52) passa integralmente via `python -m unittest discover -s tests -v`;
- [ ] Nenhum erro em `git diff --check`.

---

## 16. Questões em aberto

`Nenhuma`.

---

## 17. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| 2026-08-21 | Tornar `WorkflowConcluded` mínimo sem `concluded_at` | `review.reviewed_at` é a única fonte da verdade temporal da conclusão; eliminar redundância | `Jk-Pascoal` |
| 2026-08-21 | Adotar discriminador explícito `"event_type": "WORKFLOW_CONCLUDED"` e ausência da chave `"event_type"` como única forma de `WorkflowOpened` v1 | Eliminar ambiguidade na serialização, preservar compatibilidade com arquivos existentes e falhar fail-closed diante de qualquer chave presente diferente de `"WORKFLOW_CONCLUDED"` (inclusive `None` e `"WORKFLOW_OPENED"`) | `Jk-Pascoal` |
| 2026-08-21 | Restringir novas APIs do repositório a `append_concluded`, `get_events_by_workflow_id` e `list_all_events` | Manter a superfície de API enxuta e estritamente necessária para a reconstrução do estado de workflow | `Jk-Pascoal` |
| 2026-08-21 | Registrar limitação explícita de dual-write (divergência potencialmente persistente sem autocura na v1) | Deixar claro que a v1 não possui transação atômica coordenada nem reconciliação automática entre os dois repositórios JSONL | `Jk-Pascoal` |
| 2026-08-21 | Ajustar seção de responsabilidade humana para foco na autoridade modelada | Evitar alegação inverificável de prova física de presença humana pela dataclass | `Jk-Pascoal` |
| 2026-08-21 | Distinguir estritamente `WorkflowConcluded` de `AuditEvent` | `AuditEvent` é um registro forense resumido; `WorkflowConcluded` é um evento operacional que preserva o round-trip integral de `HumanReview` para recomposição do estado de ciclo de vida | `Jk-Pascoal` |
| 2026-08-21 | Manter `closed_at` e `review_lead_time` derivados em `GovernanceWorkflow` | Evitar redundância e garantir fonte única da verdade no domínio temporal | `Jk-Pascoal` |
| 2026-08-21 | Adotar integridade estrita de sequência (`Opened → Concluded`) no repositório | Impedir corrupção relacional, conclusões órfãs ou duplas finalizações de ciclo operacional | `Jk-Pascoal` |
| 2026-08-21 | Serializar integralmente a coleção de `CorrectionRequest` no schema de ciclo de vida | Viabilizar que o estado `REVIEWED` com desfecho `REQUEST_CORRECTION` seja reconstruído perfeitamente após restarts | `Jk-Pascoal` |
| 2026-08-21 | Preservar princípio `Repository != Projection` com funções puras em `workflow_projection.py` | Manter isolamento completo entre o I/O de arquivos JSONL e a lógica pura de reconstituição de domínio | `Jk-Pascoal` |
