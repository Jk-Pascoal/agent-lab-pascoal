# SPEC-0094 — Human Review Claim State Projection v1

> Especificação técnica da projeção pura, determinística e em memória (`read-only`)
> do estado factual de assunção de revisão humana (`HumanReviewClaim`) no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0094` |
| **Status** | `APPROVED` |
| **Issue relacionada** | `#94` |
| **Branch funcional** | `feature/issue-94-human-review-claim-state-projection` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-03` |
| **Data do ambiente** | `2026-09-03` |
| **Última atualização** | `2026-09-03` |
| **Baseline de entrada** | `509 testes aprovados` |
| **Runner oficial** | `unittest` / Python 3.11 |

---

## 1. Contexto

O **Agent Lab Pascoal** consolidou em seu núcleo normativo uma rigorosa separação em três trilhas persistentes complementares e desacopladas:
1. **Trilha de Lifecycle:** eventos de abertura e conclusão de workflow (`WorkflowOpened` v1/v2 e `WorkflowConcluded` v1) persistidos em JSONL via `JsonlWorkflowLifecycleRepository`, reidratados de forma pura por `rehydrate_workflow` e com a fila pendente projetada deterministicamente por `project_pending_human_review_queue`;
2. **Trilha de Auditoria:** eventos imutáveis de deliberação (`AuditEvent` com `schema_version = 1`) persistidos em JSONL via `JsonlAuditRepository`;
3. **Trilha de Human Review Claim:**
   - **Contrato de domínio em memória (Issue #85 / SPEC 0085):** entidade imutável `HumanReviewClaim` e função pura `claim_pending_human_review(...)` em `src/agent_lab/human_review_claim.py`;
   - **Persistência durável desacoplada (Issue #88 / SPEC 0088):** protocolo `HumanReviewClaimRepository` e implementação append-only `JsonlHumanReviewClaimRepository` com `schema_version = 1`, durabilidade física (`flush` + `os.fsync`) e permissão explícita de múltiplos claims para o mesmo `workflow_id`;
   - **Boundary de aplicação para gravação (Issue #91 / SPEC 0091):** classe `RecordHumanReviewClaimUseCase` em `src/agent_lab/human_review_claim_use_case.py` orquestrando validação em memória (Fase 1 / Zero I/O) e persistência no repositório (Fase 2).

Baseline de entrada verificado na branch `main`:

```text
Ran 509 tests in 1.980s
OK
```

Runner oficial canônico:

```powershell
python -m unittest discover -s tests -v
```

---

## 2. Separação Canônica de Camadas e Princípios Arquiteturais

Esta SPEC é governada pelo princípio mandatório do Agent Lab Pascoal:

```text
Application coordena.
Domain decide.
Repository preserva.
Projection interpreta.
```

### Invariantes e Separações Conceituais

1. **`Repository != Projection`:**
   - O `Repository` (`JsonlHumanReviewClaimRepository`) responde exclusivamente **quais fatos foram persistidos em disco** e em qual ordem física foram gravados. O repositório armazena todos os registros brutos sem interpretar regras de negócio, sem descartar claims concorrentes e sem eleger um vencedor.
   - A `Projection` (esta SPEC) é uma função pura e determinística em memória que recebe fatos de claims já persistidos ou em memória e **interpreta o estado factual de assunção** de um workflow. A projeção não executa I/O, não muta objetos, não altera repositórios e não inventa políticas arbitrárias.
2. **`HumanReviewClaim ≠ HumanReview`:** Assumir voluntariamente um workflow para análise é um fato operacional; não constitui deliberação, aprovação, reprovação ou solicitação de correção.
3. **`CLAIMED ≠ REVIEWED`:** O claim não altera o ciclo de governança de `GovernanceWorkflow`. Não existe o estado `WorkflowStatus.CLAIMED`. O workflow permanece estritamente em `WorkflowStatus.PENDING_HUMAN_REVIEW` com `review = None`.
4. **Descrever Fatos, Nunca Criar Políticas Inexistentes:**
   - A projeção deve estritamente **DESCREVER** os fatos existentes (`NO_CLAIM`, `SINGLE_CLAIM`, `MULTIPLE_CLAIMS`).
   - A projeção **NÃO** deve inventar regras operacionais de "claim ativo", "vencedor", "titular atual", "Last-Claim-Wins" ou "desempate", cuja autoridade e especificação pertencem à decisão humana de governança e não ao software.
5. **Zero I/O e Pureza Funcional:** A projeção opera exclusivamente sobre sequências fornecidas em memória; não lê arquivos, não escreve em disco e não instancia repositórios.
6. **Isolamento de Trilhas:** A interpretação de claims não emite `AuditEvent`, não emite `WorkflowLifecycleEvent` e não altera instâncias de `GovernanceWorkflow`.
7. **Eliminação de Estado Derivado Armazenado:**
   - O read-model armazena exclusivamente os fatos brutos projetados (`workflow_id` e a tupla `claims`).
   - Contagens, estados factuais e indicadores booleanos são propriedades computadas puras (`@property`), garantindo que seja impossível construir um read-model com estado internamente contraditório.

---

## 3. Problema e Justificativa

### Problema

Atualmente, o repositório `JsonlHumanReviewClaimRepository` armazena claims de forma append-only e permite que múltiplos claims sejam registrados para o mesmo `workflow_id` (por exemplo, especialistas distintos manifestando interesse no mesmo item, ou o mesmo especialista assumindo repetidamente).

No entanto, o sistema **não possui nenhuma função de projeção** capaz de inspecionar esses fatos e responder de forma tipada, imutável e determinística:
- "Este workflow possui claims associados?"
- "O workflow possui exatamente um claim inequívoco?"
- "O workflow possui múltiplos claims registrados no histórico?"

Sem um read-model padronizado:
1. Chamadores futuros (como novos Use Cases, adaptadores ou futuras projeções de fila) seriam tentados a inspecionar coleções brutas de claims de forma ad-hoc;
2. Haveria o risco crítico de chamadores implementarem regras arbitrárias de desempate (ex.: adotar o último registro via *Last-Claim-Wins* silencioso ou escolher o primeiro por ordem de append);
3. Workflows que não possuem nenhum claim registrado ficariam sem representação estruturada, dificultando diagnósticos claros de pendências não assumidas.

### Evidências

- O módulo `src/agent_lab/human_review_claim_repository.py` disponibiliza apenas as consultas brutas `list_by_workflow_id` e `list_all`, retornando tuplas não interpretadas na ordem física de inserção;
- Não existe um módulo `src/agent_lab/human_review_claim_projection.py`;
- `docs/PROJECT_COMPASS.md` registra a interpretação de claims ativos e status de fila como decisões deliberadamente adiadas na ausência de especificação formal.

---

## 4. Decisões de Design e Contrato

### 4.1 Assinatura da Projeção e Ordem de Execução

**Decisão:**
```python
def project_human_review_claim_state(
    workflow_id: str,
    claims: Sequence[HumanReviewClaim],
) -> HumanReviewClaimState:
    ...
