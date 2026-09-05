# SPEC 0100 — Reviewer Claim Eligibility Policy v1

> Especificação técnica da política pura, determinística e em memória de autoridade normativa
> e elegibilidade de revisores (`Reviewer Claim Eligibility Policy`) baseada no estado factual de claims no Agent Lab Pascoal.

---

## 1. Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0100` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#100` |
| **Título da Issue** | `Reviewer Claim Eligibility Policy v1` |
| **Branch funcional** | `feature/issue-100-reviewer-claim-eligibility-policy` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-05` |
| **Data do ambiente** | `2026-09-05` |
| **Última atualização** | `2026-09-05` |
| **Baseline de entrada** | `549 testes aprovados` |
| **Runner oficial** | `unittest` / Python 3.11.9 |

---

## 2. Contexto Arquitetural

O **Agent Lab Pascoal** consolidou progressivamente sua trilha de Human Review Claim através de incrementos estritamente desacoplados e orientados a responsabilidade única:

1. **Issue #85 (Contrato de Domínio em Memória):** introduziu o dataclass imutável `HumanReviewClaim` e a função pura `claim_pending_human_review(...)` em `src/agent_lab/human_review_claim.py`, formalizando o fato operacional de assunção de um workflow pendente;
2. **Issue #88 (Persistência Durável Desacoplada):** introduziu o protocolo `HumanReviewClaimRepository` e a implementação append-only `JsonlHumanReviewClaimRepository` (`schema_version = 1`), permitindo múltiplos claims para o mesmo `workflow_id`;
3. **Issue #91 (Boundary de Aplicação para Gravação):** introduziu `RecordHumanReviewClaimUseCase` em `src/agent_lab/human_review_claim_use_case.py`, orquestrando a validação de domínio em memória (zero-I/O) e a escrita sequencial no repositório;
4. **Issue #94 (Projeção Factual de Estado de Claims):** introduziu a projeção pura em memória `project_human_review_claim_state` e o read-model `HumanReviewClaimState` em `src/agent_lab/human_review_claim_projection.py`, categorizando factual e deterministicamente o histórico em `NO_CLAIM`, `SINGLE_CLAIM` e `MULTIPLE_CLAIMS`;
5. **Issue #97 (Composição da Fila com Estado Factual de Claims):** introduziu `ListPendingHumanReviewsWithClaimStateUseCase` em `src/agent_lab/pending_human_reviews_with_claim_state_use_case.py`, combinando de forma somente-leitura e com snapshot local único por repositório os workflows pendentes com seus respectivos claims;
6. **Issue #100 (Esta Especificação):** introduz a primeira camada de política de governança pura de elegibilidade e autoridade normativa em memória.

### Direção Canônica de Dependências

A arquitetura do projeto segue a hierarquia linear e unidirecional:

```text
Repository preserva (fatos físicos brutos na ordem de append)
    ↓
Projection interpreta (read-model factual: HumanReviewClaimState)
    ↓
Policy governa elegibilidade normativa (regras puras de autoridade)
    ↓
Application coordena (orquestra verificação e execução entre camadas)
```

> [!IMPORTANT]
> **Delimitação de Camada:**
> A Issue #100 introduz o módulo puro de Policy/Governança. Ela **NÃO** realiza ainda o enforcement dessa regra na camada de Application. O caso de uso `RecordHumanDecisionUseCase` permanece 100% inalterado nesta fatia.

---

## 3. Problema

Embora o sistema registre, persista, projete e componha os fatos de assunção voluntária (`HumanReviewClaim`), **inexiste atualmente qualquer contrato ou política explícita** que determine se uma identidade de especialista (`VerifiedSpecialistIdentity`) tem autoridade normativa para deliberar sobre um workflow a partir do seu estado factual de claims.

Atualmente, `RecordHumanDecisionUseCase` recebe `reviewer_identity` e orquestra a conclusão do workflow sem consultar a trilha de claims:
- Se o workflow possui `SINGLE_CLAIM` atribuído ao Especialista A, o Especialista B pode submeter deliberação diretamente e a aplicação conclui o ciclo;
- Se o workflow possui `MULTIPLE_CLAIMS` (disputa/multiplicidade em aberto), qualquer revisor pode deliberar sem impedimento;
- Se o workflow possui `NO_CLAIM`, qualquer revisor pode deliberar sem antes registrar compromisso operacional de assunção.

A presente especificação formaliza a regra pura e normativa de elegibilidade necessária para preencher essa lacuna de governança, preparando a base conceitual para futura integração na camada de coordenação.

---

## 4. Objetivo

Definir e implementar a **Reviewer Claim Eligibility Policy v1** no módulo dedicado:
```text
src/agent_lab/reviewer_eligibility_policy.py
```

A especificação estabelece:
1. O enum canônico `ReviewerEligibilityStatus`;
2. O read-model imutável `ReviewerEligibilityDecision`;
3. A função pura canônica `evaluate_reviewer_claim_eligibility(claim_state, reviewer_identity)`;
4. O contrato formal de equivalência de Principal Estável (`Stable Principal Identity`);
5. Validação defensiva estrita e comportamento *fail-closed*;
6. Suíte de testes unitários abrangente em `tests/test_reviewer_eligibility_policy.py`.

---

## 5. Contratos

### 5.1 ReviewerEligibilityStatus

Enum canônico tipado (`str, Enum`) definindo os quatro status possíveis de elegibilidade:

```python
class ReviewerEligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    CLAIM_REQUIRED = "CLAIM_REQUIRED"
    CLAIMANT_MISMATCH = "CLAIMANT_MISMATCH"
    MULTIPLE_CLAIMS_CONFLICT = "MULTIPLE_CLAIMS_CONFLICT"
