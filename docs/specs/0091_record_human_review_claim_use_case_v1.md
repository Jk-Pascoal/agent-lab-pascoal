# SPEC-0091 — Record Human Review Claim Application Use Case v1

> Especificação técnica do boundary da camada de aplicação responsável por coordenar
> a criação determinística e a persistência durável dos fatos de assunção voluntária de revisão humana (`HumanReviewClaim`) no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0091` |
| **Status** | `APPROVED` |
| **Issue relacionada** | `#91` |
| **Branch funcional** | `feature/issue-91-record-human-review-claim-use-case` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-02` |
| **Data do ambiente** | `2026-09-02` |
| **Última atualização** | `2026-09-02` |
| **Baseline de entrada** | `503 testes aprovados` |
| **Runner oficial** | `unittest` / Python 3.11 |

---

## 1. Contexto

O **Agent Lab Pascoal** consolida em seu núcleo normativo contratos estritos de domínio, persistência append-only em disco, projeções determinísticas e boundaries da camada de aplicação:

- Contratos de decisão humana e auditoria imutável (`HumanReview`, `AuditEvent`, `record_human_review` em `src/agent_lab/human_review.py` e `src/agent_lab/audit.py`);
- Ciclo de vida temporal e imutável de workflow (`GovernanceWorkflow`, `conclude_governance_workflow`, `open_correction_follow_up` em `src/agent_lab/workflow.py`);
- Eventos de lifecycle e persistência append-only (`WorkflowOpened`, `WorkflowConcluded`, `WorkflowLifecycleRepository`, `JsonlWorkflowLifecycleRepository` em `src/agent_lab/workflow_events.py` e `src/agent_lab/workflow_repository.py`);
- Verificação determinística somente-leitura de consistência cruzada dual-write (`verify_dual_write_consistency`, `verify_repositories_consistency` em `src/agent_lab/consistency.py`);
- Projeção pura e determinística da fila de pendências (`project_pending_human_review_queue` em `src/agent_lab/workflow_projection.py`);
- Primeiro boundary explícito de aplicação para deliberação humana (`RecordHumanDecisionUseCase` em `src/agent_lab/human_review_use_case.py`, Issue #74 / SPEC 0074);
- Segundo boundary explícito de aplicação para consulta estruturada da fila pendente (`ListPendingHumanReviewsUseCase` em `src/agent_lab/pending_human_reviews_use_case.py`, Issue #81 / SPEC 0081);
- **Contrato de domínio para assunção de revisão humana (Issue #85 / SPEC 0085):** módulo `src/agent_lab/human_review_claim.py`, definindo o dataclass congelado `HumanReviewClaim` e a função pura `claim_pending_human_review(...)`;
- **Trilha persistente dedicada para claims (Issue #88 / SPEC 0088):** módulo `src/agent_lab/human_review_claim_repository.py`, definindo o protocolo `HumanReviewClaimRepository` e o repositório append-only `JsonlHumanReviewClaimRepository` com durabilidade física (`flush` + `os.fsync`) e serialização canônica versionada (`schema_version = 1`).

Baseline de entrada verificado:

```text
Ran 503 tests in 1.438s
OK
```

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

1. **`HumanReviewClaim ≠ HumanReview`:** Assumir voluntariamente um workflow para análise operacional não constitui deliberação, aprovação, rejeição ou solicitação de correção.
2. **`CLAIMED ≠ REVIEWED`:** O claim não altera o ciclo de governança do workflow. Não existe o estado `WorkflowStatus.CLAIMED` na máquina de estados de governança.
3. **Preservação do Workflow:** A instância de `GovernanceWorkflow` fornecida permanece estritamente em `WorkflowStatus.PENDING_HUMAN_REVIEW`, com `review is None`, e permanece 100% imutável (sem qualquer mutação interna).
4. **Isolamento de Trilhas:** A persistência do claim não gera `AuditEvent` e não gera `WorkflowLifecycleEvent` (`WorkflowOpened` / `WorkflowConcluded`). Persistir claim não altera lifecycle.
5. **`Repository ≠ Projection`:** O repositório preserva os fatos persistidos e sua ordem física; projeções produzem interpretações derivadas somente segundo semânticas previamente especificadas.
6. **Invariantes pertencem ao Domínio:** A camada Application não duplica regras de negócio (status `PENDING_HUMAN_REVIEW`, coerência cronológica `claimed_at >= opened_at`, validade de `VerifiedSpecialistIdentity`). A autoridade sobre a validade do claim pertence exclusivamente a `claim_pending_human_review(...)`.
7. **Proibição de God Service:** Não criar classes genéricas agregadoras como `ClaimApplicationService`. O caso de uso deve ser coeso, autocontido e focado estritamente na operação `RecordHumanReviewClaim`.

---

## 3. Problema e Objetivos

### Problema

Atualmente, o domínio possui a regra pura `claim_pending_human_review(...)` e a persistência possui `HumanReviewClaimRepository` / `JsonlHumanReviewClaimRepository`, mas a coordenação entre ambos ainda existe de forma desarticulada no chamador ou nos testes:

```text
GovernanceWorkflow + specialist + claimed_at
    ↓