```

**Justificativa Arquitetural:**
1. **Identidade Explícita de Workflow (`workflow_id: str`):**
   - Uma assinatura que recebesse apenas `claims: Sequence[HumanReviewClaim]` seria **incapaz** de representar corretamente o estado de zero claims (`claims = ()`), pois uma sequência vazia não carrega a identidade do workflow consultado.
   - Fornecer explicitamente `workflow_id` permite à projeção responder com precisão o estado factual `NO_CLAIM` para um workflow específico conhecido, mesmo quando nenhum claim tiver sido registrado para ele.
2. **Ordem Estrita de Execução Defensiva (Validar Antes de Filtrar):**
   Para coleções globais ou parciais de entrada, a função executa obrigatoriamente a seguinte ordem determinística:
   - **Etapa 1:** Validação estrutural de `workflow_id` (deve ser `str` e não-vazia após `.strip()`);
   - **Etapa 2:** Validação estrutural de `claims` (deve satisfazer `collections.abc.Sequence`);
   - **Etapa 3:** Validação integral e exaustiva de TODOS os elementos da sequência como instâncias de `HumanReviewClaim` (fail-closed antes de qualquer filtragem);
   - **Etapa 4:** Filtragem seletiva dos claims pertencentes ao workflow alvo (`claim.workflow_id == sanitized_workflow_id`);
   - **Etapa 5:** Ordenação canônica determinística dos claims filtrados `(claimed_at ASC, claim_id ASC)`;
   - **Etapa 6:** Instanciação e retorno do read-model imutável `HumanReviewClaimState(workflow_id=sanitized_workflow_id, claims=tuple(sorted_claims))`.
3. **Justificativa da Validação Prévia:**
   - Um elemento estruturalmente inválido (ex: `None`, `dict`, `int`) contido na sequência **NÃO** deve ser silenciosamente ignorado sob a premissa de que ficaria de fora do filtro do workflow alvo. A função falha imediatamente com `TypeError`.

### 4.2 Estados Factuais Candidatos

Para representar com fidelidade a realidade dos fatos persistidos sem inventar políticas operacionais, define-se o enum canônico:

```python
class HumanReviewClaimFactState(str, Enum):
    NO_CLAIM = "NO_CLAIM"
    SINGLE_CLAIM = "SINGLE_CLAIM"
    MULTIPLE_CLAIMS = "MULTIPLE_CLAIMS"