```

**Semântica dos Valores:**
- `ELIGIBLE`: o revisor coincide com o principal estável do único claimant registrado para o workflow;
- `CLAIM_REQUIRED`: o workflow não possui claims registrados (`NO_CLAIM`); claim é pré-requisito mandatório para autoridade de revisão derivada desta política;
- `CLAIMANT_MISMATCH`: o workflow possui exatamente um claim (`SINGLE_CLAIM`), porém o revisor pretendente diverge do principal estável do claimant;
- `MULTIPLE_CLAIMS_CONFLICT`: o workflow possui multiplicidade de claims (`MULTIPLE_CLAIMS`); conflito operacional não resolvido, nenhum revisor é elegível.

> [!NOTE]
> Nenhum status adicional é permitido na v1.

### 5.2 ReviewerEligibilityDecision

Dataclass congelado imutável que transporta a decisão normativa resultante:

```python
@dataclass(frozen=True, slots=True)
class ReviewerEligibilityDecision:
    status: ReviewerEligibilityStatus

    def __post_init__(self) -> None:
        if not isinstance(self.status, ReviewerEligibilityStatus) or isinstance(self.status, bool):
            raise TypeError("status must be a ReviewerEligibilityStatus instance")

    @property
    def is_eligible(self) -> bool:
        return self.status is ReviewerEligibilityStatus.ELIGIBLE

    @property
    def reason(self) -> str:
        if self.status is ReviewerEligibilityStatus.ELIGIBLE:
            return "Reviewer matches claimant stable principal on single claim."
        if self.status is ReviewerEligibilityStatus.CLAIM_REQUIRED:
            return "Workflow has no claim recorded; claim is required prior to review."
        if self.status is ReviewerEligibilityStatus.CLAIMANT_MISMATCH:
            return "Reviewer stable principal does not match sole claimant."
        return "Workflow has multiple claims; operational conflict must be resolved externally."