claim_pending_human_review(...)  [Domínio / Memória]
    ↓
HumanReviewClaim
    ↓
HumanReviewClaimRepository.append(...)  [Persistência]
    ↓
HumanReviewClaim
```

Sem um boundary explícito na Camada de Aplicação, futuros adaptadores (UI Streamlit, API REST ou CLI) seriam forçados a orquestrar diretamente o domínio e o repositório, violando o princípio de arquitetura em camadas e criando acoplamento indevido.

### Objetivos

1. Criar o módulo `src/agent_lab/human_review_claim_use_case.py` contendo a classe de caso de uso `RecordHumanReviewClaimUseCase`;
2. Executar em código de produção a coordenação estrita em duas fases:
   - **Fase 1 (Domínio / Zero I/O):** Validação estrutural de entrada na fronteira da Application e delegação integral da criação/validação do claim para `claim_pending_human_review(...)` em memória;
   - **Fase 2 (Persistência Coordenada):** Persistência durável do `HumanReviewClaim` gerado via `HumanReviewClaimRepository.append(...)`;
3. Retornar diretamente a instância imutável de `HumanReviewClaim` resultante (sem introduzir DTOs redundantes nesta v1);
4. Propagar falhas de domínio e persistência de forma estritamente *fail-closed* sem mascaramento;
5. Exportar `RecordHumanReviewClaimUseCase` no pacote raiz `src/agent_lab/__init__.py`;
6. Fornecer cobertura de testes unitários e de integração vertical pós-restart com arquivo JSONL real.

---

## 4. Decisões de Design da API de Aplicação

### 4.1 Nome Canônico

**Decisão:** `RecordHumanReviewClaimUseCase`

**Justificativa:**
- Segue a convenção canônica já consolidada no projeto por `RecordHumanDecisionUseCase`;
- O verbo "Record" reflete com precisão a natureza da operação: coordenação da validação e registro append-only de um fato imutável;
- Evita o verbo "Claim" no nome da classe (`ClaimPendingHumanReviewUseCase`), que induziria à falsa premissa de aquisição de lock exclusivo, remoção do item da fila ou transição de estado no workflow.

### 4.2 Injeção de Dependências

A classe recebe como dependência injetada no construtor (`__init__`) o protocolo canônico:
- `HumanReviewClaimRepository` em `src/agent_lab/human_review_claim_repository.py`.

```python
class RecordHumanReviewClaimUseCase:
    def __init__(
        self,
        *,
        claim_repository: HumanReviewClaimRepository,
    ) -> None:
        self._claim_repository = claim_repository
```

### 4.3 Assinatura do Método `execute`

```python
def execute(
    self,
    workflow: GovernanceWorkflow,
    *,
    claim_id: str,
    specialist: VerifiedSpecialistIdentity,
    claimed_at: datetime,
) -> HumanReviewClaim:
    ...