```

**Semântica dos Estados:**
- **`NO_CLAIM`:** Zero fatos de claim registrados para o `workflow_id`. O workflow está puramente não assumido.
- **`SINGLE_CLAIM`:** Exatamente 1 fato de claim registrado para o `workflow_id`. Não há ambiguidade factual no histórico.
- **`MULTIPLE_CLAIMS`:** 2 ou mais fatos de claim registrados para o `workflow_id`. O histórico contém multiplicidade factual de assunções.

**Proibição Estrita de Nomenclatura de Política:**
- É terminantemente proibido o uso de termos que induzam a direitos, prioridades ou vencedores inexistentes nesta v1, tais como: `ACTIVE`, `CURRENT`, `WINNER`, `OWNER`, `LATEST`, `VALID`, `PRIMARY`.
- Evita-se também classificar o estado como "concorrência" ou "conflito", pois dois registros no histórico atestam apenas **multiplicidade factual**; interpretar conflito ou corrida exigiria premissas sobre janelas temporais ou regras de negócio que não foram definidas.

### 4.3 Read-Model Imutável: `HumanReviewClaimState`

Para eliminar qualquer risco de estados internamente contraditórios (por exemplo, `claim_count` ou `state` divergindo da tupla `claims` real), os únicos campos armazenados são os fatos fundamentais:

```python
@dataclass(frozen=True, slots=True)
class HumanReviewClaimState:
    workflow_id: str
    claims: tuple[HumanReviewClaim, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.workflow_id, str) or isinstance(self.workflow_id, bool):
            raise TypeError("workflow_id must be a string")
        sanitized_wf = self.workflow_id.strip()
        if not sanitized_wf:
            raise ValueError("workflow_id must not be empty or whitespace")
        if self.workflow_id != sanitized_wf:
            object.__setattr__(self, "workflow_id", sanitized_wf)

        if not isinstance(self.claims, tuple):
            raise TypeError("claims must be a tuple")

        for idx, claim in enumerate(self.claims):
            if not isinstance(claim, HumanReviewClaim) or isinstance(claim, bool):
                raise TypeError(
                    f"claim at index {idx} must be a HumanReviewClaim instance"
                )
            if claim.workflow_id != sanitized_wf:
                raise ValueError(
                    f"claim at index {idx} has workflow_id {claim.workflow_id!r}, "
                    f"expected {sanitized_wf!r}"
                )

    @property
    def claim_count(self) -> int:
        return len(self.claims)

    @property
    def state(self) -> HumanReviewClaimFactState:
        count = self.claim_count
        if count == 0:
            return HumanReviewClaimFactState.NO_CLAIM
        if count == 1:
            return HumanReviewClaimFactState.SINGLE_CLAIM
        return HumanReviewClaimFactState.MULTIPLE_CLAIMS

    @property
    def is_unclaimed(self) -> bool:
        return self.state is HumanReviewClaimFactState.NO_CLAIM

    @property
    def has_claims(self) -> bool:
        return self.claim_count > 0

    @property
    def has_multiple_claims(self) -> bool:
        return self.state is HumanReviewClaimFactState.MULTIPLE_CLAIMS

    @property
    def sole_claim(self) -> HumanReviewClaim | None:
        if self.state is HumanReviewClaimFactState.SINGLE_CLAIM:
            return self.claims[0]
        return None