```

**Regras Mandatórias do Read-Model:**
1. **Fonte Única da Verdade:** `status` é o único campo armazenado no construtor;
2. **Rejeição Defensiva:** `__post_init__` valida que `status` é estritamente instância de `ReviewerEligibilityStatus` (`TypeError` para strings brutas, booleanos ou outros tipos);
3. **Propriedades Puramente Derivadas:** `is_eligible` e `reason` são propriedades `@property` computadas deterministicamente a partir de `self.status`;
4. **Proibição de Estado Redundante:** é expressamente proibido aceitar argumentos `is_eligible` ou `reason` no construtor;
5. **Imutabilidade Estrita:** `@dataclass(frozen=True, slots=True)`. Qualquer tentativa de mutação levanta `FrozenInstanceError`.

---

## 6. Semântica da Policy

### 6.1 Caso `NO_CLAIM`
- **Classificação:** `ReviewerEligibilityStatus.CLAIM_REQUIRED`;
- **Elegibilidade:** `is_eligible == False`;
- **Regra:** O claim prévio é pré-requisito mandatório para que um especialista tenha autoridade para deliberar sobre o workflow sob esta política;
- **Sem Permissividade:** A v1 não introduz parâmetro `allow_unclaimed`, flags de bypass ou modos permissivos.

### 6.2 Caso `SINGLE_CLAIM`
- **Inspeção:** A Policy obtém o claim único via `claim_state.sole_claim`;
- **Comparação:** O principal do `reviewer_identity` é comparado contra o principal de `sole_claim.specialist`;
- **Resultado:**
  - Se os principais coincidem exatamente $\rightarrow$ `ReviewerEligibilityStatus.ELIGIBLE` (`is_eligible == True`);
  - Se os principais divergem $\rightarrow$ `ReviewerEligibilityStatus.CLAIMANT_MISMATCH` (`is_eligible == False`).

### 6.3 Caso `MULTIPLE_CLAIMS`
- **Classificação:** `ReviewerEligibilityStatus.MULTIPLE_CLAIMS_CONFLICT`;
- **Elegibilidade:** `is_eligible == False` para qualquer especialista;
- **Ausência de Winner:** Nenhum revisor é elegível e nenhum vencedor é eleito;
- **Invariância Absoluta à Identidade:**
  A cardinalidade factual pertence estritamente à Projection (`HumanReviewClaimState` em `src/agent_lab/human_review_claim_projection.py`). A Policy **NÃO** deduplica, não agrupa e não reinterpreta claims por especialista.
  - Dois claims de especialistas diferentes $\rightarrow$ `MULTIPLE_CLAIMS_CONFLICT`;
  - Dois claims do **mesmo** principal estável $\rightarrow$ `MULTIPLE_CLAIMS_CONFLICT`.

---

## 7. Equivalência de Principal Estável (Stable Principal Identity)

Para comparar a identidade do claimant com a do reviewer, a Policy adota o conceito de **Principal Estável**:

### 7.1 Campos Pertencentes ao Principal Estável
1. `specialist_id: str`
2. `identity_provider: str`
3. `identity_subject: str`

A equivalência entre dois especialistas ocorre se, e somente se, a tupla canônica for idêntica:
```text
(a.specialist_id, a.identity_provider, a.identity_subject) == (b.specialist_id, b.identity_provider, b.identity_subject)
```

### 7.2 Regras Estritas de Comparação Textual Exata
A Policy realiza comparação textual exata (`==`) sobre as strings já higienizadas e validadas por `VerifiedSpecialistIdentity`.

A Policy **NÃO** deve aplicar:
- `strip()` adicional como regra semântica;
- `casefold()`, `lower()` ou `upper()`;
- Resolução de sinônimos, aliases ou normalizações de domínio para provedor ou sujeito;
- Coerção implícita de tipos.

Divergências de maiúsculas/minúsculas (ex.: `"CORP_IDP"` vs `"corp_idp"`) são tratadas estritamente como identidades divergentes (`CLAIMANT_MISMATCH`).

### 7.3 Isolamento de Proveniência de Sessão
Os seguintes campos representam verificação efêmera / proveniência de sessão e **NÃO** pertencem ao principal estável:
- `verification_id`
- `verified_at`

Dois objetos `VerifiedSpecialistIdentity` com mesmo principal estável, porém com `verification_id` ou `verified_at` distintos (como em renovação de token ou nova autenticação em momentos diferentes), são considerados o **mesmo principal** para efeito desta política.

---

## 8. Ordem Determinística de Avaliação

A função `evaluate_reviewer_claim_eligibility` executa o seguinte fluxo determinístico:

```text
[Entrada: claim_state, reviewer_identity]
                 │
                 ▼
1. Validação Defensiva de Tipos
   - claim_state é HumanReviewClaimState? (senão: raise TypeError)
   - reviewer_identity é VerifiedSpecialistIdentity? (senão: raise TypeError)
                 │
                 ▼
2. Inspeção do Estado Factual da Projeção
   - Inspeciona claim_state.state
                 │
         ┌───────┼─────────────────────────┐
         │                                 │
         ▼                                 ▼
   case NO_CLAIM:                 case MULTIPLE_CLAIMS:
   retorna CLAIM_REQUIRED         retorna MULTIPLE_CLAIMS_CONFLICT
   (is_eligible = False)          (is_eligible = False)
         │
         ▼
   case SINGLE_CLAIM:
   obter sole_claim = claim_state.sole_claim
   extrair principal_claimant = (sole_claim.specialist.specialist_id, ...)
   extrair principal_reviewer = (reviewer_identity.specialist_id, ...)
   comparar principal_claimant == principal_reviewer (textual exato)
         │
         ├───────────────────────────────┐
         ▼                               ▼
   se True:                        se False:
   retorna ELIGIBLE                retorna CLAIMANT_MISMATCH
   (is_eligible = True)            (is_eligible = False)
