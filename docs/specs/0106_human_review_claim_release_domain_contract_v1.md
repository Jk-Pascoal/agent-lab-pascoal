# SPEC 0106 — Human Review Claim Release Domain Contract v1

> Especificação técnica do contrato de domínio puro, síncrono e em memória para representação
> do fato de encerramento voluntário de assunção (*release*) de um `HumanReviewClaim` no Agent Lab Pascoal.

---

## 1. Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0106` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#106` |
| **Título da Issue** | `Human Review Claim Release Domain Contract v1` |
| **Branch funcional** | `feature/issue-106-human-review-claim-release-domain-contract` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-07` |
| **Data do ambiente** | `2026-09-07` |
| **Última atualização** | `2026-09-07` |
| **Baseline de entrada** | `579 testes aprovados` (100% GREEN) |
| **Runner oficial** | `$env:PYTHONPATH="src"; py -3.11 -m unittest discover -s tests -v` |

---

## 2. Contexto Arquitetural

O **Agent Lab Pascoal** estabelece um pipeline estruturado para governança de materiais cadastrais PDM/BOM e orienta sua evolução pelo princípio fundacional:

```text
Repository preserva → Projection interpreta → Policy governa → Application coordena e aplica
```

Na trilha de assunção operacional (*Human Review Claim*), o sistema consolidou progressivamente os seguintes incrementos:
1. **Issue #85:** contrato puro de domínio em memória `HumanReviewClaim` e função `claim_pending_human_review`;
2. **Issue #88:** persistência append-only durável em JSONL via `JsonlHumanReviewClaimRepository`;
3. **Issue #91:** boundary de gravação na Camada de Aplicação (`RecordHumanReviewClaimUseCase`);
4. **Issue #94:** projeção pura factual de estado de claims (`project_human_review_claim_state` $\rightarrow$ `NO_CLAIM`, `SINGLE_CLAIM`, `MULTIPLE_CLAIMS`);
5. **Issue #97:** composição somente-leitura da fila pendente com estado factual de claims (`ListPendingHumanReviewsWithClaimStateUseCase`);
6. **Issue #100:** política pura de elegibilidade normativa em memória (`evaluate_reviewer_claim_eligibility`);
7. **Issue #103:** enforcement de elegibilidade em tempo de execução como gate obrigatório pré-write em `RecordHumanDecisionUseCase`.

Atualmente, o sistema conhece o início do ciclo de assunção (`HumanReviewClaim`), mas não possui uma representação formal de domínio para o término ou descontinuação voluntária desse claim antes da conclusão da revisão.

---

## 3. Problema e Justificativa

### 3.1 Problema

O modelo de domínio do Agent Lab possui hoje o fato imutável `HumanReviewClaim`, mas carece de um fato explícito que represente a desistência ou liberação voluntária dessa assunção pelo especialista enquanto o workflow permanece em `PENDING_HUMAN_REVIEW`.

Esse vácuo factual acarreta consequências operacionais e arquiteturais graves:
1. **Bloqueio Irreversível de Workflows:** Se um especialista assume um workflow e posteriormente precisa liberá-lo (ex.: engano, redistribuição de tarefas ou indisponibilidade), qualquer nova tentativa de assunção gera um segundo `HumanReviewClaim` no repositório append-only.
2. **Conflito Inescapável na Policy:** A projeção factual classifica múltiplos claims como `MULTIPLE_CLAIMS`. Por sua vez, a `Reviewer Claim Eligibility Policy` avalia `MULTIPLE_CLAIMS` obrigatoriamente como `MULTIPLE_CLAIMS_CONFLICT`, bloqueando permanentemente a deliberação no `RecordHumanDecisionUseCase` com `ReviewerNotEligibleError`.
3. **Ausência de Pré-condição Factual para Active Claim:** Sem o fato de domínio do *Release*, uma futura *Active Claim Projection* seria forçada a inventar regras sintéticas arbitrárias (como *Last-Claim-Wins*, *First-Claim-Wins*, sobrescrita destrutiva ou expiração por relógio), violando a separação canônica de que **Projeções interpretam fatos e não inventam autoridade ou regras de negócio**.

### 3.2 Justificativa Arquitetural

Assim como o ciclo temporal de governança exigiu a introdução simétrica de `WorkflowConcluded` para complementar `WorkflowOpened` (Issue #52), a trilha de claims necessita de um par simétrico imutável para registrar a liberação factual da assunção: `HumanReviewClaimRelease`.

Representar o release como fato de domínio puro em memória (zero-I/O) é a **pré-condição arquitetural mais correta** para viabilizar, em incrementos posteriores estritamente desacoplados, a persistência, a projeção de claims ativos e os casos de uso de liberação.

---

## 4. Distinções Epistemológicas Obrigatórias

Para assegurar a integridade do modelo, os seguintes limites conceituais são mantidos de forma estrita:

1. **`HumanReviewClaimRelease != HumanReviewClaim`:**
   - `HumanReviewClaim` representa o início factual da assunção voluntária de um workflow.
   - `HumanReviewClaimRelease` representa o término factual dessa assunção específica.
   - O release faz referência direta ao `claim_id` original, sem sobrescrevê-lo ou mutá-lo.

2. **`RELEASED CLAIM != REVIEWED WORKFLOW`:**
   - Liberar um claim **não conclui nem altera** o ciclo de governança do workflow.
   - O `GovernanceWorkflow` permanece inalterado em `WorkflowStatus.PENDING_HUMAN_REVIEW` com `review is None`.
   - Não existe e não será criado nenhum novo valor em `WorkflowStatus` (como `RELEASED` ou `UNCLAIMED`).

3. **`release de claim != conclusão de workflow`:**
   - Concluir um workflow é um ato de deliberação substantiva sobre o material (`HumanReview`).
   - Liberar um claim é um ato puramente operacional de abandono/devolução da assunção de análise.

4. **`release de claim != AuditEvent` e `release de claim != WorkflowLifecycleEvent`:**
   - O release pertence estritamente à Trilha de Claims.
   - A operação de release no domínio não emite eventos de auditoria nem eventos de ciclo de vida de workflow.

5. **`release factual != Active Claim Projection` e `release factual != Active Claim Policy`:**
   - O contrato de domínio limita-se a validar e instanciar o fato imutável do release em memória.
   - Ele não projeta se o workflow tem ou não um claim ativo no momento, nem define regras de priorização de fila.

---

## 5. Questões Resolvidas antes do TDD

Em conformidade com a governança da Issue #106, as cinco questões fundamentais de design foram analisadas e decididas:

### Questão 1: O `GovernanceWorkflow` deve realmente fazer parte da assinatura da função de release para que a invariante `PENDING_HUMAN_REVIEW` seja verificável no Domain?
**Decisão:** **SIM.**
**Justificativa:** No Agent Lab Pascoal, a integridade do domínio é auto-contida e não terceirizada para camadas externas. Na função canônica `claim_pending_human_review` (Issue #85), o `workflow` já integra a assinatura para validar se o workflow está pendente e se os timestamps são cronologicamente coerentes. Na função de release, exigir `workflow` garante que o domínio valide:
1. que `workflow` é `GovernanceWorkflow`;
2. que `workflow.workflow_id == claim.workflow_id`;
3. que `workflow.status is WorkflowStatus.PENDING_HUMAN_REVIEW` (o que implica deterministicamente `workflow.review is None` no modelo atual).
Não é ontologicamente válido no domínio liberar a assunção de um workflow que já foi deliberado e concluído (`WorkflowStatus.REVIEWED`). Exigir o workflow na assinatura impede a geração de fatos órfãos ou inconsistentes diretamente na raiz do domínio.

### Questão 2: `HumanReviewClaimRelease` deve carregar `released_by: VerifiedSpecialistIdentity` completo ou somente referência ao stable principal?
**Decisão:** Deve carregar **`released_by: VerifiedSpecialistIdentity` completo**.
**Justificativa:** Em todos os contratos do Agent Lab Pascoal (`HumanReview`, `HumanReviewClaim`, etc.), qualquer ato praticado por um especialista humano carrega uma instância imutável de `VerifiedSpecialistIdentity`. Armazenar a identidade verificada completa preserva a proveniência exata do evento (incluindo `verification_id` e `verified_at` correspondentes ao momento da liberação). A validação relacional de domínio compara o Principal Estável `(specialist_id, identity_provider, identity_subject)` dessa identidade para garantir equivalência com o claimant original, sem descartar os metadados de verificação.

### Questão 3: Há algum campo adicional realmente necessário para preservar causalidade e auditabilidade factual sem antecipar persistência?
**Decisão:** **NÃO.** Nenhum campo adicional é necessário.
**Justificativa:** Os campos propostos (`release_id`, `claim_id`, `workflow_id`, `released_by`, `released_at`) fornecem os elementos de causalidade e proveniência necessários para a V1 (`claim_id` e `workflow_id` para causalidade relacional, `released_by` para autoria e `released_at` para temporalidade). Um campo opcional de texto como `reason: str | None = None` introduziria arbítrio e validações de sanitização que não alteram a verdade factual da liberação, além de quebrar a simetria com `HumanReviewClaim` (que não possui campo `reason`).

### Questão 4: Há algum risco de duplicar conceitos existentes no domínio?
**Decisão:** **NÃO.**
**Justificativa:** O conceito é ortogonal a todos os objetos existentes. `HumanReviewClaimRelease` formaliza unicamente o término de `HumanReviewClaim`. Não colide nem duplica `HumanReview`, `CorrectionRequest`, `WorkflowConcluded` ou `MaterialRevision`.

### Questão 5: O nome “Release” é preferível a “Unclaim” dentro da linguagem ubíqua atual do projeto?
**Decisão:** **SIM, “Release” é estritamente preferível.**
**Justificativa:**
1. Na literatura técnica de gestão de recursos, locks e filas, os pares canônicos consagrados são `Claim / Release` e `Acquire / Release`.
2. O prefixo "Un-" ("Unclaim") tem conotação semântica de reversão destrutiva ou anulação de fatos passados (como "desfazer o claim"), contrariando a tese de imutabilidade e append-only do projeto. "Release", ao contrário, expressa a ação explícita e afirmativa de liberação/desistência no tempo presente, preservando a existência histórica do claim prévio.
3. No `PROJECT_COMPASS.md` (seções 3, 13 e 17) e no `README.md`, a terminologia do backlog canônico sempre registrou a operação como `release / unclaim`, priorizando o substantivo `release`.

---

## 6. Contratos de Domínio

### 6.1 Módulo e Localização

O contrato será introduzido no módulo existente:
```text
src/agent_lab/human_review_claim.py
```
**Justificativa de Coesão:** Manter `HumanReviewClaim`, `claim_pending_human_review`, `HumanReviewClaimRelease` e `release_human_review_claim` no mesmo módulo preserva a coesão ontológica da assunção de revisão, evita dependências circulares e segue o mesmo padrão de `src/agent_lab/workflow.py` (que agrupa `open_governance_workflow`, `open_correction_follow_up` e `conclude_governance_workflow`).

Os novos símbolos serão exportados no pacote raiz:
```text
src/agent_lab/__init__.py
```

---

### 6.2 Dataclass `HumanReviewClaimRelease`

Dataclass congelado (`frozen=True, slots=True`) representando o fato imutável de encerramento da assunção:

```python
@dataclass(frozen=True, slots=True)
class HumanReviewClaimRelease:
    release_id: str
    claim_id: str
    workflow_id: str
    released_by: VerifiedSpecialistIdentity
    released_at: datetime
