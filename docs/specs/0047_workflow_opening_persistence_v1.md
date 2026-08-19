# SPEC 0047 — Workflow Opening Persistence v1 — Abertura durável e reidratação de workflow pendente

> Especificação técnica da persistência append-only do evento de abertura de
> workflow (`WorkflowOpened`) e sua reidratação determinística para `GovernanceWorkflow`
> no estado `PENDING_HUMAN_REVIEW` no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0047` |
| Status | `Implementada (local — aguardando PR/CI/merge)` |
| Issue relacionada | `#47` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-19` |
| Data de conclusão | `Unreleased` |
| Última atualização | `2026-08-19` |

## 1. Contexto

O Agent Lab Pascoal possui atualmente uma arquitetura híbrida, estruturada e auditável que abrange:

- extração de evidências por regras determinísticas e por LLM estruturada;
- geração de recomendações determinísticas `DecisionRecommendation` (`APPROVE`, `REVIEW`, `REJECT`);
- identidade verificável do especialista humano `VerifiedSpecialistIdentity`;
- deliberação humana final estruturada `HumanReview` (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`);
- correlação atômica de revisão e auditoria `record_human_review` -> `HumanReviewResult`;
- persistência auditável durável em JSONL via `JsonlAuditRepository` com `AuditEvent` e `schema_version = 1`;
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow` com `WorkflowStatus.PENDING_HUMAN_REVIEW` e `WorkflowStatus.REVIEWED`, introduzido na SPEC 0044).

O baseline de entrada confirmado deste incremento é de 152 testes:

```text
Ran 152 tests
OK
```

O runner oficial permanece:

```powershell
python -m unittest discover -s tests -v
```

Embora o domínio represente o ciclo temporal no domínio (`GovernanceWorkflow.opened_at`), a abertura do workflow existe **exclusivamente em memória volátil**.

Quando uma recomendação é gerada e um workflow é aberto (`PENDING_HUMAN_REVIEW`), caso o processo seja finalizado antes da conclusão da deliberação pelo especialista humano, o fato da abertura e o estado pendente são completamente perdidos.

Para retomar o trabalho, seria necessário reprocessar todo o material (reexecutando regras e chamadas a LLM), o que viola o determinismo temporal, altera o timestamp original de abertura e impede a rastreabilidade do ciclo de governança em espera.

Além disso, a persistência existente de auditoria (`AuditEvent`) destina-se ao registro pós-decisão humana (`HUMAN_REVIEW_RECORDED`), não devendo ser sobrecarregada ou acoplada com o gerenciamento de ciclos operacionais em trânsito. A auditoria atual persiste uma representação correlacionada da revisão humana (com contagem de correções e metadados estruturados), e não um snapshot/round-trip integral de `HumanReview` (visto que `justification` e os detalhes individuais de `CorrectionRequest` não fazem round-trip na auditoria).

## 2. Problema, evidências e impacto

### Problema

1. O fato de abertura de um workflow (`GovernanceWorkflow` no estado `PENDING_HUMAN_REVIEW`) não sobrevive ao encerramento do processo.
2. Não existe mecanismo para persistir duravelmente o evento de abertura de forma append-only.
3. Não existe mecanismo de projeção/reidratação capaz de restaurar o `GovernanceWorkflow` original a partir de um registro persistido sem recalcular regras ou reexecutar LLM.
4. A trilha persistente de auditoria (`AuditEvent`) não modela abertura de ciclo operacional e não deve sofrer mutações conceituais ou quebra de compatibilidade em seu repositório.

### Evidências

1. `src/agent_lab/workflow.py` define `GovernanceWorkflow` e `conclude_governance_workflow`, mas não contém camada de I/O, serialização ou repositório.
2. `src/agent_lab/audit_repository.py` e `src/agent_lab/audit_serialization.py` são dedicados a `AuditEvent` com `schema_version = 1` gerados por `record_human_review`.
3. Não há testes nem código para recuperar workflows pendentes após reinício da aplicação.
4. O baseline atual de 152 testes valida apenas a criação e transição em memória.

### Impacto