```

> [!IMPORTANT]
> A Policy **NÃO** recalcula `len(claim_state.claims)` nem filtra a lista interna de claims para redefinir o estado. Ela consome diretamente a propriedade `claim_state.state` da projeção oficial.

---

## 9. Comportamento Fail-Closed e Pureza

### Fail-Closed
- `claim_state` não-`HumanReviewClaimState` $\rightarrow$ `TypeError`;
- `reviewer_identity` não-`VerifiedSpecialistIdentity` $\rightarrow$ `TypeError`;
- `status` não-`ReviewerEligibilityStatus` no construtor de `ReviewerEligibilityDecision` $\rightarrow$ `TypeError`;
- Tentativa de passar argumentos desconhecidos (`is_eligible`, `reason`) $\rightarrow$ `TypeError`;
- Nenhuma exceção genérica é mascarada; zero fallbacks permissivos.

### Pureza e Zero I/O
A Policy opera como função pura de governança:
- Síncrona;
- Determinística;
- Zero I/O;
- Sem leitura ou injeção de repositórios;
- Sem acesso a sistema de arquivos ou rede;
- Sem dependência de relógio (`datetime.now()`, etc.);
- Sem fontes de aleatoriedade (`random`, `uuid`);
- Sem mutação de argumentos de entrada.

---

## 10. Limite de Enforcement (Enforcement Boundary)

A Issue #100 estabelece **autoridade normativa em memória**.

Ela responde exclusivamente à questão de governança:
> *“Dado este `HumanReviewClaimState` e esta `VerifiedSpecialistIdentity`, qual é a elegibilidade normativa do revisor?”*

A Policy **NÃO** modifica `RecordHumanDecisionUseCase` e **NÃO** impede em tempo de execução a conclusão de workflows na camada de aplicação.

A integração e o enforcement operacional do vínculo *claimant $\rightarrow$ reviewer* em `RecordHumanDecisionUseCase` constituem o escopo de uma futura fatia arquitetural dedicada.

---

## 11. Fora de Escopo (Explicitamente Não-Objetivos)

Permanecem formalmente fora de escopo:
- Alteração ou injeção em `RecordHumanDecisionUseCase`;
- Enforcement na camada de Application;
- Injeção de repositórios ou I/O dentro da policy;
- Deduplicação, agrupamento ou reinterpretação de claims;
- Active claim / Claim ativo;
- Eleição de vencedor (Winner) / Desempate;
- First-Claim-Wins ou Last-Claim-Wins;
- Locking, mutex, lease, checkout, TTL, expiry ou SLA;
- Operações de ciclo de vida de claim (`unclaim`, `release`, `transfer`, revogação);
- Modificação de `GovernanceWorkflow` ou `WorkflowStatus` (não existe `WorkflowStatus.CLAIMED`);
- Interfaces visuais (UI Streamlit, endpoints REST, CLI);
- Concorrência multiprocesso / Pressão P-07.

---

## 12. Estratégia de Micro-TDD Planejada

A implementação deverá ocorrer em fatias atômicas orientadas a testes em `tests/test_reviewer_eligibility_policy.py`:

```text
Fatia 1: Contratos e Read-Model
  -> Teste: instanciação válida, validação defensiva de status, imutabilidade, propriedades derivadas is_eligible e reason.
  -> Rejeição de construtor com is_eligible ou reason.

Fatia 2: Caso NO_CLAIM
  -> Teste: workflow sem claims resulta em CLAIM_REQUIRED e is_eligible=False.

Fatia 3: Caso SINGLE_CLAIM (Sucesso)
  -> Teste: mesmo principal estável resulta em ELIGIBLE e is_eligible=True.

Fatia 4: Caso SINGLE_CLAIM (Divergências de Principal)
  -> Testes:
     - divergência em specialist_id -> CLAIMANT_MISMATCH
     - divergência em identity_provider -> CLAIMANT_MISMATCH
     - divergência em identity_subject -> CLAIMANT_MISMATCH
     - sensibilidade a maiúsculas/minúsculas (ex: "CORP_IDP" vs "corp_idp") -> CLAIMANT_MISMATCH

Fatia 5: Isolamento de Proveniência de Sessão
  -> Teste: mesmo principal com verification_id e verified_at distintos -> ELIGIBLE.

Fatia 6: Caso MULTIPLE_CLAIMS de Especialistas Distintos
  -> Teste: múltiplos claims de especialistas diferentes -> MULTIPLE_CLAIMS_CONFLICT e is_eligible=False.

Fatia 7: Caso MULTIPLE_CLAIMS do Mesmo Principal
  -> Teste: dois claims do mesmo principal estável -> MULTIPLE_CLAIMS_CONFLICT e is_eligible=False.

Fatia 8: Validações Defensivas Fail-Closed e Exportação
  -> Teste: tipos inválidos para claim_state e reviewer_identity levantam TypeError.
  -> Teste: exportação pública dos símbolos no pacote raiz agent_lab.
  -> Regressão canônica completa (549 + novos testes GREEN).