```

- **`workflow`:** Instância de `GovernanceWorkflow` a ser associada ao claim (validada defensivamente como `isinstance(workflow, GovernanceWorkflow)`);
- **`claim_id`:** Identificador único do claim;
- **`specialist`:** Identidade verificada do especialista (`VerifiedSpecialistIdentity`);
- **`claimed_at`:** Timestamp timezone-aware do momento da assunção.

### 4.4 Retorno da v1

**Decisão:** Retornar diretamente `HumanReviewClaim`.

**Justificativa:**
- `HumanReviewClaim` já é uma dataclass imutável congelada (`frozen=True`, `slots=True`), autossuficiente e tipada;
- Ao contrário de `RecordHumanDecisionUseCase` (que coordena quatro artefatos distintos: workflow, review, audit event e lifecycle event, justificando `RecordHumanDecisionResult`), o fluxo de claim produz e persiste um único artefato (`HumanReviewClaim`);
- Não criar `RecordHumanReviewClaimResult` nesta v1 por mera simetria estética, evitando DTOs redundantes e mantendo o design minimalista.

### 4.5 Regras de Responsabilidade

- A Application realiza exclusivamente validação estrutural defensiva necessária na fronteira (`isinstance(workflow, GovernanceWorkflow) -> TypeError`).
- A Application **NÃO** duplica regras que pertencem ao domínio:
  - Não checa `workflow.status is WorkflowStatus.PENDING_HUMAN_REVIEW`;
  - Não valida formato textual de `claim_id`;
  - Não checa monotonicidade temporal `claimed_at >= workflow.opened_at`;
  - Não checa monotonicidade de identidade `specialist.verified_at <= claimed_at`;
  - Não valida se `claimed_at` possui timezone.
- Toda essa validação semântica e temporal permanece delegada a `claim_pending_human_review(...)`.

---

## 5. Ordem Exata de Coordenação e Tratamento de Falhas

### 5.1 Sequência em Duas Fases (Domain Preparation $\rightarrow$ I/O)

```text
[Chamador / UI / API]
      │
      │ execute(workflow, claim_id=..., specialist=..., claimed_at=...)
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: DOMÍNIO / MEMÓRIA / ZERO I/O                                        │
│                                                                             │
│ 1. Validação Estrutural de Entrada (Application)                            │
│    - if not isinstance(workflow, GovernanceWorkflow): raise TypeError       │
│                                                                             │
│ 2. Criação e Validação Determinística do Claim (Domain)                     │
│    - claim = claim_pending_human_review(                                    │
│          workflow,                                                          │
│          claim_id=claim_id,                                                 │
│          specialist=specialist,                                             │
│          claimed_at=claimed_at,                                             │
│      )                                                                      │
│    - [PONTO DE FALHA]: Se houver violação de status, cronologia ou tipos,    │
│      o domínio levanta TypeError / ValueError imediatamente em memória.     │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      │ (Claim em memória válido com sucesso)
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: PERSISTÊNCIA COORDENADA (I/O)                                       │
│                                                                             │
│ 3. Persistência Append-Only no Repositório (Repository)                     │
│    - self._claim_repository.append(claim)                                   │
│    - [PONTO DE FALHA]: Se houver duplicate claim_id, corrupção ou erro I/O, │
│      o repositório propaga exceção imediatamente fail-closed.               │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: RETORNO DIRETO                                                      │
│                                                                             │
│ 4. Retorno do artefato imutável persistido                                  │
│    - return claim                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Categorias de Falha

#### Categoria A — Falhas Determinísticas da Fase 1 / Domínio (Zero I/O)
* **Origem:** Violação de invariantes em `claim_pending_human_review(...)` ou validação estrutural de tipo no Use Case;
* **Exemplos:**
  - `TypeError`: `workflow` não é `GovernanceWorkflow`, `specialist` não é `VerifiedSpecialistIdentity`, `claim_id` não é string;
  - `ValueError`: `workflow` não está em `PENDING_HUMAN_REVIEW` (ex: `REVIEWED`); `claimed_at < workflow.opened_at`; `specialist.verified_at > claimed_at`; `claim_id` vazio ou somente whitespace; `claimed_at` sem timezone;
* **Garantia:** Zero I/O ocorreu. O repositório não é chamado (`self._claim_repository.append` não é executado) e os arquivos físicos em disco permanecem 100% inalterados.