```

**Regras do Read-Model:**
- **Fonte única da verdade:** `claims` constitui a única fonte factual; `claim_count`, `state`, `is_unclaimed`, `has_claims`, `has_multiple_claims` e `sole_claim` são estritamente derivados de `self.claims`;
- **Impossibilidade de contradição:** Como `state` e `claim_count` não são campos do construtor, é impossível instanciar `HumanReviewClaimState` com um `claim_count` falso ou um `state` em desacordo com a cardinalidade de `claims`;
- **Tentativa de passar derivados no construtor:** Tentativas de instanciar passando `state=...` ou `claim_count=...` levantam `TypeError` de argumentos desconhecidos nativo de dataclasses com `slots=True`;
- **Imutabilidade:** `frozen=True, slots=True`, sem setters e sem estado mutável;
- **`sole_claim`:**
  - Retorna o único objeto `HumanReviewClaim` quando `state == SINGLE_CLAIM`;
  - Retorna `None` quando `state == NO_CLAIM` ou `state == MULTIPLE_CLAIMS`;
  - **Sentido semântico mandatório:** `sole_claim` significa estrita e literalmente **"o único fato de claim existente"**, e **NUNCA** "claim ativo", "vencedor de disputa" ou "titular do lock".

---

## 5. Determinismo e Ordenação Canônica

### 5.1 Ordenação Canônica de Apresentação

Para garantir independência integral da ordem de entrada dos registros em `claims`:
- Os claims associados ao workflow alvo são ordenados deterministicamente por:
  ```python
  key=lambda claim: (claim.claimed_at, claim.claim_id)
  ```
- **Tie-Break Determinístico:** Se dois claims tiverem exatamente o mesmo timestamp `claimed_at`, o desempate na ordenação ocorre pela ordem lexicográfica estrita de `claim.claim_id`.
- **Declaração Explícita de Não-Autoridade:**
  > Esta ordenação é estritamente um mecanismo de determinismo de apresentação do read-model. Ela **NÃO** constitui regra de *Last-Claim-Wins*, não concede precedência ou autoridade operacional a nenhum especialista e não indica quem deve deliberar o workflow.

### 5.2 Validações de Entrada e Tratamento de Erros (*Fail-Closed*)

1. **`workflow_id`:**
   - Se `not isinstance(workflow_id, str)` ou `isinstance(workflow_id, bool)`: levantar `TypeError("workflow_id must be a string")`;
   - Se `not workflow_id.strip()`: levantar `ValueError("workflow_id must not be empty or whitespace")`.
2. **`claims`:**
   - Se `not isinstance(claims, collections.abc.Sequence)` ou `isinstance(claims, (str, bytes, bytearray))`: levantar `TypeError("claims must be a Sequence of HumanReviewClaim")`;
   - Se qualquer item em `claims` não for `HumanReviewClaim` (ex: `None`, `dict`, `int`, etc.): levantar `TypeError(f"all items in claims must be HumanReviewClaim instances, got {type(item).__name__}")` **antes de qualquer filtragem por workflow_id**.
3. **Sequência Vazia (`claims = ()`):**
   - Comportamento válido e esperado;
   - Retorna `HumanReviewClaimState(workflow_id=sanitized_id, claims=())`, com `state = NO_CLAIM`, `claim_count = 0`.
4. **Claims de Outros Workflows:**
   - Itens que sejam instâncias válidas de `HumanReviewClaim`, mas cujo `claim.workflow_id != sanitized_id`, são filtrados e descartados da composição de `claims` do read-model resultante.
   - Se após a filtragem restarem 0 claims para aquele `workflow_id`, o resultado derivado é `NO_CLAIM`.

---

## 6. Confrontação com a Arquitetura Anterior

| Marco Anterior | Solução Adotada Anteriormente | Solução Nesta SPEC (SPEC-0094) | Coerência Arquitetural |
|---|---|---|---|
| **Issue #71** — *Material Revision Lineage Projection v1* | Recusou a criação de "latest revision" ou "canonical head" arbitrárias diante de bifurcações (`fork_predecessor_ids`) e múltiplas cabeças (`head_revision_ids`). | Recusa a criação de "active claim" ou "Last-Claim-Wins" diante de múltiplos claims (`MULTIPLE_CLAIMS`). | **Idêntica:** expõe a ambiguidade/multiplicidade factual em vez de escondê-la com políticas não especificadas. |
| **Issue #77** — *Pending Human Review Queue Projection v1* | Função pura em memória com zero I/O, operando sobre sequências de eventos e ordenação canônica determinística `(opened_at, workflow_id)`. | Função pura em memória com zero I/O, operando sobre sequências de claims e ordenação canônica determinística `(claimed_at, claim_id)`. | **Idêntica:** pureza funcional, ausência de efeitos colaterais e determinismo estável. |
| **Issue #85** — *Human Review Claim Domain Contract v1* | Dataclass congelada `HumanReviewClaim` imutável, `CLAIMED != REVIEWED`, `workflow.status` inalterado. | Consome `HumanReviewClaim` sem mutação; não introduz status `CLAIMED` no workflow. | **Total respeito:** preserva a integridade ontológica do claim e do workflow. |
| **Issue #88** — *Human Review Claim Persistence v1* | Permite múltiplos claims para o mesmo `workflow_id` em JSONL append-only na ordem física de gravação. | Lê esses múltiplos claims persistidos e classifica fielmente como `MULTIPLE_CLAIMS` sem descartar nenhum registro. | **Total respeito:** `Repository != Projection`; o repositório preserva a história bruta, a projeção interpreta. |
| **Issue #91** — *Record Human Review Claim Application Use Case v1* | Boundary de gravação em duas fases (Domínio com zero I/O $\rightarrow$ Persistência) sem eleger claim ativo. | Read-model de leitura pura que reflete com exatidão os fatos persistidos pelo Use Case. | **Total respeito:** fecha a contrapartida de interpretação da trilha de claims. |

---

## 7. Escopo Detalhado

### Incluído (In-Scope)

1. **Módulo de Projeção (`src/agent_lab/human_review_claim_projection.py`):**
   - Enum `HumanReviewClaimFactState` com os valores `NO_CLAIM`, `SINGLE_CLAIM`, `MULTIPLE_CLAIMS`;
   - Dataclass imutável `HumanReviewClaimState` (`frozen=True, slots=True`) com campos apenas factuais (`workflow_id`, `claims`) e propriedades derivadas;
   - Função pura `project_human_review_claim_state(workflow_id: str, claims: Sequence[HumanReviewClaim]) -> HumanReviewClaimState` com validação prévia exaustiva fail-closed;
   - Ordenação determinística de apresentação `(claimed_at ASC, claim_id ASC)`;
2. **Exportação Pública no Pacote Raiz (`src/agent_lab/__init__.py`):**
   - Exportação de `HumanReviewClaimFactState`, `HumanReviewClaimState` e `project_human_review_claim_state`;
3. **Testes Unitários (`tests/test_human_review_claim_projection.py`):**
   - Caso `NO_CLAIM`: sequência vazia `claims = ()` e sequência contendo apenas claims de outros workflows;
   - Caso `SINGLE_CLAIM`: exatamente um claim correspondente; comprovação de `sole_claim`, `has_claims == True`, `has_multiple_claims == False`, `is_unclaimed == False`;
   - Caso `MULTIPLE_CLAIMS`: dois ou mais claims para o mesmo `workflow_id`; comprovação de `sole_claim is None`, `has_multiple_claims == True`, `claim_count == len(claims)`;
   - Independência da ordem de entrada: permutações de entrada geram exatamente a mesma tupla `claims` canonicamente ordenada;
   - Tie-break por `claim_id` em claims com mesmo `claimed_at`;
   - Filtragem seletiva: preservação apenas dos claims do `workflow_id` alvo e descarte de claims de outros workflows válidos;
   - Derivação pura do read-model: comprovação de que `claim_count == len(state.claims)` e `state` dependem unicamente da cardinalidade de `claims`;
   - Rejeição de argumentos derivados no construtor de `HumanReviewClaimState`: tentar passar `state=...` ou `claim_count=...` levanta `TypeError`;
   - Validações defensivas fail-closed:
     - `workflow_id` não-string ou booleano (`TypeError`);
     - `workflow_id` vazio ou somente whitespace (`ValueError`);
     - `claims` não-sequência (`TypeError`);
     - item de `claims` não-`HumanReviewClaim` falha imediatamente com `TypeError`, inclusive em coleções com claims de múltiplos workflows e itens inválidos que estariam fora do filtro;
   - Imutabilidade comprovada: tentativa de mutação de atributos em `HumanReviewClaimState` levanta `FrozenInstanceError`;
4. **Testes de Integração Vertical Pós-Restart (`tests/test_human_review_claim_projection_integration.py`):**
   - Comprovação do pipeline vertical completo com persistência real em JSONL:
     1. Criação de arquivo JSONL com múltiplos claims via `JsonlHumanReviewClaimRepository`;
     2. Simulação de encerramento do processo e nova instância do repositório;
     3. Leitura via `repository.list_all()` ou `repository.list_by_workflow_id()`;
     4. Projeção com `project_human_review_claim_state`;
     5. Comprovação da correta derivação de `NO_CLAIM`, `SINGLE_CLAIM` e `MULTIPLE_CLAIMS` sobre dados reais persistidos;
5. **Preservação Integral do Baseline:**
   - 100% dos 509 testes existentes mantidos GREEN em Python 3.11 / `unittest`.

### Explicitamente Fora de Escopo (Out of Scope)

- **Claim Ativo / Active Claim / Current Claim / Winner / Owner;**
- **Vigência temporal, janelas de validade, TTL ou expiração;**
- **Exclusividade, locking, lease, mutex ou checkout;**
- **Políticas de Last-Claim-Wins ou desempate operacional;**
- **Atribuição gerencial compulsória (*assignment*) ou *ownership*;**
- **Operações de ciclo de vida de claims (`unclaim`, `release`, `transfer`, revogação);**
- **SLAs de revisão ou priorização operacional de fila;**
- **Projeção composta de fila com claims (`Queue with Claim State`);**
- **Application Use Case para consulta agregada da fila com claims;**
- **Verificação de consistência cruzada entre claims e auditoria (`Audit-Claim Consistency Check`);**
- **Qualquer alteração nos módulos de domínio existentes (`GovernanceWorkflow`, `HumanReviewClaim`);**
- **Interfaces externas (UI Streamlit, endpoints REST, comandos CLI);**
- **Processamento assíncrono ou concorrência multiprocesso;**
- **Pressões arquiteturais P-07 (Escala 100k+ SKUs) e P-08 (Material Supersession / Replacement).**

---

## 8. Estratégia de Implementação (Micro-TDD Planejado)

A implementação seguirá ciclos estritos de micro-TDD em pequenas fatias atômicas orientadas a evidência. Nenhuma falha artificial será criada se um comportamento for garantido por composição.

### Fatias Planejadas

```text
Fatia 1: Read-Model Puramente Factual e Projeção Básica para Caso NO_CLAIM
  -> Teste: test_no_claim_with_empty_sequence e test_no_claim_when_no_matching_workflow
  -> Execução: RED genuíno (módulo src/agent_lab/human_review_claim_projection.py não existe)
  -> Implementação GREEN: definir HumanReviewClaimFactState, HumanReviewClaimState (com workflow_id e claims apenas) e project_human_review_claim_state
  -> Validação: NO_CLAIM derivado com tupla vazia, claim_count=0 e propriedades corretas