```

#### Validações em `__post_init__` (Validações Intrínsecas):
1. **`release_id`:**
   - Deve ser instância de `str` (rejeição de outros tipos e de `bool` com `TypeError`);
   - Sanitizado via `.strip()`;
   - Não pode ser vazio ou composto exclusivamente por whitespace (`ValueError`).
   - O valor armazenado é sanitizado com `.strip()` via `object.__setattr__(self, "release_id", sanitized_release_id)`, seguindo a convenção de identidade própria do novo fato.
2. **`claim_id`:**
   - Deve ser instância de `str` (rejeição de outros tipos e de `bool` com `TypeError`);
   - Não pode ser vazio ou composto exclusivamente por whitespace (`ValueError`);
   - **Sem mutação/normalização silenciosa:** o valor é preservado exatamente como recebido, sem aplicação de `strip()` no valor armazenado.
3. **`workflow_id`:**
   - Deve ser instância de `str` (rejeição de outros tipos e de `bool` com `TypeError`);
   - Não pode ser vazio ou composto exclusivamente por whitespace (`ValueError`);
   - **Sem mutação/normalização silenciosa:** o valor é preservado exatamente como recebido, sem aplicação de `strip()` no valor armazenado.
4. **`released_by`:**
   - Deve ser instância de `VerifiedSpecialistIdentity` (`TypeError`).
5. **`released_at`:**
   - Deve ser instância de `datetime` (`TypeError`);
   - Deve ser explicitamente timezone-aware (`tzinfo is not None and utcoffset() is not None`), rejeitando datetimes naive com `ValueError`.
6. **Consistência temporal de verificação:**
   - `released_by.verified_at <= released_at` (rejeita verificação posterior ao release com `ValueError`, permitindo igualdade cronológica no boundary).

---

### 6.3 Função Pura de Domínio `release_human_review_claim`

Função canônica pura, síncrona e em memória para validar e emitir o release:

```python
def release_human_review_claim(
    workflow: GovernanceWorkflow,
    claim: HumanReviewClaim,
    *,
    release_id: str,
    releasing_specialist: VerifiedSpecialistIdentity,
    released_at: datetime,
) -> HumanReviewClaimRelease:
    ...