#### Categoria B — Falhas de Persistência da Fase 2 (Repository)
* **Origem:** Rejeições e erros de persistência levantados por `HumanReviewClaimRepository.append(...)`;
* **Exemplos:**
  - `DuplicateHumanReviewClaimError`: `claim_id` já existe no arquivo;
  - `HumanReviewClaimCorruptionError`: arquivo corrompido ou com schema violado (com `line_number` 1-based);
  - `HumanReviewClaimPersistenceError` / `OSError`: falhas físicas de escrita/disco;
* **Garantia e Semântica:**
  - A exceção propaga imediatamente de forma *fail-closed*;
  - **Sem blocos `except Exception` genéricos, sem retries silenciosos, sem compensação automática e sem rollbacks fictícios;**
  - O Use Case não mascara falhas de infraestrutura.

---

## 6. Semântica de Múltiplos Claims e Vigência

O Use Case apenas coordena e registra o fato de assunção solicitado.

### Regras Declaradas

1. **Unicidade Estrita Apenas de `claim_id`:** O repositório rejeita repetição de `claim_id`, mas permite múltiplos claims associados ao mesmo `workflow_id`.
2. **Sem Verificação de Exclusividade:** O Use Case **NÃO** consulta se o workflow já possui claims anteriores antes de persistir.
3. **Sem Eleição de Vencedor:** O Use Case **NÃO** elege qual especialista é o "dono" do workflow.
4. **Sem Revogação:** O Use Case **NÃO** cancela ou revoga claims prévios.
5. **Sem Bloqueio de Workflow:** O workflow permanece acessível e em `PENDING_HUMAN_REVIEW`.
6. **Vigência Indefinida nesta Fatia:** A definição de qual claim é ativo ou vigente permanece **indefinida** nesta v1.
7. **Exclusividade e Desempate Indefinidos:** Regras de exclusividade, expiração ou desempate permanecem **indefinidas** nesta v1.
8. **Proibição de Política Arbitrária em Projeções Futuras:** Projection não cria política. Nenhuma futura `Active Claim Projection` poderá inventar regras de vigência (*Last-Claim-Wins*, timestamp mais recente ou qualquer política equivalente) sem que haja um contrato operacional formalmente especificado por decisão humana.

---

## 7. Escopo Detalhado

### Incluído (In-Scope)

1. **Módulo de Aplicação (`src/agent_lab/human_review_claim_use_case.py`):**
   - Classe `RecordHumanReviewClaimUseCase` com injeção de dependência no `__init__` e método `execute(...)`;
   - Validação defensiva de fronteira (`isinstance(workflow, GovernanceWorkflow) -> TypeError`);
   - Coordenação determinística em duas fases (Domínio com Zero I/O $\rightarrow$ Persistência);
   - Retorno direto de `HumanReviewClaim`;
2. **Exportação Pública (`src/agent_lab/__init__.py`):**
   - Exportação de `RecordHumanReviewClaimUseCase` no pacote raiz;
3. **Testes Unitários (`tests/test_human_review_claim_use_case.py`):**
   - Happy path: coordenação completa (Workflow + Domínio + Mock/Fake Repo $\rightarrow$ retorno `HumanReviewClaim`);
   - Validação defensiva de entrada: rejeição de tipo não-`GovernanceWorkflow` com `TypeError`;
   - Falha determinística de domínio antes de I/O: workflow já revisado levanta `ValueError` e repo mock comprova que `append` não foi chamado;
   - Falha determinística de domínio antes de I/O: violações cronológicas (`claimed_at < opened_at`) e de especialista (`verified_at > claimed_at`) levantam `ValueError` sem chamar `append`;
   - Propagação fail-closed de falhas do repositório: `DuplicateHumanReviewClaimError` e `HumanReviewClaimCorruptionError` propagam sem mascaramento;
4. **Testes de Integração Vertical (`tests/test_human_review_claim_use_case_integration.py`):**
   - Integração vertical com `JsonlHumanReviewClaimRepository` real gravando em arquivo JSONL temporário;
   - Verificação de persistência física em disco;
   - Comprovação pós-restart: nova instância do repositório lê fielmente o claim persistido pelo Use Case;
   - Comprovação de múltiplos claims para o mesmo `workflow_id` persistidos sequencialmente via Use Case;