- Perda de itens pendentes de revisão em eventuais interrupções de processo;
- Impossibilidade de construir filas duráveis de governança e painéis operacionais de pendências;
- Risco de reprocessamento redundante e descontinuidade temporal de `opened_at`;
- Risco de acoplamento indevido caso a persistência de workflow fosse injetada forçadamente na trilha de `AuditEvent`.

## 3. Objetivo

Implementar a camada vertical de persistência append-only do evento de abertura (`WorkflowOpened`) em formato JSONL e a respectiva projeção determinística que reidrata `GovernanceWorkflow` no estado `PENDING_HUMAN_REVIEW`, garantindo:

1. **Separação estrita de contratos:** `WorkflowOpened` é um evento de ciclo de vida de workflow, desacoplado de `AuditEvent`.
2. **Identidade dupla explícita:**
   - `event_id`: identificador único universal do fato/registro de abertura;
   - `workflow_id`: identificador único do ciclo de vida do workflow de governança.
3. **Persistência append-only durável:** repositório JSONL com escrita durável via `flush` e `os.fsync`, com serialização versionada (`schema_version = 1`), sem asserção de atomicidade transacional.
4. **Separação entre Repositório e Projeção (`Repository != Projection`):**
   - Repositório (`WorkflowLifecycleRepository` / `JsonlWorkflowLifecycleRepository`) é responsável exclusivamente pelo I/O append-only e recuperação de registros `WorkflowOpened`;
   - Projeção/reidratação (`rehydrate_pending_workflow` em `workflow_projection.py`) é responsável pela reconstrução determinística do `GovernanceWorkflow` no domínio.
5. **Preservação integral dos dados:** recuperação exata de `DecisionRecommendation`, lista completa de `GovernanceEvidence` (com `source`, `issue_type`, `observation`, `severity`), `rationale` e `opened_at` (timezone-aware).
6. **Não recomputar regras nem LLM:** a reidratação reconstrói a recomendação e as evidências a partir do conteúdo persistido, sem invocar analisadores.
7. **Integridade de auditoria:** `AuditEvent`, `audit_serialization.py`, `audit_repository.py` e sua suíte de testes permanecem 100% inalterados.

## 4. Decisões arquiteturais deliberadas

1. **`WorkflowOpened` separado de `AuditEvent`:** A abertura de workflow é um evento de fluxo de trabalho/ciclo de vida, não um evento da trilha de deliberação humana de auditoria.
2. **Identidades claras (`event_id` vs `workflow_id`):** `event_id` é o identificador único do evento de abertura (o fato imutável gravado); `workflow_id` é a âncora do ciclo de revisão do material.
3. **Persistência append-only em JSONL com `schema_version = 1`:** Utilizar arquivo de linhas JSON com escrita durável (`write`, `flush`, `fsync`) e validação de schema explícito, sem afirmar atomicidade transacional.
4. **Princípio `Repository != Projection` e Separação de Módulos:**
   - O contrato do evento `WorkflowOpened` reside em `src/agent_lab/workflow_events.py`;
   - A função pura de projeção/reidratação `rehydrate_pending_workflow` reside no módulo separado `src/agent_lab/workflow_projection.py`;
   - O repositório (`WorkflowLifecycleRepository` / `JsonlWorkflowLifecycleRepository`) em `src/agent_lab/workflow_repository.py` persiste e recupera instâncias de `WorkflowOpened`.
5. **Nomenclatura normativa `WorkflowLifecycleRepository`:** O repositório adota o nome `WorkflowLifecycleRepository` para representar adequadamente o log de ciclo de vida e viabilizar extensão futura com `WorkflowConcluded` sem renomear a abstração.
6. **Preservação profunda de `DecisionRecommendation`:** A serialização deve incluir a coleção completa de evidências estruturadas (`GovernanceEvidence`) para que o workflow reidratado seja idêntico ao original em memória, mantendo `requires_human_decision = True`.
7. **Reidratação sem recomputação:** É proibido reexecutar regras de validação ou invocar LLM durante a leitura/reidratação; a verdade do parecer original está contida no evento gravado.
8. **Timestamps timezone-aware:** `opened_at` deve conter `tzinfo` explícito, sendo rejeitado qualquer timestamp naive.
9. **Detecção fail-closed de duplicidade e corrupção:** O repositório rejeita `event_id` ou `workflow_id` duplicados na abertura e falha explicitamente se encontrar linha JSON corrompida.
10. **Não alteração dos módulos de auditoria existentes:** `audit.py`, `audit_serialization.py` e `audit_repository.py` permanecem intocados.
11. **Delimitação estrita de escopo (v1):** `WorkflowConcluded`, persistência de `REVIEWED`, persistência completa de `HumanReview` neste repositório e cálculo persistente de `review_lead_time` estão fora do escopo da Issue #47. A persistência completa de `HumanReview` permanece fora do escopo; a auditoria atual persiste uma representação correlacionada da revisão humana, não um snapshot/round-trip integral de `HumanReview`.

