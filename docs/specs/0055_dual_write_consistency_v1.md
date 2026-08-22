# SPEC 0055 — Dual-Write Consistency Check v1 — Verificação determinística de consistência entre lifecycle e auditoria

> Especificação técnica da verificação estritamente somente-leitura (`read-only`)
> e determinística de integridade e correspondência entre eventos de conclusão de
> ciclo de vida (`WorkflowConcluded`) e eventos de auditoria (`AuditEvent` de tipo `HUMAN_REVIEW_RECORDED`)
> correlacionados por `review_id` no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0055` |
| Status | `Proposta` |
| Issue relacionada | `#55` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-22` |
| Última atualização | `2026-08-22` |

---

## 1. Contexto

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais PDM/BOM. O baseline atual integrado na branch `main` possui 255 testes aprovados e consolida:

- fronteira LLM estruturada e tipada com guardrail de identidade;
- Evidence Engine multiorigem determinístico;
- recommendation pipeline com compulsoriedade de `requires_human_decision = True`;
- identidade verificável do especialista humano `VerifiedSpecialistIdentity`;
- deliberação humana estruturada via `HumanReview` (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`);
- persistência auditável durável append-only (`AuditEvent` com `schema_version = 1` e `JsonlAuditRepository`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow` com `opened_at`, `closed_at`, `review_lead_time`);
- persistência de abertura de ciclo de vida append-only (`WorkflowOpened` com `schema_version = 1` e `JsonlWorkflowLifecycleRepository`, Issue #47);
- persistência de conclusão de ciclo de vida append-only (`WorkflowConcluded` com `schema_version = 1` e `JsonlWorkflowLifecycleRepository`, Issue #52);
- projeção pura de reidratação (`rehydrate_workflow`) reconstruindo deterministicamente `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` ou `REVIEWED` após reinicializações de processo.

Baseline oficial de entrada verificado:

```text
Ran 255 tests in 1.022s
OK
```

Ambiente e runner oficiais:
- **Linguagem:** Python 3.11
- **Runner oficial:** `python -m unittest discover -s tests -v`

---

## 2. Problema, evidências e impacto

### Problema

No desenho arquitetural atual, a conclusão de uma revisão humana gera duas consequências persistentes desacopladas e independentes:
1. Gravação de `WorkflowConcluded` no arquivo de ciclo de vida operacional (`workflow_events.jsonl` via `JsonlWorkflowLifecycleRepository`);
2. Gravação de `AuditEvent` no arquivo de auditoria forense (`audit_events.jsonl` via `JsonlAuditRepository`).

As duas trilhas permanecem conceitualmente separadas sob o princípio `WorkflowLifecycleEvent != AuditEvent`. No entanto, **o dual-write não é atômico**. Uma falha de processo, queda de energia, erro de I/O em disco ou interrupção entre a primeira e a segunda gravação resulta em histórias persistentes divergentes (por exemplo, um workflow concluído sem trilha de auditoria correspondente, ou um evento de auditoria sem o fechamento do ciclo operacional).

### Evidências

1. `src/agent_lab/audit_repository.py` e `src/agent_lab/workflow_repository.py` realizam I/O em arquivos JSONL distintos com `os.fsync` local, sem protocolo de transação distribuída (2PC) ou coordenação transacional de duas fases.
2. Em `docs/PROJECT_COMPASS.md` (Seção 4.3 e Seção 13), o limite é formalmente registrado como decisão deliberadamente adiada ("atomicidade transacional e reconciliação automática entre trilha de auditoria e trilha de lifecycle").
3. Inexiste atualmente no sistema qualquer mecanismo diagnóstico capaz de inspecionar os dois repositórios e atestar se o estado persistido conjunto é consistente ou se contém anomalias pós-falha.

### Impacto

- **Divergência Silenciosa:** Erros operacionais não são percebidos até que auditorias manuais ou tentativas de reidratação ocorram.
- **Risco de Rastreabilidade:** Perda do vínculo entre a decisão operacional no workflow e o registro probatório da auditoria.
- **Insegurança Operacional:** Impossibilidade de verificar programaticamente a higidez dos dados persistidos antes de etapas críticas (como futuras integrações com ERP).

---

## 3. Hipótese e Objetivo

### Hipótese

Uma função pura e determinística de inspeção de leitura, complementada por um adaptador de repositório, é suficiente para detectar e discriminar as classes de inconsistência definidas nesta SPEC v1 entre `WorkflowConcluded` e `AuditEvent` (`HUMAN_REVIEW_RECORDED`), respeitando o princípio de **"detecção antes de reparação"**, sem exigir banco relacional, sem violar o desacoplamento das entidades e sem introduzir mutações acidentais nos repositórios append-only.

### Objetivo

Implementar o módulo `src/agent_lab/consistency.py` contendo a verificação determinística e estritamente somente-leitura (`read-only`) capaz de cruzar `WorkflowConcluded` e `AuditEvent` (`HUMAN_REVIEW_RECORDED`) por `review_id`, detectando órfãos, divergências cadastrais/temporais/metadados e duplicidades, produzindo um relatório estruturado e imutável `DualWriteConsistencyReport`.

---

## 4. Escopo

### Incluído

1. **Enum `ConsistencyIssueType`** em `src/agent_lab/consistency.py` com os 8 tipos canônicos de inconsistência:
   - `MISSING_AUDIT_EVENT`: `WorkflowConcluded` sem `AuditEvent` correspondente;
   - `MISSING_WORKFLOW_CONCLUDED`: `AuditEvent` (`HUMAN_REVIEW_RECORDED`) sem `WorkflowConcluded` correspondente;
   - `MATERIAL_ID_MISMATCH`: divergência em `material_id`;
   - `ACTOR_ID_MISMATCH`: divergência entre `concluded.review.reviewer_id` e `audit_event.actor_id`;
   - `TIMESTAMP_MISMATCH`: divergência temporal entre `concluded.review.reviewed_at` e `audit_event.occurred_at` (comparação semântica de objetos `datetime` timezone-aware);
   - `AUDIT_METADATA_MISMATCH`: divergência ou ausência em campos de metadados sobrepostos de `AuditEvent.metadata`;
   - `DUPLICATE_REVIEW_ID_IN_LIFECYCLE`: colisão de múltiplos `WorkflowConcluded` com o mesmo `review_id`;
   - `DUPLICATE_REVIEW_ID_IN_AUDIT`: colisão de múltiplos `AuditEvent` (`HUMAN_REVIEW_RECORDED`) com o mesmo `review_id`.
2. **Dataclass Imutável `ConsistencyIssue`:** representação estruturada de uma inconsistência com `issue_type`, `review_id`, `workflow_id: str | None`, `audit_event_id: str | None` e `details: str`.
3. **Dataclass Imutável `DualWriteConsistencyReport`:** sumário com `total_concluded_events: int`, `total_audit_review_events: int`, `matched_pairs_count: int`, `issues: tuple[ConsistencyIssue, ...]` e propriedade derivada `is_consistent`.
4. **Definição Formal de `matched_pairs_count`:** número de correlações 1:1 não ambíguas por `review_id`. Um par unívoco continua sendo contado como correlacionado em `matched_pairs_count` mesmo se apresentar divergências pontuais (`MATERIAL_ID_MISMATCH`, `ACTOR_ID_MISMATCH`, `TIMESTAMP_MISMATCH` ou `AUDIT_METADATA_MISMATCH`). Registros com `review_id` duplicado em qualquer lado são ambíguos e não entram em `matched_pairs_count`.
5. **Precedência de Duplicidades:** `review_id` duplicado gera `DUPLICATE_REVIEW_ID_*` e é imediatamente excluído do processamento normal daquele `review_id`, evitando a geração em cascata de diagnósticos artificiais de `MISSING_*` ou mismatches adicionais.
6. **Função Pura Central `verify_dual_write_consistency`:**
   - Assinatura: `verify_dual_write_consistency(lifecycle_events: Sequence[WorkflowLifecycleEvent], audit_events: Sequence[AuditEvent]) -> DualWriteConsistencyReport`;
   - Sem I/O, estritamente em memória, determinística e pura.
7. **Função Adaptadora de Repositórios `verify_repositories_consistency`:**
   - Assinatura: `verify_repositories_consistency(lifecycle_repo: WorkflowLifecycleRepository, audit_repo: AuditRepository) -> DualWriteConsistencyReport`;
   - Consome `list_all_events()` e `list_all()` e delega para a função pura.
8. **Verificação Defensiva de Metadados:** validação segura de campos sobrepostos sem levantar `KeyError` ou exceções não controladas.
9. **Testes Unitários e de Integração:** cobertura completa dos comportamentos especificados, incluindo simulações de interrupção entre gravações em ambas as direções pós-restart.

### Fora do Escopo

- Reparo automático ou reconciliação ativa de arquivos em disco.
- Transação distribuída, 2PC, mutex multiprocesso ou distributed locking.
- Modificação de arquivos persistidos existentes (`workflow_events.jsonl` e `audit_events.jsonl` continuam append-only).
- Modificação de versão de schema (permanece `schema_version = 1`).
- Parser alternativo de corrupção física/JSON (responsabilidade dos repositórios existentes).
- Banco de dados relacional ou SQLite.
- Filas, mensageria, SLAs operacionais ou notificações.
- Integração com ERP ou chamada direta de escrita em sistemas legados.
- Reabertura de workflows após `REQUEST_CORRECTION`.
- Alteração das invariantes constitucionais vigentes.

---

## 5. Invariantes e Responsabilidade Humana

### Invariantes Constitucionais a Preservar

1. **Detecção antes de reparação:** o sistema diagnostica e reporta inconsistências; a intervenção ou reparo exige governança deliberada.
2. **`WorkflowLifecycleEvent ≠ AuditEvent`:** as duas trilhas permanecem entidades separadas em arquivos e repositórios distintos.
3. **`Repository != Checker`:**
   - A leitura com bloqueio de corrupção estrutural de arquivo, JSON inválido ou violação de schema (`AuditCorruptionError`, `WorkflowCorruptionError`) continua sendo responsabilidade estrita e *fail-closed* dos repositórios (`JsonlAuditRepository` e `JsonlWorkflowLifecycleRepository`);
   - O consistency checker opera sobre instâncias válidas de `AuditEvent` e `WorkflowLifecycleEvent` desserializadas;
   - `AUDIT_METADATA_MISMATCH` cobre chaves ausentes, valores incompatíveis ou semanticamente divergentes dentro do dicionário `metadata` de um `AuditEvent` válido, sem converter `consistency.py` em parser redundante de arquivos corrompidos.
4. **Somente-Leitura Estrita:** a verificação não efetua escritas, alterações de metadados ou remoções em nenhum arquivo.
5. **Filtro de Escopo Preciso:**
   - Instâncias de `WorkflowOpened` pertencem ao ciclo temporal e não têm correlação com `AuditEvent` (devem ser ignoradas na checagem cruzada de conclusões sem gerar falsos positivos);
   - Apenas `AuditEvent` com `event_type == AuditEventType.HUMAN_REVIEW_RECORDED` participam da correlação por `review_id`.
6. **Comparação Semântica de Tempo:** a equivalência temporal entre `reviewed_at` e `occurred_at` (e entre `verified_at` e `identity_verified_at` no metadata) deve ser avaliada diretamente sobre objetos `datetime` cientes de fuso horário (`aware datetime`), evitando comparações ingênuas de strings ISO.
7. **Tolerância Defensiva a Metadados:** campos ausentes, tipos corrompidos ou chaves faltantes em `AuditEvent.metadata` devem ser convertidos em diagnósticos `AUDIT_METADATA_MISMATCH`, nunca disparando `KeyError` ou quebrando o fluxo de auditoria. Para `identity_verified_at`, o valor deve ser convertido defensivamente para `datetime` timezone-aware; se ausente, inválido, naive ou divergente de `reviewer_identity.verified_at`, reportar `AUDIT_METADATA_MISMATCH`.
8. **Bloqueio de Associação Ambígua e Precedência de Duplicidades:** caso um `review_id` apareça duplicado em qualquer trilha, todas as suas ocorrências devem ser reportadas como `DUPLICATE_REVIEW_ID_*`, esse `review_id` deve ser isolado do processamento normal (evitando geração em cascata de `MISSING_*` ou mismatches adicionais) e nenhuma correspondência arbitrária deve ser computada em `matched_pairs_count`.
9. **Determinismo e Ordenação Estável:** a lista de inconsistências gerada deve ser previsível e deterministicamente ordenada por `review_id` e `issue_type`.
10. **Fonte Única da Verdade no Relatório:** a tupla `issues` é o estado canônico do `DualWriteConsistencyReport`. A propriedade `is_consistent` é derivada estritamente de `len(self.issues) == 0`.

### Responsabilidade Humana

A verificação de consistência dual-write é uma ferramenta diagnóstica de suporte à governança. O relatório gerado oferece visibilidade probatória inequívoca para auditores e especialistas técnicos. O sistema não altera dados automaticamente nem assume presunção de correção sem deliberação humana.

---

## 6. Requisitos

### Requisitos Funcionais

- `RF-01` — O módulo `src/agent_lab/consistency.py` deve exportar o enum `ConsistencyIssueType`, as dataclasses `ConsistencyIssue` e `DualWriteConsistencyReport`, a função pura `verify_dual_write_consistency` e a função adaptadora `verify_repositories_consistency`.
- `RF-02` — `verify_dual_write_consistency` deve receber uma sequência de `WorkflowLifecycleEvent` e uma sequência de `AuditEvent`, retornando um `DualWriteConsistencyReport` imutável.
- `RF-03` — Quando todas as instâncias de `WorkflowConcluded` possuírem exatamente um `AuditEvent` (`HUMAN_REVIEW_RECORDED`) correspondente com dados perfeitamente consistentes, o relatório deve conter `is_consistent = True`, `issues = ()` e `matched_pairs_count` igual ao total de conclusões.
- `RF-04` — Se um `WorkflowConcluded` não possuir `AuditEvent` com o mesmo `review_id`, reportar `MISSING_AUDIT_EVENT`.
- `RF-05` — Se um `AuditEvent` (`HUMAN_REVIEW_RECORDED`) não possuir `WorkflowConcluded` com o mesmo `review_id`, reportar `MISSING_WORKFLOW_CONCLUDED`.
- `RF-06` — Se houver divergência entre `concluded.review.material_id` e `audit_event.material_id`, reportar `MATERIAL_ID_MISMATCH` e manter a contagem do par 1:1 unívoco em `matched_pairs_count`.
- `RF-07` — Se houver divergência entre `concluded.review.reviewer_id` (`reviewer_identity.specialist_id`) e `audit_event.actor_id`, reportar `ACTOR_ID_MISMATCH` e manter a contagem do par 1:1 unívoco em `matched_pairs_count`.
- `RF-08` — Se houver divergência de instante temporal entre `concluded.review.reviewed_at` e `audit_event.occurred_at`, reportar `TIMESTAMP_MISMATCH` e manter a contagem do par 1:1 unívoco em `matched_pairs_count`.
- `RF-09` — Se houver divergência nos campos sobrepostos de metadados entre `HumanReview` e `AuditEvent.metadata`, reportar `AUDIT_METADATA_MISMATCH` indicando o campo divergente:
  - `system_recommendation`
  - `human_decision`
  - `agrees_with_system`
  - `correction_count`
  - `identity_provider`
  - `identity_subject`
  - `identity_verification_id`
  - `identity_verified_at` (comparado semanticamente como `datetime` timezone-aware)
- `RF-10` — Se `AuditEvent.metadata` omitir campos obrigatórios ou contiver valores/tipos incompatíveis, reportar `AUDIT_METADATA_MISMATCH` de forma limpa, sem levantar `KeyError`.
- `RF-11` — Se houver mais de um `WorkflowConcluded` com o mesmo `review_id` no lifecycle, reportar `DUPLICATE_REVIEW_ID_IN_LIFECYCLE` para cada ocorrência, isolar o `review_id` de análises adicionais e não parear com a auditoria.
- `RF-12` — Se houver mais de um `AuditEvent` (`HUMAN_REVIEW_RECORDED`) com o mesmo `review_id` na auditoria, reportar `DUPLICATE_REVIEW_ID_IN_AUDIT` para cada ocorrência, isolar o `review_id` de análises adicionais e não parear com o lifecycle.
- `RF-13` — Eventos de abertura `WorkflowOpened` devem ser ignorados pela correlação e não devem gerar falsos positivos de auditoria ausente.
- `RF-14` — Eventos de auditoria com `event_type` distinto de `HUMAN_REVIEW_RECORDED` (futuros) devem ser ignorados pela correlação cruzada com conclusões.
- `RF-15` — Repositórios vazios ou sequências vazias devem resultar em relatório com `is_consistent = True`, contagens zeradas e sem inconsistências.
- `RF-16` — `verify_repositories_consistency` deve aceitar instâncias dos protocolos `WorkflowLifecycleRepository` e `AuditRepository`, lendo os eventos persistidos e aplicando `verify_dual_write_consistency`.

### Requisitos de Qualidade

- `RQ-01` — Todas as estruturas de dados de saída devem ser congeladas (`frozen=True`) e imutáveis.
- `RQ-02` — Zero mutação de estado durante as operações de verificação.
- `RQ-03` — Determinismo estrito na ordem de apresentação das inconsistências no relatório.
- `RQ-04` — Cobertura dos comportamentos especificados através do runner oficial `python -m unittest discover -s tests -v`.

---

## 7. Proposta Técnica e Contratos Propostos

### Estrutura de Módulos

```text
src/agent_lab/
├── consistency.py          # Novo: Tipos, Relatório, Função Pura e Adaptador
├── audit.py                # Existente: AuditEvent, record_human_review (inalterado)
├── audit_repository.py     # Existente: JsonlAuditRepository (inalterado)
├── human_review.py         # Existente: HumanReview, VerifiedSpecialistIdentity (inalterado)
├── workflow_events.py      # Existente: WorkflowOpened, WorkflowConcluded (inalterado)
└── workflow_repository.py  # Existente: JsonlWorkflowLifecycleRepository (inalterado)
```

### Contratos de Dados Propostos (`src/agent_lab/consistency.py`)

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence

from agent_lab.audit import AuditEvent, AuditEventType
from agent_lab.audit_repository import AuditRepository
from agent_lab.workflow_events import (
    WorkflowConcluded,
    WorkflowLifecycleEvent,
    WorkflowOpened,
)
from agent_lab.workflow_repository import WorkflowLifecycleRepository


class ConsistencyIssueType(str, Enum):
    """Categorias discriminadas de inconsistência entre lifecycle e auditoria."""

    MISSING_AUDIT_EVENT = "MISSING_AUDIT_EVENT"
    MISSING_WORKFLOW_CONCLUDED = "MISSING_WORKFLOW_CONCLUDED"
    MATERIAL_ID_MISMATCH = "MATERIAL_ID_MISMATCH"
    ACTOR_ID_MISMATCH = "ACTOR_ID_MISMATCH"
    TIMESTAMP_MISMATCH = "TIMESTAMP_MISMATCH"
    AUDIT_METADATA_MISMATCH = "AUDIT_METADATA_MISMATCH"
    DUPLICATE_REVIEW_ID_IN_LIFECYCLE = "DUPLICATE_REVIEW_ID_IN_LIFECYCLE"
    DUPLICATE_REVIEW_ID_IN_AUDIT = "DUPLICATE_REVIEW_ID_IN_AUDIT"


@dataclass(frozen=True, slots=True)
class ConsistencyIssue:
    """Diagnóstico imutável de uma inconsistência pontual identificada."""

    issue_type: ConsistencyIssueType
    review_id: str
    workflow_id: str | None = None
    audit_event_id: str | None = None
    details: str = ""


@dataclass(frozen=True, slots=True)
class DualWriteConsistencyReport:
    """Relatório estruturado e imutável da verificação de consistência cruzada."""

    total_concluded_events: int
    total_audit_review_events: int
    matched_pairs_count: int
    issues: tuple[ConsistencyIssue, ...] = field(default_factory=tuple)

    @property
    def is_consistent(self) -> bool:
        return len(self.issues) == 0

    @property
    def issue_count(self) -> int:
        return len(self.issues)


def verify_dual_write_consistency(
    lifecycle_events: Sequence[WorkflowLifecycleEvent],
    audit_events: Sequence[AuditEvent],
) -> DualWriteConsistencyReport:
    """Função pura que avalia a integridade e paridade entre lifecycle e auditoria."""
    ...


def verify_repositories_consistency(
    lifecycle_repo: WorkflowLifecycleRepository,
    audit_repo: AuditRepository,
) -> DualWriteConsistencyReport:
    """Adaptador de repositório que extrai eventos e executa a verificação pura."""
    ...
```

---

## 8. Critérios de Aceite

- [ ] `CA-01` — **Coleções Vazias:** Coleções ou repositórios vazios produzem relatório consistente vazio (`is_consistent = True`, contagens zeradas: `total_concluded_events = 0`, `total_audit_review_events = 0`, `matched_pairs_count = 0` e `issues = ()`).
- [ ] `CA-02` — **Par Perfeito:** Um par perfeito e sincronizado `WorkflowConcluded` + `AuditEvent(HUMAN_REVIEW_RECORDED)` com dados idênticos produz `is_consistent = True` e `matched_pairs_count = 1` (com `issues = ()`).
- [ ] `CA-03` — **Órfão no Lifecycle:** `WorkflowConcluded` sem auditoria correspondente gera issue `MISSING_AUDIT_EVENT` com `is_consistent = False` e `matched_pairs_count = 0`.
- [ ] `CA-04` — **Órfão na Auditoria:** `AuditEvent(HUMAN_REVIEW_RECORDED)` sem conclusão correspondente gera issue `MISSING_WORKFLOW_CONCLUDED` com `is_consistent = False` e `matched_pairs_count = 0`.
- [ ] `CA-05` — **Divergência de Material:** Divergência de `material_id` entre `HumanReview` e `AuditEvent` gera issue `MATERIAL_ID_MISMATCH` (o par unívoco 1:1 continua sendo computado em `matched_pairs_count`).
- [ ] `CA-06` — **Divergência de Especialista:** Divergência de especialista (`concluded.review.reviewer_id` != `audit_event.actor_id`) gera issue `ACTOR_ID_MISMATCH` (o par unívoco 1:1 continua sendo computado em `matched_pairs_count`).
- [ ] `CA-07` — **Divergência Temporal:** Divergência temporal entre `concluded.review.reviewed_at` e `audit_event.occurred_at` gera issue `TIMESTAMP_MISMATCH` avaliada semanticamente via timezone-aware datetime (o par unívoco 1:1 continua sendo computado em `matched_pairs_count`).
- [ ] `CA-08` — **Inconsistência em Metadados:** Metadados ausentes, com tipos incompatíveis ou semanticamente divergentes em `AuditEvent.metadata` (incluindo `system_recommendation`, `human_decision`, `agrees_with_system`, `correction_count`, `identity_provider`, `identity_subject`, `identity_verification_id` e `identity_verified_at` avaliado semanticamente como timezone-aware datetime) geram issue `AUDIT_METADATA_MISMATCH` sem disparar `KeyError` ou exceção não tratada (o par unívoco 1:1 continua sendo computado em `matched_pairs_count`).
- [ ] `CA-09` — **Duplicidade de `review_id` no Lifecycle:** `review_id` duplicado no lifecycle gera issue `DUPLICATE_REVIEW_ID_IN_LIFECYCLE` para cada ocorrência, isola o `review_id` do processamento normal (evitando cascata de `MISSING_*` ou mismatches adicionais) e não entra em `matched_pairs_count`.
- [ ] `CA-10` — **Duplicidade de `review_id` na Auditoria:** `review_id` duplicado na auditoria gera issue `DUPLICATE_REVIEW_ID_IN_AUDIT` para cada ocorrência, isola o `review_id` do processamento normal (evitando cascata de `MISSING_*` ou mismatches adicionais) e não entra em `matched_pairs_count`.
- [ ] `CA-11` — **Isolamento de `WorkflowOpened`:** `WorkflowOpened` é ignorado pela correlação cruzada e não é tratado como órfão nem gera diagnósticos espúrios.
- [ ] `CA-12` — **Isolamento de Outros Tipos de Auditoria:** `AuditEvent` com tipo diferente de `HUMAN_REVIEW_RECORDED` não participa da correlação cruzada com conclusões.
- [ ] `CA-13` — **Determinismo na Ordenação:** A ordem das issues reportadas no relatório `DualWriteConsistencyReport` é estritamente determinística.
- [ ] `CA-14` — **Integração End-to-End com Falha Dual-Write:** Testes de integração com arquivos temporários via `verify_repositories_consistency` reproduzem estado parcial entre as duas escritas após restart e detectam a inconsistência nas duas direções (gravação completa no lifecycle sem auditoria, e gravação completa na auditoria sem lifecycle).
- [ ] `CA-15` — **Preservação do Baseline de Testes:** Os 255 testes anteriores permanecem estritamente GREEN e todos os novos testes utilizam o runner oficial `unittest` em Python 3.11.
- [ ] `CA-16` — **Imutabilidade de Schemas:** Nenhum schema persistente ou `schema_version` é alterado (permanece `schema_version = 1`).

---

## 9. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| **Comparação de tempo ingênua** por timezone offset | Média | Alto | Utilizar comparação estrita direta entre instâncias de `datetime` timezone-aware do Python, que normaliza internamente fusos UTC e offsets. |
| **KeyError em metadados** não padronizados | Média | Alto | Acesso defensivo via `.get()` e validação explícita de tipos com geração de `AUDIT_METADATA_MISMATCH` contextualizado. |
| **Ambiguidade em duplicidades** de `review_id` | Baixa | Médio | Bloqueio explícito de pareamento e isolamento do identificador caso a cardinalidade para um determinado `review_id` seja diferente de `1:1`. |
| **Regressão no baseline** existente (255 testes) | Baixa | Crítico | Execução mandatória de `python -m unittest discover -s tests -v` antes de qualquer finalização. |

---

## 10. Estratégia de Testes e TDD em Micro-Fatias

A implementação seguirá estritamente o ciclo TDD RED → GREEN:

### Micro-Fatia 1: Tipos Básicos e Modelo de Relatório (RED → GREEN)
- **Teste:** `tests/test_dual_write_consistency.py` validando instanciação de `ConsistencyIssueType`, `ConsistencyIssue` e `DualWriteConsistencyReport` (com `is_consistent` como propriedade derivada de `issues`).
- **Implementação:** Definição das classes em `src/agent_lab/consistency.py`.

### Micro-Fatia 2: Caso Base Consistente e Coleções Vazias (RED → GREEN)
- **Teste:** Testes unitários para repositórios vazios e cenários com 1 e múltiplos workflows/auditorias perfeitamente sincronizados.
- **Implementação:** Lógica inicial de agrupamento por `review_id` e contagem de pares unívocos.

### Micro-Fatia 3: Detecção de Eventos Órfãos (RED → GREEN)
- **Teste:** Cenários com `MISSING_AUDIT_EVENT` e `MISSING_WORKFLOW_CONCLUDED`.
- **Implementação:** Identificação de chaves presentes exclusivamente em um dos lados da correlação.

### Micro-Fatia 4: Detecção de Divergências de Atributos (RED → GREEN)
- **Teste:** Cenários com divergência em `material_id`, `actor_id` e `timestamp` (com semântica timezone-aware).
- **Implementação:** Checagens cruzadas sobre pares unívocos identificados, mantendo-os em `matched_pairs_count`.

### Micro-Fatia 5: Validação Defensiva de Metadados de Auditoria (RED → GREEN)
- **Teste:** Cenários com divergência em parecer, decisão, proveniência de identidade, contagem de correções, validação semântica de `identity_verified_at` e ausência de chaves no dicionário `metadata`.
- **Implementação:** Extração e validação segura dos metadados reportando `AUDIT_METADATA_MISMATCH`.

### Micro-Fatia 6: Precedência de Duplicidades e Bloqueio de Associação (RED → GREEN)
- **Teste:** Cenários com `DUPLICATE_REVIEW_ID_IN_LIFECYCLE` e `DUPLICATE_REVIEW_ID_IN_AUDIT` garantindo isolamento sem cascata de `MISSING_*`.
- **Implementação:** Agrupamento por lista, emissão de duplicidade e exclusão de pareamento para `len > 1`.

### Micro-Fatia 7: Adaptador de Repositórios e Integração Ponta a Ponta (RED → GREEN)
- **Teste:** `tests/test_dual_write_consistency_integration.py` com leitura de arquivos JSONL reais e simulações de interrupção entre gravações em ambas as direções pós-restart.
- **Implementação:** `verify_repositories_consistency` integrando os repositórios existentes.

### Micro-Fatia 8: Regressão Geral
- **Execução:** `python -m unittest discover -s tests -v` assegurando 255 testes anteriores + novos testes GREEN.

---

## 11. Limitações Explícitas que Permanecem

1. **Ausência de Reparo Automático:** A detecção aponta inconsistências mas não modifica os arquivos JSONL (a reconciliação continua exigindo deliberação humana ou intervenção operacional explícita).
2. **Leitura Integral em Memória:** Os repositórios realizam leitura completa do arquivo para montar as sequências de eventos (adequado para escala do laboratório e alinhado aos repositórios atuais).
3. **Escopo Restrito à V1:** Múltiplos ciclos por workflow, reabertura após solicitação de correção e integração transacional direta continuam fora de escopo.

---

## 12. Versionamento e Release

- **Impacto SemVer:** `MINOR` (adição de nova funcionalidade de inspeção de consistência estritamente compatível e não-destrutiva).
- **Publicação:** `Unreleased` (integrada à esteira para futura release pós-v0.1.0).
- **Atualização do `CHANGELOG.md`:** Sim, ao final do ciclo de implementação.