```

---

## 13. Critérios de Aceite

1. Módulo `src/agent_lab/reviewer_eligibility_policy.py` implementado com zero I/O;
2. `ReviewerEligibilityStatus` implementado como enum contendo rigorosamente os 4 valores canônicos: `ELIGIBLE`, `CLAIM_REQUIRED`, `CLAIMANT_MISMATCH`, `MULTIPLE_CLAIMS_CONFLICT`;
3. `ReviewerEligibilityDecision` implementado com `@dataclass(frozen=True, slots=True)`, armazenando exclusivamente `status: ReviewerEligibilityStatus`;
4. `ReviewerEligibilityDecision.__post_init__` valida defensivamente que `status` é instância de `ReviewerEligibilityStatus` (rejeitando strings, booleanos ou tipos espúrios com `TypeError`);
5. Propriedade `is_eligible` é `@property` puramente derivada, retornando `True` exclusivamente se `status == ReviewerEligibilityStatus.ELIGIBLE` e `False` para os demais;
6. Propriedade `reason` é `@property` puramente derivada deterministicamente de `self.status`, sem aceitar parâmetro no construtor;
7. Avaliação em `NO_CLAIM` classifica o revisor como inelegível e retorna rigorosamente `status == ReviewerEligibilityStatus.CLAIM_REQUIRED` e `is_eligible == False`;
8. Avaliação em `SINGLE_CLAIM` com principal estável coincidente (comparação textual exata de `specialist_id`, `identity_provider` e `identity_subject`) classifica o revisor como elegível e retorna `status == ReviewerEligibilityStatus.ELIGIBLE` e `is_eligible == True`;
9. Avaliação em `SINGLE_CLAIM` com divergência textual exata em qualquer um dos três atributos de principal retorna `status == ReviewerEligibilityStatus.CLAIMANT_MISMATCH` e `is_eligible == False`;
10. Avaliação em `SINGLE_CLAIM` com mesmo principal estável, porém com `verification_id` ou `verified_at` distintos, retorna `status == ReviewerEligibilityStatus.ELIGIBLE` e `is_eligible == True`;
11. Avaliação em `MULTIPLE_CLAIMS` classifica o revisor como inelegível e retorna rigorosamente `status == ReviewerEligibilityStatus.MULTIPLE_CLAIMS_CONFLICT` e `is_eligible == False`, inclusive quando todos os múltiplos claims pertencerem ao mesmo principal estável;
12. Tentativas de passar tipos incorretos para `claim_state` ou `reviewer_identity` levantam `TypeError` (*fail-closed*);
13. Tentativas de mutação em `ReviewerEligibilityDecision` levantam `FrozenInstanceError`;
14. Tentativas de passar argumentos `is_eligible` ou `reason` no construtor de `ReviewerEligibilityDecision` levantam `TypeError`;
15. `RecordHumanDecisionUseCase` permanece 100% inalterado;
16. 100% dos 549 testes existentes mantidos GREEN no runner oficial `python -m unittest discover -s tests -v`;
17. `git diff --check` limpo sem whitespace residual.

---

## 14. Definition of Done (DoD)

- [ ] SPEC 0100 aprovada por revisão humana formal;
- [ ] Branch `feature/issue-100-reviewer-claim-eligibility-policy` isolada e ativa a partir de `c145b65`;
- [ ] Ciclo micro-TDD executado com commits atômicos rastreáveis;
- [ ] Todos os novos testes implementados exclusivamente via `unittest` em Python 3.11;
- [ ] Suíte completa de testes aprovada: `python -m unittest discover -s tests -v`;
- [ ] `git diff --check` limpo sem erros de formatação ou whitespace;
- [ ] Auditoria pré-PR confirmando ausência de escopo não autorizado (especialmente ausência de alterações em `RecordHumanDecisionUseCase`);
- [ ] Pull Request funcional aberto referenciando `Refs #100`;
- [ ] Status check obrigatório da CI do PR funcional aprovado;
- [ ] PR funcional mergeado na `main`;
- [ ] Issue #100 permanece OPEN após o merge funcional;
- [ ] Closeout documental executado em branch/PR documental dedicado, atualizando `docs/PROJECT_COMPASS.md`;
- [ ] PR documental de closeout referencia `Closes #100`;
- [ ] Issue #100 somente é considerada concluída após o merge do closeout documental.

> [!NOTE]
> **Distinção de Governança:** Functional completion != Issue completion. O merge funcional conclui a entrega de código e testes; o fechamento formal da Issue ocorre exclusivamente após o closeout documental integrado na `main`.