Fatia 2: Caso SINGLE_CLAIM e Comportamento de sole_claim
  -> Teste: test_single_claim_projection_and_sole_claim
  -> Execução: comprovação do comportamento
  -> Implementação GREEN: derivação pura de SINGLE_CLAIM a partir de len(claims) == 1 e exposição de sole_claim
  -> Validação: sole_claim retorna o claim único, is_unclaimed=False, has_claims=True

Fatia 3: Caso MULTIPLE_CLAIMS e Filtragem por workflow_id
  -> Teste: test_multiple_claims_projection e test_filters_claims_by_workflow_id
  -> Execução: comprovação do comportamento
  -> Implementação GREEN: agrupamento/filtragem por workflow_id e estado MULTIPLE_CLAIMS com sole_claim=None
  -> Validação: múltiplos claims representados sem eleição de vencedor

Fatia 4: Ordenação Canônica Determinística e Tie-Break
  -> Teste: test_canonical_sorting_independent_of_input_order e test_tie_break_by_claim_id
  -> Execução: comprovação de invariância à ordem de entrada
  -> Implementação GREEN: sorted(filtered_claims, key=lambda c: (c.claimed_at, c.claim_id))
  -> Validação: saída idêntica para qualquer permutação da sequência de entrada

Fatia 5: Validação Defensiva Estrita (Validação Prévia à Filtragem) e Fail-Closed
  -> Teste:
     - rejeição de workflow_id inválido/vazio
     - claims não-Sequence
     - item não-HumanReviewClaim em coleção global falha com TypeError ANTES de qualquer filtragem
     - prova de que claim_count == len(claims) e state são exclusivamente derivados
     - construtor de HumanReviewClaimState rejeita argumentos state e claim_count com TypeError
     - FrozenInstanceError comprovado
  -> Execução: checagens fail-closed
  -> Implementação GREEN: validação prévia exaustiva na projeção e no __post_init__ do read-model
  -> Validação: propagação estrita de TypeError e ValueError