5. **Preservação Integral do Baseline:**
   - 100% dos 503 testes existentes mantidos GREEN em Python 3.11 / `unittest`.

### Explicitamente Fora de Escopo (Out of Scope)

- **Projeção de Claims Ativos (`Active Claim Projection` / `Last-Claim-Wins` / eleição de vigência);**
- **Projeção Composta de Fila com Claims (`Queue with Claim Status Projection`);**
- **Criação de DTO redundante `RecordHumanReviewClaimResult`;**
- **Locking, mutex, lease, timeout, checkout ou controle de concorrência multiprocesso;**
- **Operações de ciclo de vida de claim (`unclaim`, `release`, `transfer`, cancelamento, expiração);**
- **Atribuição gerencial compulsória (*assignment* / *ownership*) ou SLAs operacionais;**
- **Qualquer alteração em `GovernanceWorkflow`, `WorkflowStatus` (sem status `CLAIMED`), `AuditEvent` ou `WorkflowLifecycleEvent`;**
- **Interfaces externas (UI Streamlit, CLI, APIs REST);**
- **Autenticação, autorização ou RBAC real;**
- **Pressões arquiteturais P-07 (Escala 100k+ SKUs) e P-08 (Material Supersession / Replacement).**

---

## 8. Estratégia TDD Planejada

A implementação seguirá um ciclo rigoroso de micro-TDD em fatias mínimas progressivas orientadas a evidência.

### Princípio Metodológico de Testes
Cada fatia começa pela introdução/execução do teste que prova a propriedade desejada:
- Se o teste falhar por ausência real da propriedade: registrar o estado RED genuíno e implementar a mudança mínima de código de produção para alcançar GREEN.
- Se o teste já estiver aprovado pela composição de invariantes prévias ou implementações de fatias anteriores: registrar honestamente como **"GREEN por composição"** e **NÃO fabricar falha artificial (RED artificial)**.
- Nenhuma mutação de código de produção deve ser realizada exclusivamente para simular um estado RED.

### Fatias Planejadas

```text
Fatia 1: Happy path de coordenação da Application
  -> Teste: tests/test_human_review_claim_use_case.py (happy path com fake/mock repo)
  -> Execução: RED esperado por ausência inicial do módulo src/agent_lab/human_review_claim_use_case.py
  -> Implementação GREEN: criação mínima de RecordHumanReviewClaimUseCase
  -> Validação: coordenação Domain -> Repo -> retorno HumanReviewClaim

Fatia 2: Falhas determinísticas de entrada e domínio antes de I/O
  -> Teste: tests/test_human_review_claim_use_case.py (workflow inválido, status != PENDING, cronologia inválida)
  -> Execução: verificar comportamento (RED se validação defensiva estiver ausente; GREEN por composição se delegada diretamente ao domínio)
  -> Implementação GREEN (se necessário): validação estrutural defensiva na Application
  -> Validação: comprovação de que append nunca é chamado quando Fase 1 falha

Fatia 3: Propagação fail-closed de falhas de persistência
  -> Teste: tests/test_human_review_claim_use_case.py (duplicate claim_id, corruption error)
  -> Execução: verificar comportamento (espera-se GREEN por composição se o Use Case não interceptar exceções)
  -> Implementação GREEN (se necessário): assegurar que nenhuma captura indevida de erro ocorra
  -> Validação: exceções propagam de forma fail-closed sem mascaramento

Fatia 4: Integração vertical pós-restart com repositório JSONL real
  -> Teste: tests/test_human_review_claim_use_case_integration.py
  -> Execução: verificar comportamento com JsonlHumanReviewClaimRepository real
  -> Implementação GREEN (se necessário): nenhuma alteração adicional caso a composição já esteja GREEN
  -> Validação: persistência física durável, múltiplos claims por workflow e recuperação pós-restart

Fatia 5: Public export no pacote raiz
  -> Teste: teste de importação de RecordHumanReviewClaimUseCase a partir de agent_lab
  -> Execução: RED se o símbolo ainda não estiver em __all__ / __init__.py; GREEN se já adicionado
  -> Implementação GREEN (se necessário): exportar RecordHumanReviewClaimUseCase em src/agent_lab/__init__.py
  -> Validação: símbolo importável publicamente na raiz do pacote

Regressão Canônica:
  -> python -m unittest discover -s tests -v (503 + novos testes GREEN)
```