## 5. Escopo

### Incluído

- Contrato imutável de evento `WorkflowOpened` em `src/agent_lab/workflow_events.py` contendo `event_id`, `workflow_id`, `recommendation` e `opened_at`;
- Função pura de projeção/reidratação `rehydrate_pending_workflow(event: WorkflowOpened) -> GovernanceWorkflow` em `src/agent_lab/workflow_projection.py`;
- Serialização e desserialização versionada (`schema_version = 1`) do evento `WorkflowOpened` e sua recomendação/evidências em `src/agent_lab/workflow_serialization.py`;
- Protocolo `WorkflowLifecycleRepository` e implementação `JsonlWorkflowLifecycleRepository` em `src/agent_lab/workflow_repository.py`;
- Operações do repositório:
  - `append_opened(event: WorkflowOpened) -> None`;
  - `get_opened_by_id(event_id: str) -> WorkflowOpened | None`;
  - `get_opened_by_workflow_id(workflow_id: str) -> WorkflowOpened | None`;
  - `list_opened_by_material(material_id: str) -> tuple[WorkflowOpened, ...]`;
  - `list_all_opened() -> tuple[WorkflowOpened, ...]`;
- Validação estrita de timezone aware em `opened_at`;
- Rejeição de `event_id` duplicado e rejeição de abertura para `workflow_id` já existente;
- Tratamento fail-closed de corrupção com identificação do número da linha;
- Testes unitários de eventos, projeção, serialização e repositório;
- Testes de integração do ciclo completo de abertura, persistência durável, reabertura em nova instância e reidratação pendente;
- Regressão integral dos 152 testes existentes.

### Fora do escopo

- Persistência completa de `HumanReview` permanece fora do escopo; a auditoria atual persiste uma representação correlacionada da revisão humana, não um snapshot/round-trip integral de `HumanReview`;
- Persistência do evento de conclusão (`WorkflowConcluded`);
- Persistência do estado `REVIEWED` em arquivo JSONL de workflow;
- Cálculo persistente de `review_lead_time` em arquivo de workflow;
- Atualização ou exclusão (update/delete) de registros (append-only estrito);
- Múltiplos ciclos de workflow para o mesmo `workflow_id` (ciclos subsequentes ficam para v2);
- Banco de dados relacional (SQLite, PostgreSQL) ou NoSQL;
- Concorrência multiprocesso ou locks de rede/distribuídos;
- Filas em memória/externas (RabbitMQ, Celery, SQS);
- APIs HTTP/REST ou interfaces Web;
- Qualquer alteração em `src/agent_lab/audit.py`, `src/agent_lab/audit_serialization.py`, `src/agent_lab/audit_repository.py`.

## 6. Responsabilidade humana e limites do agente

- O sistema persiste a abertura de um workflow para registrar que uma recomendação algorítmica está aguardando revisão humana.
- A persistência do evento `WorkflowOpened` e a reidratação de `GovernanceWorkflow` restabelecem o estado `PENDING_HUMAN_REVIEW`.
- Em nenhuma hipótese a persistência ou a reidratação aprovam, rejeitam ou concluem o workflow de forma autônoma.
- A responsabilidade de decisão sobre o material continua integralmente sob o especialista humano.

## 7. Invariantes