```

#### Validações Relacionais e Regras de Domínio (Ordem Fail-Closed Estrita):

1. **Validação Nominal de Tipos dos Argumentos:**
   - `workflow` deve ser instância de `GovernanceWorkflow` (`TypeError`);
   - `claim` deve ser instância de `HumanReviewClaim` (`TypeError`);
   - `releasing_specialist` deve ser instância de `VerifiedSpecialistIdentity` (`TypeError`);
   - `released_at` deve ser instância de `datetime` (`TypeError`).
2. **Validação Prévia de Timezone-Awareness em `released_at`:**
   - Antes de qualquer comparação temporal relacional, validar que `released_at` é timezone-aware:
     ```python
     if released_at.tzinfo is None or released_at.utcoffset() is None:
         raise ValueError("released_at must be timezone-aware")
     ```
   - Esta checagem estrita impede que o Python dispare seu `TypeError` incidental interno ao comparar datetime naive com o datetime aware de `claim.claimed_at`, garantindo a taxonomia contratual prevista (`ValueError`).
3. **Coerência Estrutural entre Workflow e Claim:**
   - `workflow.workflow_id == claim.workflow_id` por comparação textual exata; se divergir, levantar `ValueError("workflow_id mismatch between workflow and claim")`.
4. **Elegibilidade de Estado do Workflow:**
   - `workflow.status is WorkflowStatus.PENDING_HUMAN_REVIEW`; se for diferente (`WorkflowStatus.REVIEWED`), levantar `ValueError("workflow must be pending human review to release claim")`.
   - *Nota de design:* Como `GovernanceWorkflow.status` deriva diretamente de `review` (`PENDING_HUMAN_REVIEW` quando `review is None`, e `REVIEWED` quando `review is not None`), validar que o status é `PENDING_HUMAN_REVIEW` garante de forma exaustiva que `workflow.review is None`, dispensando verificações redundantes.
5. **Equivalência Estrita de Principal Estável:**
   - O especialista que libera (`releasing_specialist`) deve corresponder ao mesmo Principal Estável do especialista que assumiu o claim (`claim.specialist`):
     ```python
     is_same_principal = (
         releasing_specialist.specialist_id == claim.specialist.specialist_id
         and releasing_specialist.identity_provider == claim.specialist.identity_provider
         and releasing_specialist.identity_subject == claim.specialist.identity_subject
     )
     ```
   - Se `is_same_principal` for falso, levantar `ValueError("releasing specialist stable principal must match claimant stable principal")`.
   - **Regra de Isolamento de Metadados:** `verification_id` e `verified_at` não integram o Principal Estável. Uma nova sessão/verificação do mesmo especialista humano é perfeitamente válida e autorizada a realizar o release.
6. **Monotonicidade Temporal Relacional:**
   - `released_at >= claim.claimed_at` cronologicamente; se `released_at < claim.claimed_at`, levantar `ValueError("released_at must not be before claim claimed_at")`.
   - Igualdade temporal no boundary (`released_at == claim.claimed_at`) é expressamente permitida.
7. **Instanciação com IDs Causais Exatos:**
   - A função instancia `HumanReviewClaimRelease` repassando os identificadores diretamente do claim original:
     ```python
     return HumanReviewClaimRelease(
         release_id=release_id,
         claim_id=claim.claim_id,
         workflow_id=claim.workflow_id,
         released_by=releasing_specialist,
         released_at=released_at,
     )
     ```
8. **Garantia de Imutabilidade dos Parâmetros de Entrada:**
   - A instância de `workflow` permanece 100% inalterada;
   - A instância de `claim` permanece 100% inalterada;
   - Nenhum campo é mutado nos objetos recebidos.

---

## 7. Invariantes a Garantir

1. **Pureza e Zero I/O:** Nenhuma chamada a disco, rede, relógio de sistema (`datetime.now()`), banco de dados ou variáveis de ambiente.
2. **Determinismo Estrito:** Mesmas entradas produzem exatamente a mesma saída ou a mesma exceção.
3. **Imutabilidade Histórica:** O fato `HumanReviewClaim` não é alterado, cancelado ou sobrescrito na memória. O fato `HumanReviewClaimRelease` é gerado como entidade autônoma.
4. **Preservação do Workflow:** O `GovernanceWorkflow` permanece inalterado em `WorkflowStatus.PENDING_HUMAN_REVIEW` com `review = None`.
5. **Equivalência Canônica de Principal:** Somente o detentor do claim (mesmo `specialist_id`, `identity_provider` e `identity_subject`) pode voluntariamente liberá-lo nesta V1.
6. **Monotonicidade Causal:** `claim.claimed_at <= release.released_at`.

---

## 8. Escopo Negativo Explícito

NÃO faz parte desta Issue ou SPEC:
- Serialização versionada (`schema_version = 1`), deserialização ou envelopes JSONL para release;
- Protocolo ou implementação de repositório de releases (`JsonlHumanReviewClaimReleaseRepository`);
- Alterações em `JsonlHumanReviewClaimRepository` ou em seu arquivo JSONL;
- Application Use Cases (`ReleaseHumanReviewClaimUseCase`);
- Alteração na projeção factual `project_human_review_claim_state`;
- Criação de `ActiveClaimProjection`;
- Criação de `ActiveClaimPolicy`;
- Alterações na `Reviewer Claim Eligibility Policy` (`evaluate_reviewer_claim_eligibility`);
- Alterações no gate pré-write do `RecordHumanDecisionUseCase`;
- Políticas operacionais de assignment, ownership, winner, First-Claim-Wins ou Last-Claim-Wins;
- Force-release administrativo (liberação por terceiros, supervisores ou sistema);
- Transfer / reassignment direto de claim;
- Mecanismos de lease temporal, TTL, timeouts automáticos, cron jobs ou SLAs;
- Regra de histórico "claim já foi liberado anteriormente" (regras que dependem do histórico completo pertencem à Projection/Repository em incrementos futuros);
- Criação de novos estados em `WorkflowStatus`;
- Emissão de `AuditEvent` ou `WorkflowLifecycleEvent`;
- UI, CLI, APIs REST, multithreading ou distributed locks.

---

## 9. Estratégia de Testes (TDD)

A implementação será estritamente guiada por testes em `tests/test_human_review_claim.py`, mantendo a suíte de testes de assunção unificada e coesa:

### 9.1 Matriz de Testes do Dataclass `HumanReviewClaimRelease`
1. **Criação Válida:** Instanciação bem-sucedida com tipos corretos e timestamp timezone-aware;
2. **Imutabilidade (`frozen=True`):** Tentativa de modificar atributos levanta `FrozenInstanceError` / `AttributeError`;
3. **Validação e Sanitização de `release_id`:**
   - Tipos inválidos (`None`, `int`, `list`, `bool`) levantam `TypeError`;
   - String vazia ou contendo apenas espaços levanta `ValueError`;
   - Sanitização de espaços externos (`strip()`) armazenando o valor limpo.
4. **Validação de `claim_id`:**
   - Tipos inválidos (`None`, `int`, `bool`) levantam `TypeError`;
   - String vazia ou contendo apenas espaços levanta `ValueError`;
   - Preservação exata do valor recebido (sem normalização ou mutação).
5. **Validação de `workflow_id`:**
   - Tipos inválidos (`None`, `int`, `bool`) levantam `TypeError`;
   - String vazia ou contendo apenas espaços levanta `ValueError`;
   - Preservação exata do valor recebido (sem normalização ou mutação).
6. **Validação de `released_by`:**
   - Tipos inválidos levantam `TypeError`.
7. **Validação de `released_at`:**
   - Não-datetime levanta `TypeError`;
   - Datetime naive (sem `tzinfo` ou `utcoffset`) levanta `ValueError`.
8. **Validação Temporal de Verificação:**
   - `released_by.verified_at > released_at` levanta `ValueError`;
   - `released_by.verified_at == released_at` é aceito.

### 9.2 Matriz de Testes da Função `release_human_review_claim`
1. **Caso Nominal:** Release bem-sucedido com workflow pendente, claim válido, mesmo especialista e timestamp posterior;
2. **Boundary Temporal:** `released_at == claim.claimed_at` é aceito;
3. **Validações Nominais de Tipo:**
   - `workflow` inválido levanta `TypeError`;
   - `claim` inválido levanta `TypeError`;
   - `releasing_specialist` inválido levanta `TypeError`;
   - `released_at` inválido levanta `TypeError`.
4. **Validação Prévia de Timezone:**
   - `released_at` naive levanta `ValueError("released_at must be timezone-aware")`, sem que ocorra comparação temporal prévia ou `TypeError` incidental do Python.
5. **Incompatibilidade Relacional:**
   - `workflow.workflow_id != claim.workflow_id` levanta `ValueError("workflow_id mismatch between workflow and claim")`.
6. **Elegibilidade do Workflow:**
   - `workflow.status == WorkflowStatus.REVIEWED` levanta `ValueError("workflow must be pending human review to release claim")`.
7. **Monotonicidade Temporal Relacional:**
   - `released_at < claim.claimed_at` levanta `ValueError("released_at must not be before claim claimed_at")`.
8. **Equivalência de Principal Estável:**
   - Mesmo principal estável com `verification_id` e `verified_at` diferentes é **aceito com sucesso**;
   - `specialist_id` diferente levanta `ValueError`;
   - `identity_provider` diferente levanta `ValueError`;
   - `identity_subject` diferente levanta `ValueError`.
9. **Preservação Exata dos IDs do Claim:**
   - Os valores de `claim_id` e `workflow_id` no release gerado são exatamente idênticos aos do claim original recebido.
10. **Preservação de Estado e Imutabilidade:**
    - Instância de `workflow` original permanece 100% inalterada (`status`, `review`, timestamps);
    - Instância de `claim` original permanece 100% inalterada;
    - Nenhum efeito colateral em memória.

---

## 10. Critérios de Aceite

1. **Contrato Formal Implementado:** Dataclass `HumanReviewClaimRelease` e função pura `release_human_review_claim` implementados com tipagem estrita e validação fail-closed em `src/agent_lab/human_review_claim.py`;
2. **Exportação Pública:** Símbolos `HumanReviewClaimRelease` e `release_human_review_claim` exportados no pacote raiz `src/agent_lab/__init__.py`;
3. **Testes Unitários Abrangentes:** Testes explícitos cobrindo cada ramo de validação, boundary e caso nominal definido nesta SPEC em `tests/test_human_review_claim.py`;
4. **Regressão 100% GREEN:** Execução de `$env:PYTHONPATH="src"; py -3.11 -m unittest discover -s tests -v` com todos os 579 testes do baseline + novos testes unitários aprovados;
5. **Respeito aos Limites:** Zero linhas de código de persistência, projeção, use case, políticas de active claim ou mutação em workflow.
