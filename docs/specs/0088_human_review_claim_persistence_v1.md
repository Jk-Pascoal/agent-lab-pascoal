# SPEC-0088 — Human Review Claim Persistence v1

> Especificação técnica para a persistência local, durável, append-only e fail-closed
> dos fatos de assunção voluntária de revisão humana (`HumanReviewClaim`) no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0088` |
| **Status** | `APPROVED` |
| **Issue relacionada** | `#88` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-01` |
| **Última atualização** | `2026-09-01` |
| **Baseline de entrada** | `462 testes aprovados` |
| **Runner oficial** | `unittest` / Python 3.11 |

---

## 1. Contexto

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais PDM/BOM. O baseline atual integrado na branch `main` possui **462 testes aprovados** (100% GREEN, `unittest`, Python 3.11) e consolida:

- validação cadastral determinística e fronteira LLM estruturada com guardrails de identidade;
- Evidence Engine multiorigem (`RULE`, `VALIDATION`, `DUPLICATE`, `LLM`) e pipeline de recomendação determinístico com `requires_human_decision = True`;
- deliberação humana estruturada via `HumanReview` com `VerifiedSpecialistIdentity`;
- persistência durável append-only de auditoria (`AuditEvent` com `schema_version = 1` e `JsonlAuditRepository`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow` com `PENDING_HUMAN_REVIEW` e `REVIEWED`);
- persistência durável append-only de abertura e conclusão de ciclo de vida (`WorkflowOpened` v1/v2, `WorkflowConcluded` v1 e `JsonlWorkflowLifecycleRepository`);
- projeção determinística de reidratação (`rehydrate_workflow`) reconstruindo `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` e `REVIEWED`;
- verificação determinística somente-leitura de consistência cruzada dual-write (`verify_dual_write_consistency`, `verify_repositories_consistency`);
- linhagem causal de follow-up pós-correção com persistência versionada (`schema_version = 2`);
- proveniência, persistência e projeção de linhagem topológica de revisões de materiais (`MaterialRevision`, `JsonlMaterialRevisionRepository`, `project_material_revision_lineage`);
- projeção pura de fila de pendências (`project_pending_human_review_queue`);
- boundary de aplicação para consulta estruturada da fila pendente (`ListPendingHumanReviewsUseCase`);
- boundary de aplicação para deliberação humana (`RecordHumanDecisionUseCase`);
- **contrato de domínio puro em memória para assunção de revisão humana (Issue #85):** módulo `src/agent_lab/human_review_claim.py`, definindo o dataclass congelado `HumanReviewClaim` (`claim_id`, `workflow_id`, `specialist: VerifiedSpecialistIdentity`, `claimed_at: datetime`) e a função pura `claim_pending_human_review(...)`.

Baseline oficial de entrada verificado:

```text
Ran 462 tests in 1.860s
OK
```

Runner oficial:

```powershell
$env:PYTHONPATH="src"; py -3.11 -m unittest discover -s tests -v
```

---

## 2. Problema, Justificativa e Impacto

### Problema

Atualmente, `HumanReviewClaim` e `claim_pending_human_review` operam exclusivamente em memória no domínio. Quando o processo da aplicação é reinicializado, todos os fatos operacionais de assunção de workflows por especialistas verificados são perdidos:

1. **Inexistência de serialização versionada:** não há formato canônico e versionado para codificar e decodificar instâncias de `HumanReviewClaim`;
2. **Inexistência de repositório local durável:** inexiste armazenamento persistente em disco para preservar a história física de claims operacionais;
3. **Ausência de durabilidade e fail-closed:** não há garantias de sincronização física com disco (`flush` + `os.fsync`) nem diagnóstico rigoroso (*fail-closed*) com apontamento de `line_number` 1-based em caso de corrupção de dados ou inconsistência de schema.

### Justificativa e Impacto

Para que a esteira de **Human-in-the-Loop operacional** evolua para uma operação de PoC com suporte a reinicializações de processo e consultas estruturadas, os fatos brutos de assunção voluntária devem ser persistidos com durabilidade.

Sem uma trilha persistente dedicada:
- Reinicializações de processo perdem o histórico de quem assumiu qual workflow e em qual momento;
- Futuras projeções de fila com status de atendimento não terão base física para reconstruir o estado operacional pós-restart;
- Haveria risco de tentar acoplar indevidamente os claims à trilha de ciclo de vida (`WorkflowLifecycleEvent`) ou à trilha de auditoria (`AuditEvent`), violando a separação canônica de responsabilidades do sistema.

---

## 3. Separação Tripla de Responsabilidades Persistentes

O Agent Lab Pascoal preserva uma rigorosa separação de responsabilidades entre três trilhas persistentes complementares, append-only e totalmente desacopladas:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. TRILHA DE LIFECYCLE (Append-only)                                                   │
│    WorkflowOpened (v1/v2) | WorkflowConcluded (v1)                                     │
│    -> Preserva os fatos do ciclo temporal de governança do GovernanceWorkflow.         │
│    -> Viabiliza a reidratação determinística para PENDING_HUMAN_REVIEW e REVIEWED.     │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. TRILHA DE AUDITORIA (Append-only, desacoplada)                                      │
│    AuditEvent (v1)                                                                     │
│    -> Preserva a prova imutável e a rastreabilidade técnica da deliberação humana.     │
│    -> Registra o ato formal e vinculante pós-decisão do especialista.                  │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. TRILHA DEDICADA DE CLAIMS (Append-only, desacoplada)                                │
│    HumanReviewClaim (v1)                                                               │
│    -> Preserva o fato operacional imutável de assunção voluntária de um workflow.      │
│    -> Registra que um especialista assumiu a análise, sem alterar a governança.        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Regras Mandatórias de Isolamento

- **`HumanReviewClaim` NÃO deve ser incorporado a `WorkflowLifecycleEvent`:** o claim é um fato operacional imutável de assunção humana de atendimento; ele não altera o estado do ciclo de vida temporal (`GovernanceWorkflow` permanece estritamente em `PENDING_HUMAN_REVIEW`).
- **`HumanReviewClaim` NÃO deve ser incorporado a `AuditEvent`:** assumir uma tarefa para análise não é uma deliberação, não é uma aprovação, rejeição ou solicitação de correção e não possui efeito de auditoria de governança.
- **Trilha Persistente Dedicada:** os claims devem ser armazenados em arquivo/repositório JSONL dedicado (`JsonlHumanReviewClaimRepository`), com envelope e versionamento de schema próprios.

---

## 4. Invariantes Constitucionais e Arquiteturais

1. **`HumanReviewClaim != HumanReview`:** o claim expressa o compromisso operacional de atendimento; `HumanReview` expressa a decisão substantiva final. Assumir não é deliberar.
2. **`CLAIMED != REVIEWED`:** o claim não conclui o workflow e não existe `WorkflowStatus.CLAIMED` na máquina de estados de governança.
3. **`Repository != Projection`:** o repositório é append-only e preserva os fatos físicos na ordem de inserção. O repositório **não interpreta** qual claim é ativo, não resolve concorrência e não elege vencedores.
4. **`WorkflowLifecycleEvent != HumanReviewClaim` & `AuditEvent != HumanReviewClaim`:** nenhum evento de lifecycle ou auditoria é gerado ou gravado pela persistência de claims.
5. **Imutabilidade do Workflow:** o ato de persistir um claim não efetua qualquer mutação no objeto `GovernanceWorkflow`.
6. **Unicidade Estrita Apenas de `claim_id`:** o repositório rejeita inserção de duplicidade por `claim_id` (`DuplicateHumanReviewClaimError`).
7. **Não-Bloqueio por `workflow_id` no Repositório:** o repositório **NÃO** deve usar duplicidade de `workflow_id` como mecanismo de trava, locking ou coordenação operacional. Se dois claims distintos referenciarem o mesmo `workflow_id`, ambos são persistidos como fatos brutos na ordem física em que chegarem. Caberá à futura camada de Projeção interpretar esses fatos.
8. **Preservação Temporal e de Identidade:** `claimed_at` e `specialist.verified_at` devem ser serializados em formato ISO 8601 preservando obrigatoriamente a timezone e a exatidão cronológica no round-trip.
9. **Leitura *Fail-Closed* Estrita:** linhas em branco, JSONs malformados, schemas incompatíveis, campos ausentes ou datetimes inválidos interrompem a leitura imediatamente com `HumanReviewClaimCorruptionError` contendo o `line_number` físico 1-based.
10. **Durabilidade Física:** toda escrita append-only executa obrigatoriamente `flush()` seguido de `os.fsync()`.

---

## 5. Contratos e Desenho Técnico

### 5.1 Serialização Versionada (`src/agent_lab/human_review_claim_serialization.py`)

A serialização canônica de `HumanReviewClaim` utiliza envelope explícito versionado com `schema_version = 1`.

#### Constante
```python
SCHEMA_VERSION_V1 = 1
```

#### Envelope Serializado Canônico (JSON)
```json
{
  "schema_version": 1,
  "claim_id": "CLM-001",
  "workflow_id": "WF-001",
  "specialist": {
    "specialist_id": "SPEC-001",
    "identity_provider": "CORPORATE_IDP",
    "identity_subject": "user-12345",
    "verification_id": "VER-001",
    "verified_at": "2026-08-31T10:00:00+00:00"
  },
  "claimed_at": "2026-08-31T10:05:00+00:00"
}
```

#### Shape Exato de `VerifiedSpecialistIdentity`
Preserva rigorosamente os 5 campos do contrato formal de `src/agent_lab/human_review.py`, mantendo a distinção entre tipos de domínio e tipos serializados:

- **No contrato de domínio (`VerifiedSpecialistIdentity`):**
  1. `specialist_id: str` (não-vazio, sem coerção silenciosa);
  2. `identity_provider: str` (não-vazio);
  3. `identity_subject: str` (não-vazio);
  4. `verification_id: str` (não-vazio);
  5. `verified_at: datetime` (timezone-aware).

- **No envelope serializado (JSON):**
  1. `specialist_id: str` (string exata);
  2. `identity_provider: str` (string exata);
  3. `identity_subject: str` (string exata);
  4. `verification_id: str` (string exata);
  5. `verified_at: str` (formato ISO 8601 timezone-aware).

#### Funções Puras de Serialização
```python
def human_review_claim_to_record(claim: HumanReviewClaim) -> dict[str, object]:
    """Serializa um HumanReviewClaim imutável em um dicionário versionado (schema_version = 1)."""

def human_review_claim_from_record(record: Mapping[str, object]) -> HumanReviewClaim:
    """Desserializa um dicionário versionado em uma instância imutável de HumanReviewClaim."""
```

#### Regras de Validação na Serialização
- Rejeitar com `ValueError` se `claim` não for `HumanReviewClaim` em `to_record`;
- Rejeitar com `ValueError` se `record` não for `Mapping` em `from_record`;
- Rejeitar se `schema_version` estiver ausente, não for inteiro ou for diferente de `1`;
- Rejeitar se qualquer campo obrigatório estiver ausente (`claim_id`, `workflow_id`, `specialist`, `claimed_at`);
- Rejeitar se qualquer campo string for de tipo incorreto ou for vazio após `strip()`;
- Rejeitar se `claimed_at` ou `specialist.verified_at` não forem strings ISO 8601 válidas ou forem naive (sem timezone);
- Rejeitar se `specialist.verified_at > claimed_at`;
- Rejeitar se o payload contiver campos extras desconhecidos no envelope raiz ou no objeto `specialist`.

---

### 5.2 Repositório Local e Protocolo (`src/agent_lab/human_review_claim_repository.py`)

#### Hierarquia de Exceções
```python
class HumanReviewClaimPersistenceError(Exception):
    """Exceção base para operações de persistência de claims."""

class DuplicateHumanReviewClaimError(HumanReviewClaimPersistenceError):
    """Lançada ao tentar persistir um HumanReviewClaim cujo claim_id já existe no repositório."""

class HumanReviewClaimCorruptionError(HumanReviewClaimPersistenceError):
    """Lançada quando um registro ou arquivo JSONL de claims está corrompido ou viola o schema."""

    def __init__(self, message: str, *, line_number: int) -> None:
        super().__init__(message)
        self.line_number = line_number
```

#### Protocolo de Persistência
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class HumanReviewClaimRepository(Protocol):
    """Protocolo abstrato para persistência append-only de claims de revisão humana."""

    def append(self, claim: HumanReviewClaim) -> None: ...
    def get_by_id(self, claim_id: str) -> HumanReviewClaim | None: ...
    def list_by_workflow_id(self, workflow_id: str) -> tuple[HumanReviewClaim, ...]: ...
    def list_all(self) -> tuple[HumanReviewClaim, ...]: ...
```

#### Implementação Concreta: `JsonlHumanReviewClaimRepository`
```python
class JsonlHumanReviewClaimRepository:
    """Repositório local append-only em arquivo JSONL para HumanReviewClaims."""

    def __init__(self, path: Path) -> None: ...
    
    @property
    def path(self) -> Path: ...

    def append(self, claim: HumanReviewClaim) -> None: ...
    def get_by_id(self, claim_id: str) -> HumanReviewClaim | None: ...
    def list_by_workflow_id(self, workflow_id: str) -> tuple[HumanReviewClaim, ...]: ...
    def list_all(self) -> tuple[HumanReviewClaim, ...]: ...
```

#### Comportamento dos Métodos do Repositório
- `append(claim)`:
  1. Valida se `claim` é instância de `HumanReviewClaim`;
  2. Lê o histórico persistido (fail-closed);
  3. Verifica se já existe claim com o mesmo `claim_id`; se existir, levanta `DuplicateHumanReviewClaimError`;
  4. Serializa o claim via `human_review_claim_to_record`;
  5. Cria diretórios pai se não existirem (`mkdir(parents=True, exist_ok=True)`);
  6. Grava em modo append (`"a"`), executando `file.write(f"{line}\n")`, `file.flush()` e `os.fsync(file.fileno())`.
- `get_by_id(claim_id)`:
  - Valida se `claim_id` é string não-vazia;
  - Retorna o `HumanReviewClaim` correspondente ou `None` se não for encontrado.
- `list_by_workflow_id(workflow_id)`:
  - Valida se `workflow_id` é string não-vazia;
  - Retorna uma tupla imutável `tuple[HumanReviewClaim, ...]` contendo **todos** os claims persistidos daquele `workflow_id`, preservando estritamente a **ordem física de inserção (append)**;
  - **Não determina** claim ativo ou vencedor; apenas relata os fatos persistidos.
- `list_all()`:
  - Retorna uma tupla imutável `tuple[HumanReviewClaim, ...]` contendo todos os claims gravados no arquivo na ordem física de append.
- **Tratamento de Arquivo Inexistente ou Vazio:**
  - Se o arquivo não existir, `list_all()` retorna `()`, `get_by_id()` retorna `None` e `list_by_workflow_id()` retorna `()`.
  - Se o arquivo tiver tamanho zero (0 bytes), retorna coleções vazias sem erro.
- **Tratamento de Corrupção (Fail-Closed):**
  - Linhas em branco (`line.strip() == ""`): levanta `HumanReviewClaimCorruptionError` com `line_number`;
  - JSON malformado (erro de sintaxe JSON): levanta `HumanReviewClaimCorruptionError` com `line_number`;
  - Registro que não seja objeto JSON (`dict`): levanta `HumanReviewClaimCorruptionError` com `line_number`;
  - Schema inválido, versão incompatível ou campo ausente/inválido: levanta `HumanReviewClaimCorruptionError` com `line_number`.

---

## 6. Escopo (In-Scope)

1. Criação do módulo `src/agent_lab/human_review_claim_serialization.py` com constante `SCHEMA_VERSION_V1 = 1`, funções `human_review_claim_to_record` e `human_review_claim_from_record`;
2. Suporte a round-trip com preservação integral de `claim_id`, `workflow_id`, `VerifiedSpecialistIdentity` e `claimed_at` (com equivalência de timezone);
3. Validação defensiva e *fail-closed* de tipos, strings não-vazias e integridade cronológica (`specialist.verified_at <= claimed_at`);
4. Criação do módulo `src/agent_lab/human_review_claim_repository.py` contendo:
   - Hierarquia de exceções (`HumanReviewClaimPersistenceError`, `DuplicateHumanReviewClaimError`, `HumanReviewClaimCorruptionError`);
   - Protocolo `@runtime_checkable class HumanReviewClaimRepository(Protocol)`;
   - Classe concreta `JsonlHumanReviewClaimRepository(path: Path)`.
5. Implementação das operações `append`, `get_by_id`, `list_by_workflow_id` e `list_all` retornando tuplas imutáveis e preservando a ordem física de inserção;
6. Garantia de durabilidade física com `flush()` + `os.fsync()`;
7. Bloqueio estrito de unicidade por `claim_id` (`DuplicateHumanReviewClaimError`);
8. Permissão expressa para persistência de múltiplos claims para o mesmo `workflow_id` desde que possuam `claim_id`s distintos;
9. Leitura *fail-closed* acusando `HumanReviewClaimCorruptionError` com `line_number` 1-based para qualquer anomalia física ou estrutural;
10. Teste de integração vertical pós-restart (`tests/test_human_review_claim_persistence_integration.py`), comprovando que nova instância do repositório lê fielmente os dados gravados por instância anterior sobre o mesmo arquivo JSONL em disco;
11. Exportação pública dos novos símbolos em `src/agent_lab/__init__.py`;
12. Preservação de 100% dos 462 testes do baseline canônico atual em Python 3.11 / `unittest`.

---

## 7. Fora do Escopo (Out of Scope)

Deliberadamente excluídos desta fatia técnica:

- **Projeção de claims ativos (`ActiveClaimProjection` / `project_active_claims`):** derivação de estado ativo/livre permanece em fatia subsequente;
- **Determinação de claim ativo, vigente ou vencedor:** o repositório apenas armazena e recupera fatos;
- **Exclusividade ou unicidade de `workflow_id` no repositório:** múltiplos claims para o mesmo workflow são fatos históricos legítimos a serem interpretados por Projections;
- **Mecanismos de concorrência e trava:** locks, mutexes, checkout, optimistic/pessimistic locking ou leases em disco;
- **Operações de ciclo operacional de claim:** unclaim, release, transferência de titularidade ou revogação;
- **Políticas operacionais de atendimento:** SLA, prazos de atendimento, expiração automática ou priorização de fila;
- **Concorrência multiprocesso e distribuída:** múltiplos processos concorrentes de escrita ou transações distribuídas (2PC);
- **Camada de Aplicação para Claim (`ClaimPendingHumanReviewUseCase`):** orquestração de caso de uso de claim permanece para fatia posterior;
- **Interfaces de Usuário e APIs:** interfaces Web/Streamlit, CLI interativa ou endpoints HTTP/REST;
- **Autenticação e Autorização corporativa:** RBAC, SSO, OAuth2 ou validação de permissões;
- **Alterações em outras trilhas:** nenhuma alteração em `AuditEvent`, `AuditRepository`, `WorkflowLifecycleEvent` ou `WorkflowLifecycleRepository`;
- **Alterações em `GovernanceWorkflow`:** nenhuma alteração em `WorkflowStatus` (não criar status `CLAIMED`).

---

## 8. Estratégia de Testes e TDD

O desenvolvimento será orientado a testes (TDD) em três fatias verticais progressivas:

```text
Fatia 1: Serialização Versionada
  -> Teste RED: test_human_review_claim_serialization.py
  -> Implementação GREEN: human_review_claim_serialization.py
  -> Validação: round-trip, tipos, fail-closed, timezones, schema_version = 1

Fatia 2: Repositório Append-Only Local
  -> Teste RED: test_human_review_claim_repository.py
  -> Implementação GREEN: human_review_claim_repository.py
  -> Validação: append, fsync, duplicate claim_id, múltiplos claims para mesmo workflow_id,
     get_by_id, list_by_workflow_id, list_all, fail-closed com line_number 1-based

Fatia 3: Integração Vertical Pós-Restart & Exports
  -> Teste RED: test_human_review_claim_persistence_integration.py
  -> Implementação GREEN: src/agent_lab/__init__.py
  -> Validação: persistência real em JSONL temporário, simulação de múltiplos restarts,
     round-trip pós-restart, exportação pública dos símbolos, regressão total GREEN
```

---

## 9. Critérios de Aceite

- [ ] `SCHEMA_VERSION_V1 = 1` exportado e validado em `src/agent_lab/human_review_claim_serialization.py`;
- [ ] Round-trip exato de serialização/desserialização de `HumanReviewClaim` preservando todos os campos e timezone;
- [ ] Envelope JSON de serialização preserva o shape exato de `VerifiedSpecialistIdentity` (`specialist_id`, `identity_provider`, `identity_subject`, `verification_id`, `verified_at`);
- [ ] Desserialização rejeita schemas inválidos, campos ausentes/nulos, datas naive e strings compostas apenas por whitespace com `ValueError`;
- [ ] `JsonlHumanReviewClaimRepository` realiza escritas append-only com durabilidade comprovada (`flush` + `os.fsync`);
- [ ] Tentativa de gravar `claim_id` duplicado levanta `DuplicateHumanReviewClaimError` antes de qualquer escrita;
- [ ] Gravação de múltiplos claims com o mesmo `workflow_id` (e `claim_id`s distintos) é permitida e preservada na ordem física de inserção;
- [ ] `get_by_id` recupera o claim exato por `claim_id` ou retorna `None`;
- [ ] `list_by_workflow_id` retorna tupla imutável com todos os claims daquele `workflow_id` na ordem física de inserção;
- [ ] `list_all` retorna tupla imutável com todos os claims persistidos na ordem física de inserção;
- [ ] Leitura *fail-closed* levanta `HumanReviewClaimCorruptionError` informando o `line_number` 1-based em caso de linha vazia, JSON malformado ou violação de contrato;
- [ ] Arquivo inexistente ou de 0 bytes é tratado de forma limpa como repositório vazio;
- [ ] Teste de integração vertical pós-restart comprova recuperação fiel através de nova instância do repositório sobre arquivo JSONL persistido;
- [ ] Símbolos públicos exportados em `src/agent_lab/__init__.py`;
- [ ] Suíte completa de testes executada com `unittest` e Python 3.11 permanece 100% GREEN sobre o baseline de entrada de 462 testes.

---

## 10. Definition of Done (DoD)

- [ ] SPEC aprovada por revisão humana;
- [ ] Todas as três fatias de TDD implementadas com commits atômicos (RED -> GREEN);
- [ ] Suíte de testes canônica aprovada: `$env:PYTHONPATH="src"; py -3.11 -m unittest discover -s tests -v`;
- [ ] `git diff --check` limpo e sem whitespace residual;
- [ ] Nenhum acoplamento indevido com `AuditEvent` ou `WorkflowLifecycleEvent`;
- [ ] Nenhuma lógica de projeção ativa ou caso de uso introduzida antecipadamente;
- [ ] `docs/PROJECT_COMPASS.md` atualizado no closeout com o novo baseline e descrição do incremento;
- [ ] README Audit obrigatório no closeout (`README.md` atualizado somente se o incremento alterar informação pública relevante; caso contrário, registrar explicitamente "README Audit — no update required").