1. **Separação de Eventos:** `WorkflowOpened` e `AuditEvent` são entidades distintas com finalidades e repositórios independentes.
2. **Distinção de Identidade:** `event_id` identifica o evento de abertura de forma única; `workflow_id` identifica o ciclo do workflow.
3. **Imutabilidade:** `WorkflowOpened` é uma dataclass estritamente congelada (`frozen=True`, `slots=True`).
4. **Integridade da Recomendação:** `DecisionRecommendation` reidratada deve preservar o mesmo `material_id`, `decision`, `rationale`, `requires_human_decision = True` e a lista exata de `GovernanceEvidence`.
5. **Reidratação Fiel e Pura:** A reidratação via `rehydrate_pending_workflow` deve produzir uma instância de `GovernanceWorkflow` com `review = None`, `status = WorkflowStatus.PENDING_HUMAN_REVIEW` e `opened_at` idêntico ao evento persistido.
6. **Não recomputação:** Nenhum motor de regras ou agente LLM é invocado durante a reidratação.
7. **Timestamps Timezone-Aware:** `opened_at` deve ser obrigatoriamente aware (`tzinfo` presente e válido).
8. **Unicidade de Abertura:** Uma tentativa de persistir uma abertura com `event_id` já existente ou `workflow_id` já aberto deve ser rejeitada com erro explícito.
9. **Fail-Closed:** Qualquer corrupção estrutural ou versão de schema inválida no arquivo JSONL impede leituras e lança exceção com número da linha.
10. **Persistência Não-Volátil / Durável:** A escrita deve realizar `flush` e `fsync` (escrita durável) antes de retornar controle ao chamador.

## 8. Requisitos

### Requisitos funcionais

- `RF-01` — Deve existir o contrato imutável `WorkflowOpened` em `src/agent_lab/workflow_events.py` com os campos `event_id: str`, `workflow_id: str`, `recommendation: DecisionRecommendation`, `opened_at: datetime`.
- `RF-02` — `WorkflowOpened.__post_init__` deve validar que `event_id` e `workflow_id` são strings não vazias, `recommendation` é instância de `DecisionRecommendation` e `opened_at` é datetime timezone-aware.
- `RF-03` — Deve existir o protocolo `WorkflowLifecycleRepository` e a implementação `JsonlWorkflowLifecycleRepository` em `src/agent_lab/workflow_repository.py`.
- `RF-04` — O repositório deve persistir o evento `WorkflowOpened` em arquivo JSONL com `schema_version = 1`.
- `RF-05` — A serialização de `WorkflowOpened` deve registrar o envelope completo contendo `event_id`, `workflow_id`, `opened_at` em ISO 8601 com timezone e a serialização determinística de `recommendation` (incluindo todas as evidências com `source`, `issue_type`, `observation`, `severity`).
- `RF-06` — O repositório deve fornecer `get_opened_by_id(event_id: str) -> WorkflowOpened | None`.
- `RF-07` — O repositório deve fornecer `get_opened_by_workflow_id(workflow_id: str) -> WorkflowOpened | None`.
- `RF-08` — O repositório deve fornecer `list_opened_by_material(material_id: str) -> tuple[WorkflowOpened, ...]`.
- `RF-09` — O repositório deve fornecer `list_all_opened() -> tuple[WorkflowOpened, ...]`.
- `RF-10` — As listagens do repositório devem preservar a ordem física de gravação do arquivo.
- `RF-11` — O repositório deve rejeitar a gravação de `event_id` duplicado com exceção explícita.
- `RF-12` — O repositório deve rejeitar a gravação de um segundo evento de abertura para o mesmo `workflow_id`.
- `RF-13` — Deve existir a função pura de projeção/reidratação `rehydrate_pending_workflow(event: WorkflowOpened) -> GovernanceWorkflow` no módulo `src/agent_lab/workflow_projection.py` que retorna um `GovernanceWorkflow` com `status == WorkflowStatus.PENDING_HUMAN_REVIEW`, `review = None` e dados preservados.
- `RF-14` — O repositório deve lançar erro de corrupção explícito indicando o número da linha ao encontrar JSON malformado, campo obrigatório ausente, tipo inválido ou `schema_version` desconhecido.

### Requisitos de qualidade