Fatia 6: Exportação Pública no Pacote Raiz
  -> Teste: importação a partir do namespace agent_lab
  -> Execução: RED se ausente em __all__; GREEN após adição
  -> Implementação GREEN: exportar símbolos em src/agent_lab/__init__.py
  -> Validação: símbolos acessíveis publicamente

Fatia 7: Teste de Integração Vertical Pós-Restart
  -> Teste: tests/test_human_review_claim_projection_integration.py
  -> Execução: pipeline com JsonlHumanReviewClaimRepository real em JSONL
  -> Implementação GREEN: comprovação composicional sem alteração de código
  -> Validação: persistência em disco -> restart simulado -> projeção fiel

Regressão Canônica:
  -> python -m unittest discover -s tests -v (509 + novos testes GREEN)
```

---

## 9. Critérios de Aceite

- [ ] SPEC técnica aprovada formalmente por revisão humana antes de qualquer alteração em `src/` ou `tests/`;
- [ ] Implementação de `src/agent_lab/human_review_claim_projection.py` com o enum `HumanReviewClaimFactState`, o dataclass `HumanReviewClaimState` e a função pura `project_human_review_claim_state`;
- [ ] `HumanReviewClaimState` armazena exclusivamente `workflow_id: str` e `claims: tuple[HumanReviewClaim, ...]`;
- [ ] `state`, `claim_count`, `is_unclaimed`, `has_claims`, `has_multiple_claims` e `sole_claim` são estritamente propriedades derivadas (`@property`) sem armazenamento redundante;
- [ ] Tentativa de instanciar `HumanReviewClaimState` com argumentos `state` ou `claim_count` rejeitada com `TypeError`;
- [ ] `workflow_id` validado fail-closed (`TypeError` para não-string/bool, `ValueError` para string vazia/whitespace);
- [ ] `claims` validado fail-closed (`TypeError` para não-Sequence);
- [ ] Validação prévia e exaustiva: qualquer elemento em `claims` que não seja `HumanReviewClaim` levanta `TypeError` imediatamente, antes de qualquer filtragem de workflow;
- [ ] Retorno fiel de `HumanReviewClaimFactState.NO_CLAIM` quando a sequência for vazia ou não contiver claims para o `workflow_id`;
- [ ] Retorno fiel de `HumanReviewClaimFactState.SINGLE_CLAIM` e propriedade `sole_claim` preenchida quando houver exatamente 1 claim;
- [ ] Retorno fiel de `HumanReviewClaimFactState.MULTIPLE_CLAIMS` e propriedade `sole_claim is None` quando houver $\ge 2$ claims;
- [ ] Ordenação canônica determinística `(claimed_at ASC, claim_id ASC)` comprovada em testes de permutação;
- [ ] `sole_claim` documentado e testado estritamente como "único fato existente", sem alegação de "claim ativo" ou precedência;
- [ ] `HumanReviewClaimState` imutável (`FrozenInstanceError` em tentativa de mutação);
- [ ] Teste de integração vertical comprovando persistência em arquivo JSONL real com `JsonlHumanReviewClaimRepository` e projeção correta pós-restart;
- [ ] Exportação pública de `HumanReviewClaimFactState`, `HumanReviewClaimState` e `project_human_review_claim_state` em `src/agent_lab/__init__.py`;
- [ ] Preservação de 100% dos 509 testes existentes no baseline (`python -m unittest discover -s tests -v`);
- [ ] `git diff --check` limpo, sem erros de whitespace.

---

## 10. Definition of Done (DoD)

- [ ] SPEC 0094 aprovada por revisão humana;
- [ ] Branch `feature/issue-94-human-review-claim-state-projection` isolada e ativa;
- [ ] Ciclo TDD executado com commits atômicos e mensagens padronizadas;
- [ ] Todos os novos testes implementados exclusivamente via `unittest` em Python 3.11;
- [ ] Suíte canônica 100% aprovada: `python -m unittest discover -s tests -v`;
- [ ] `git diff --check` limpo;
- [ ] Preflight e auditoria pré-PR realizados;
- [ ] Pull Request aberto referenciando `Closes #94`;
- [ ] Status check obrigatório da CI aprovado;
- [ ] PR funcional mergeado na `main`;
- [ ] Closeout documental posterior atualizando `docs/PROJECT_COMPASS.md`, README Audit, PMP e roadmap.