---

## 9. Critérios de Aceite

- [ ] SPEC técnica aprovada por revisão humana antes de qualquer código funcional;
- [ ] Implementação de `RecordHumanReviewClaimUseCase` em `src/agent_lab/human_review_claim_use_case.py`;
- [ ] O Use Case recebe `claim_repository: HumanReviewClaimRepository` por injeção no construtor;
- [ ] Validação defensiva de entrada rejeita `workflow` não-`GovernanceWorkflow` com `TypeError`;
- [ ] Delegação integral da criação e validação do claim para `claim_pending_human_review(...)`;
- [ ] Falhas de domínio ocorrem em memória na Fase 1 com zero I/O no repositório;
- [ ] Persistência sequencial no repositório via `HumanReviewClaimRepository.append(...)`;
- [ ] Retorno direto da instância imutável `HumanReviewClaim`;
- [ ] Propagação *fail-closed* de `DuplicateHumanReviewClaimError` e `HumanReviewClaimCorruptionError` sem captura genérica;
- [ ] Testes unitários com fake/mock repository aprovados;
- [ ] Teste de integração vertical com `JsonlHumanReviewClaimRepository` real em JSONL temporário aprovado pós-restart;
- [ ] `RecordHumanReviewClaimUseCase` exportado em `src/agent_lab/__init__.py`;
- [ ] Baseline de 503 testes existentes permanece 100% GREEN em Python 3.11 / `unittest`;
- [ ] `git diff --check` permanece limpo e sem whitespace residual.

---

## 10. Definition of Done (DoD)

- [ ] SPEC 0091 aprovada formalmente por revisão humana;
- [ ] Branch de trabalho `feature/issue-91-record-human-review-claim-use-case` criada e isolada;
- [ ] Ciclo TDD executado com commits atômicos e rastreáveis;
- [ ] Todos os novos testes implementados exclusivamente via `unittest` em Python 3.11;
- [ ] Suíte completa de testes aprovada: `python -m unittest discover -s tests -v`;
- [ ] `git diff --check` limpo;
- [ ] Preflight e auditoria humana pré-PR realizados;
- [ ] Pull Request funcional aberto referenciando `Closes #91`;
- [ ] Status check obrigatório da CI aprovado;
- [ ] PR funcional mergeado na `main`;
- [ ] Closeout documental posterior atualizando `docs/PROJECT_COMPASS.md`, README Audit, PMP e roadmap.

---

## 11. Riscos e Mitigações

| Risco | Severidade | Mitigação Arquitetural |
| :--- | :--- | :--- |
| **Duplicação de regras de domínio na Application** | Alta | A classe não verifica `workflow.status` nem cronologias; delega integralmente à função pura `claim_pending_human_review(...)`. |
| **Falsa expectativa de locking/exclusividade** | Alta | A SPEC explicita que o Use Case apenas registra o fato; múltiplos claims para o mesmo `workflow_id` são permitidos e vigência permanece indefinida nesta v1. |
| **Mascaramento indevido de erros de persistência** | Alta | O método `execute` não possui blocos `except Exception`; permite que erros do repositório propaguem *fail-closed*. |
| **Criação de DTOs redundantes** | Média | A SPEC determina o retorno direto de `HumanReviewClaim`, sem introduzir `RecordHumanReviewClaimResult` nesta v1. |
| **Acoplamento com outras trilhas (Audit/Lifecycle)** | Alta | O Use Case injeta exclusivamente `HumanReviewClaimRepository`; zero chamadas para `AuditRepository` ou `WorkflowLifecycleRepository`. |

---

## 12. Arquivos Envolvidos

* **Novos Arquivos:**
  * `docs/specs/0091_record_human_review_claim_use_case_v1.md`
  * `src/agent_lab/human_review_claim_use_case.py`
  * `tests/test_human_review_claim_use_case.py`
  * `tests/test_human_review_claim_use_case_integration.py`
* **Arquivos Existentes Modificados:**
  * `src/agent_lab/__init__.py` (apenas adição do export público de `RecordHumanReviewClaimUseCase`)