- `RQ-01` — `WorkflowOpened`, `rehydrate_pending_workflow` e os módulos de domínio de workflow não devem importar diretamente o mecanismo de I/O em disco.
- `RQ-02` — A API do repositório de workflow deve ser estritamente append-only (sem métodos de alteração ou exclusão).
- `RQ-03` — As coleções retornadas pelas consultas devem ser imutáveis (`tuple`).
- `RQ-04` — A escrita em disco deve executar `flush` e `os.fsync` garantindo escrita durável em disco.
- `RQ-05` — A implementação deve utilizar exclusivamente a biblioteca padrão do Python (`dataclasses`, `datetime`, `enum`, `json`, `os`, `pathlib`, `typing`).
- `RQ-06` — Todos os testes de persistência devem utilizar diretórios temporários (`tempfile.TemporaryDirectory`) e garantir limpeza após execução.
- `RQ-07` — O baseline completo de 152 testes existentes deve permanecer integralmente GREEN.
- `RQ-08` — Nenhuma alteração deve ser feita em `src/agent_lab/audit.py`, `src/agent_lab/audit_serialization.py`, `src/agent_lab/audit_repository.py`.

## 9. Proposta técnica

### Contratos e Estruturas Propostas

#### 1. Evento de Domínio (`WorkflowOpened` em `src/agent_lab/workflow_events.py`)

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent_lab.decision import DecisionRecommendation


@dataclass(frozen=True, slots=True)
class WorkflowOpened:
    """Immutable domain event representing the opening of a governance workflow."""

    event_id: str
    workflow_id: str
    recommendation: DecisionRecommendation
    opened_at: datetime

    def __post_init__(self) -> None:
        # Validação não vazia para event_id e workflow_id
        # Validação isinstance DecisionRecommendation
        # Validação timezone-aware para opened_at
        ...
```

#### 2. Projeção / Reidratação (`rehydrate_pending_workflow` em `src/agent_lab/workflow_projection.py`)

```python
from __future__ import annotations

from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus
from agent_lab.workflow_events import WorkflowOpened


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
```

#### 3. Repositório (`WorkflowLifecycleRepository` e `JsonlWorkflowLifecycleRepository` em `src/agent_lab/workflow_repository.py`)

```python
class WorkflowLifecycleRepository(Protocol):
    def append_opened(self, event: WorkflowOpened) -> None: ...
    def get_opened_by_id(self, event_id: str) -> WorkflowOpened | None: ...
    def get_opened_by_workflow_id(self, workflow_id: str) -> WorkflowOpened | None: ...
    def list_opened_by_material(self, material_id: str) -> tuple[WorkflowOpened, ...]: ...
    def list_all_opened(self) -> tuple[WorkflowOpened, ...]: ...