---

## 11. Riscos e Mitigações

| Risco | Severidade | Mitigação Arquitetural |
|---|---|---|
| **Inconsistência interna por campos redundantes** | Crítica | Eliminou-se o armazenamento de `state` e `claim_count`; todas as informações são propriedades derivadas exclusivamente da tupla `claims`. |
| **Interpretação errônea de `sole_claim` como "claim ativo"** | Alta | A documentação da SPEC e as docstrings explicitam que `sole_claim` significa unicamente que existe 1 fato isolado, sem promessa de lock ou exclusividade. |
| **Invenção inadvertida de Last-Claim-Wins** | Crítica | A projeção classifica $\ge 2$ claims como `MULTIPLE_CLAIMS` e define `sole_claim = None`, recusando a escolha do mais recente. A ordenação é declarada como puro determinismo de apresentação. |
| **Ocultação de dados inválidos em coleções globais** | Alta | A validação estrutural de tipo ocorre sobre toda a coleção de entrada antes da filtragem, levantando `TypeError` imediatamente caso haja elementos corrompidos. |
| **Acoplamento prematuro com a fila de pendências** | Média | A projeção é mantida estritamente focada em claims (`HumanReviewClaimState`), deixando a composição de fila para uma fatia posterior dedicada (`Queue with Claim State`). |

---

## 12. Arquivos Envolvidos

* **Novos Arquivos:**
  * `docs/specs/0094_human_review_claim_state_projection_v1.md`
  * `src/agent_lab/human_review_claim_projection.py`
  * `tests/test_human_review_claim_projection.py`
  * `tests/test_human_review_claim_projection_integration.py`
* **Arquivos Existentes Modificados:**
  * `src/agent_lab/__init__.py` (apenas adição dos exports públicos)