```

#### 4. Serialização Versionada (`schema_version = 1` em `src/agent_lab/workflow_serialization.py`)

Envelope JSON persistido em arquivo JSONL:

```json
{
  "schema_version": 1,
  "event_id": "evt-open-001",
  "workflow_id": "wf-mat-001-20260819-01",
  "opened_at": "2026-08-19T08:30:00+00:00",
  "recommendation": {
    "material_id": "MAT-001",
    "decision": "REVIEW",
    "rationale": "Recomendação REVIEW: 1 evidência(s) requer(em) análise humana.",
    "requires_human_decision": true,
    "evidence": [
      {
        "material_id": "MAT-001",
        "source": "RULE",
        "issue_type": "MISSING_CRITICAL_FIELD",
        "observation": "Campo obrigatório do material não informado",
        "severity": "WARNING"
      }
    ]
  }
}
```

### Arquivos previstos

```text
src/agent_lab/workflow_events.py              # Contrato WorkflowOpened
src/agent_lab/workflow_projection.py          # Função pura de projeção rehydrate_pending_workflow
src/agent_lab/workflow_serialization.py       # Serialização/desserialização versionada
src/agent_lab/workflow_repository.py          # Exceções, Protocolo WorkflowLifecycleRepository e JsonlWorkflowLifecycleRepository
tests/test_workflow_events.py                # Testes unitários do evento WorkflowOpened
tests/test_workflow_projection.py            # Testes unitários da projeção rehydrate_pending_workflow
tests/test_workflow_serialization.py         # Testes de serialização, round-trip e validações
tests/test_workflow_repository.py            # Testes do repositório JSONL, I/O durável, duplicidade e corrupção
tests/test_workflow_opening_integration.py   # Teste integrado: criação -> abertura -> persistência -> nova instância -> reidratação
docs/specs/0047_workflow_opening_persistence_v1.md # Esta especificação técnica
```

Arquivos que **NÃO** serão alterados:

```text
src/agent_lab/audit.py
src/agent_lab/audit_serialization.py
src/agent_lab/audit_repository.py
tests/test_audit_serialization.py
tests/test_audit_repository.py
tests/test_audit_persistence_integration.py
```

## 10. Estratégia de testes e TDD

### Etapa 1 — Evento `WorkflowOpened` (RED -> GREEN)

- Criação de `WorkflowOpened` válido;
- Rejeição de `event_id` e `workflow_id` vazios ou com espaços em branco;
- Rejeição de `opened_at` naive;
- Rejeição de `recommendation` inválida;
- Imutabilidade da dataclass (`frozen=True`).

### Etapa 2 — Projeção / Reidratação `rehydrate_pending_workflow` (RED -> GREEN)

- `rehydrate_pending_workflow` gera `GovernanceWorkflow` com `status == PENDING_HUMAN_REVIEW`, `review = None` e dados intactos;
- Rejeição de tipos inválidos em `rehydrate_pending_workflow`.

### Etapa 3 — Serialização Versionada (RED -> GREEN)

- Round-trip completo `WorkflowOpened` <-> JSON record;
- Preservação exata de `evidence` (múltiplas evidências, diferentes severidades e fontes);
- Preservação do timezone de `opened_at`;
- Rejeição de `schema_version` diferente de `1`;
- Rejeição de registros incompletos ou tipos inválidos.

### Etapa 4 — Repositório JSONL e Integridade (RED -> GREEN)

- Criação automática de arquivo na primeira escrita;
- Leitura em arquivo inexistente ou vazio retorna tupla vazia;
- `append_opened` grava de forma síncrona com `flush` e `fsync` (escrita durável);
- Recuperação em nova instância do repositório (`get_opened_by_id`, `get_opened_by_workflow_id`);
- Filtragem por `list_opened_by_material` e listagem geral `list_all_opened`;
- Preservação da ordem física de gravação;
- Rejeição de duplicidade de `event_id`;
- Rejeição de duplicidade de `workflow_id`;
- Detecção de corrupção (JSON inválido, tipo corrompido) com erro fail-closed e linha referenciada.

### Etapa 5 — Integração Ponta a Ponta (RED -> GREEN)

- Fluxo integrado:
  1. Extração de evidências e geração de `DecisionRecommendation`;
  2. Abertura do evento `WorkflowOpened` com timestamp timezone-aware;
  3. Gravação durável em `JsonlWorkflowLifecycleRepository`;
  4. Fechamento e instanciação de novo repositório apontando para o mesmo arquivo;
  5. Recuperação do `WorkflowOpened`;
  6. Projeção via `rehydrate_pending_workflow`;
  7. Conclusão do workflow reidratado via `conclude_governance_workflow` com uma deliberação humana válida;
  8. Comprovação da integridade do ciclo completo sem reexecução de regras ou LLM.

### Etapa 6 — Regressão Completa

Executar o runner oficial:

```powershell
python -m unittest discover -s tests -v
```

Garantir que todos os 152 testes anteriores permaneçam GREEN, somados aos novos testes da Issue #47.

## 11. Gates de qualidade

Antes do Pull Request, executar:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios mínimos:

- todos os testes aprovados;
- nenhum erro de espaços em branco em `git diff --check`;
- alterações restritas aos arquivos previstos na SPEC;
- nenhum dado real ou credencial versionado;
- zero dependências externas adicionadas;
- documentação e Project Compass atualizados ao final.

## 12. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Confundir `WorkflowOpened` com `AuditEvent` | Média | Alto | Separação estrita de módulos, contratos, arquivos de persistência e repositórios. |
| Inconsistência na reidratação de evidências | Baixa | Médio | Serialização explícita campo a campo de `GovernanceEvidence` com round-trip testado. |
| Reabertura acidental do mesmo `workflow_id` | Média | Médio | Validação no repositório rejeitando segundo evento de abertura para o mesmo `workflow_id`. |
| Corrupção de arquivo JSONL em gravação parcial | Baixa | Alto | Uso estrito de `flush` e `os.fsync` (escrita durável), além de leitura em modo fail-closed com linha identificada. |
| Perda de timezone no round-trip JSON | Baixa | Alto | Parsing estrito de formato ISO 8601 com `fromisoformat()` e asserção de timezone aware. |

## 13. Plano de reversão

Em caso de necessidade de reversão:

1. Remover os novos arquivos de workflow persistence (`src/agent_lab/workflow_events.py`, `src/agent_lab/workflow_projection.py`, `src/agent_lab/workflow_serialization.py`, `src/agent_lab/workflow_repository.py`);
2. Remover os testes específicos da Issue #47;
3. Manter intactos `src/agent_lab/workflow.py`, `src/agent_lab/audit_repository.py` e os contratos existentes;
4. Executar os 152 testes do baseline para confirmar estabilidade.

## 14. Versionamento e release

### Impacto SemVer

`MINOR` — Nova funcionalidade compatível de persistência e reidratação de workflow, sem breaking changes nos contratos vigentes.

### Publicação prevista

- Versão planejada: `Unreleased`
- Criação de tag: Não neste incremento
- Criação de GitHub Release: Não neste incremento
- Atualização do `CHANGELOG.md`: No encerramento da release

## 15. Critérios de aceite

- [x] Contrato `WorkflowOpened` implementado como dataclass imutável em `src/agent_lab/workflow_events.py`;
- [x] Função pura `rehydrate_pending_workflow` implementada e testada em `src/agent_lab/workflow_projection.py`;
- [x] Serialização versionada `schema_version = 1` implementada preservando toda a `DecisionRecommendation` e `GovernanceEvidence` em `src/agent_lab/workflow_serialization.py`;
- [x] Repositório `JsonlWorkflowLifecycleRepository` implementado com operações de busca e listagem em `src/agent_lab/workflow_repository.py`;
- [x] Escrita com `flush` e `os.fsync` (escrita durável);
- [x] Rejeição de `event_id` duplicado e `workflow_id` já aberto;
- [x] Leitura em modo fail-closed com identificação de linha em caso de corrupção;
- [x] `AuditEvent`, `audit_serialization.py`, `audit_repository.py` e `schema_version = 1` de auditoria permanecem intocados;
- [x] Testes unitários e de integração implementados com `unittest`;
- [x] Suíte completa de testes (152 anteriores + 54 novos = 206) passa com 100% de aprovação local;
- [x] Nenhum erro em `git diff --check`;
- [ ] Pipeline de CI no GitHub Actions validada após abertura de PR e push da branch.

## 16. Questões em aberto

Nenhuma.

## 17. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| 2026-08-19 | Separar `WorkflowOpened` de `AuditEvent` | Preservar a trilha de auditoria e evitar acoplamento entre ciclo de vida operacional e histórico pós-decisão | `Jk-Pascoal` e Pasquara |
| 2026-08-19 | Adotar princípio `Repository != Projection` com módulo dedicado `workflow_projection.py` | Manter a responsabilidade de I/O separada da reidratação e regras do domínio | `Jk-Pascoal` e Pasquara |
| 2026-08-19 | Nomear repositório como `WorkflowLifecycleRepository` | Representar adequadamente o log de ciclo de vida e viabilizar futura extensão com `WorkflowConcluded` | `Jk-Pascoal` e Pasquara |
| 2026-08-19 | Nomear função como `rehydrate_pending_workflow` | Refletir explicitamente que a v1 reconstrói workflows no estado `PENDING_HUMAN_REVIEW` | `Jk-Pascoal` e Pasquara |
| 2026-08-19 | Serializar `DecisionRecommendation` completa com evidências | Permitir reidratação 100% determinística sem necessidade de reprocessar regras ou LLM | `Jk-Pascoal` e Pasquara |
| 2026-08-19 | Delimitar escopo da v1 à abertura e reidratação pendente | Manter entrega vertical enxuta e focar na persistência do estado pendente antes de evoluir conclusão | `Jk-Pascoal` e Pasquara |
