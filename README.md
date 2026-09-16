# Agent Lab Pascoal

Laboratório progressivo de engenharia de agentes de IA aplicado à governança de materiais PDM e estruturas BOM.

## Objetivo

Construir, compreender e avaliar agentes capazes de apoiar a governança de cadastros industriais sem substituir a decisão do especialista.

O laboratório evolui de soluções simples e auditáveis para componentes probabilísticos somente quando existe uma hipótese mensurável de ganho. A arquitetura combina baseline determinístico, contratos estruturados para LLM, fronteiras explícitas de validação, guardrails semânticos, ciclo temporal de governança, proveniência de revisões, projeções determinísticas e revisão humana obrigatória.

## Princípios de engenharia

> **A IA só entra onde demonstrar ganho mensurável sobre uma solução mais simples.**

1. **A IA recomenda; o humano decide:** o sistema produz evidências e recomendações rastreáveis, mas a decisão final e a autorização de mudanças permanecem estritamente humanas.
2. **Separação de responsabilidades:**
   - **Application coordena:** orquestra o fluxo de execução entre os componentes através de boundaries explícitos de coordenação.
   - **Domain decide:** encapsula regras de negócio, validações e invariantes.
   - **Repository preserva fatos persistidos:** armazena registros e eventos em logs duráveis, estruturados e append-only.
   - **Projection interpreta:** reconstrói o estado atual e topologias a partir do histórico persistido.
3. **Repository != Projection:** Repository preserva fatos persistidos; Projection interpreta. Repositórios append-only não reescrevem fatos históricos; projeções derivam estado ou topologia sem mutar a fonte persistida.
4. **WorkflowLifecycleEvent != AuditEvent:** o lifecycle preserva os fatos e o estado operacional do processo (`PENDING_HUMAN_REVIEW`, `REVIEWED`); a trilha de auditoria preserva evidência imutável e rastreabilidade técnica da deliberação humana.
5. **CorrectionRequest != MaterialRevision:** a solicitação de correção do especialista (`CorrectionRequest`) expressa a intenção humana de ajuste no contexto da revisão; a revisão de material (`MaterialRevision`) é um registro de proveniência cadastral em contrato e repositório separados. O campo `source_review_id` em `MaterialRevision` é proveniência declarada, não prova de causalidade nem aplicação automática da correção.
6. **Dual-write deliberadamente não-atômico no registro da decisão:** a persistência no fluxo `RecordHumanDecisionUseCase` → `AuditRepository` → `WorkflowLifecycleRepository` é sequencial e sem transações distribuídas (sem 2PC, rollback, retry automático ou compensação). A consistência entre essas duas fontes é verificada de forma determinística e somente-leitura.
7. **HumanReviewClaim != HumanReview e CLAIMED != REVIEWED:** a assunção operacional (`HumanReviewClaim`) representa o compromisso voluntário de um especialista verificado em analisar um workflow pendente (`PENDING_HUMAN_REVIEW`) e possui trilha persistente dedicada append-only, sem alterar o ciclo de governança, sem emitir eventos de auditoria ou lifecycle e sem constituir deliberação ou decisão humana.
8. **HumanReviewClaimRelease != HumanReviewClaim:** a liberação voluntária de reivindicação (`HumanReviewClaimRelease`) registra o fato histórico de liberação pelo especialista verificado, sem alterar o workflow nem o claim persistido, sem constituir revogação forçada e sem eleger claim ativo.
9. **Ground Truth != Prediction e Dataset != Metric:** o gabarito de referência (`Ground Truth`) expressa uma expectativa factual ou normativa de governança com proveniência explícita, segregada de predições e recomendações algorítmicas (`Prediction`); o dataset de avaliação organiza coleções canônicas imutáveis, segregado das métricas derivadas e diagnósticos de conformidade.
10. **Evaluation Contract != Benchmark Result e evaluation_case_id != material_id:** a avaliação atômica ou em lote afere exatidão categórica determinística em memória entre pares estruturados, sem constituir benchmark comparativo amplo ou runner orquestrado; o identificador experimental do caso de avaliação (`evaluation_case_id`) preserva a identidade metrológica do teste e não se confunde com a entidade cadastral de domínio (`material_id`).


## Arquitetura atual

A arquitetura do laboratório opera em camadas desacopladas e trilhas persistentes complementares:

```text
MaterialRecord
     │
     ├──────────────► Baseline determinístico
     │                  │
     │                  └──► Evidence Engine
     │
     └──────────────► Fronteira LLM (independente de provider)
                        │
                        ├──► Prompt determinístico
                        ├──► LLMProvider
                        ├──► JSON bruto → Validação Pydantic
                        ├──► Guardrail de identidade
                        └──► GovernanceAgentOutput
                                  │
                                  └──► Evidence Engine
                                            │
                                            └──► DecisionRecommendation
                                                      │
                                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TRILHA DE LIFECYCLE (Append-only)                                                      │
│                                                                                        │
│  WorkflowOpened  ──►  JsonlWorkflowLifecycleRepository  ◄──  WorkflowConcluded        │
│          │                                                           │                 │
│          └───────────────────────────┬───────────────────────────────┘                 │
│                                      ▼                                                 │
│                        rehydrate_workflow (Projeção)                                  │
│                                      │                                                 │
│                      ┌───────────────┴───────────────┐                                 │
│                      ▼                               ▼                                 │
│            PENDING_HUMAN_REVIEW                  REVIEWED                              │
│                      │                               │                                 │
│                      │                 open_correction_follow_up                       │
│                      │                 (predecessor_workflow_id,                       │
│                      │                  triggering_review_id)                          │
│                      ▼                                                                 │
│             Revisão pelo Especialista (+ VerifiedSpecialistIdentity)                   │
└──────────────────────┬─────────────────────────────────────────────────────────────────┘
                       │
                       │ Coordenação via Application
                       │ (RecordHumanDecisionUseCase: gate pré-write + gravação sequencial não-atômica)
                       ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TRILHA DE AUDITORIA (Append-only, desacoplada)                                         │
│                                                                                        │
│  HumanReview ──► AuditEvent ──► JsonlAuditRepository                                   │
│                                                                                        │
│  Consistência cruzada (Read-only):                                                     │
│  verify_dual_write_consistency / verify_repositories_consistency                       │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TRILHA DE HUMAN REVIEW CLAIM E RELEASE (Append-only, desacoplada)                      │
│                                                                                        │
│  Assunção de claim:                                                                    │
│  HumanReviewClaim                                                                      │
│       │                                                                                │
│       ▼                                                                                │
│  JsonlHumanReviewClaimRepository (Append-only) ──► Claim JSONL                         │
│                                                          │                             │
│       ┌──────────────────────────────────────────────────┘                             │
│       ▼                                                                                │
│  project_human_review_claim_state (Projeção factual pura)                              │
│       │                                                                                │
│       ▼                                                                                │
│  HumanReviewClaimState (NO_CLAIM / SINGLE_CLAIM / MULTIPLE_CLAIMS)                     │
│       │                                                                                │
│       ▼                                                                                │
│  evaluate_reviewer_claim_eligibility (Policy pura de governança em memória)            │
│       │                                                                                │
│       ▼                                                                                │
│  ReviewerEligibilityDecision ──► Gate pré-write em RecordHumanDecisionUseCase          │
│                                                                                        │
│  Liberação voluntária de claim (Application coordena):                                 │
│  release_human_review_claim (Domínio) ──► HumanReviewClaimRelease (Fato imutável)      │
│       │                                                                                │
│       ▼                                                                                │
│  ReleaseHumanReviewClaimUseCase ──► JsonlHumanReviewClaimReleaseRepository             │
│                                                   │                                    │
│                                                   ▼                                    │
│                                          Claim Release JSONL                           │
│  (Fato histórico isolado / sem active claim / sem revogação de histórico)              │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TRILHA DE MATERIAL REVISION (Contrato e repositório independentes)                     │
│                                                                                        │
│  MaterialRevision (com source_review_id declarado e predecessor_revision_id)           │
│       │                                                                                │
│       ▼                                                                                │
│  JsonlMaterialRevisionRepository (Append-only)                                         │
│       │                                                                                │
│       ▼                                                                                │
│  project_material_revision_lineage (Topologia pura: roots, heads, forks, ciclos)       │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CAMADA DE GROUND TRUTH E AVALIAÇÃO (Pura em memória, zero-I/O)                         │
│                                                                                        │
│  Contratos atômicos de Ground Truth (Proveniência explícita):                          │
│  MaterialRuleGroundTruth / DuplicatePairGroundTruth / DecisionRecommendationGroundTruth│
│       │                                                                                │
│       ▼                                                                                │
│  Datasets canônicos de avaliação (Coleções imutáveis ordenadas por case_id/gt_id):     │
│  MaterialRuleGroundTruthDataset / DuplicatePairGroundTruthDataset /                     │
│  DecisionRecommendationGroundTruthDataset                                              │
│       │                                                                                │
│       ▼                                                                                │
│  Aferição de recomendações de governança:                                              │
│  DecisionRecommendationGroundTruth + DecisionRecommendation                            │
│       │                                                                                │
│       ├──► evaluate_decision_recommendation (Atômico: validação relacional material_id) │
│       │         │                                                                      │
│       │         ▼                                                                      │
│       │    DecisionRecommendationCaseEvaluation (is_match / is_mismatch)                │
│       │                                                                                │
│       └──► evaluate_decision_recommendations (Lote 1:1 por evaluation_case_id)          │
│                 │                                                                      │
│                 ▼                                                                      │
│            DecisionRecommendationEvaluationReport (total, match, mismatch, accuracy)   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Camada de Aplicação (Application Layer)

Os casos de uso de Application oferecem boundaries explícitos de coordenação:

- **`RecordHumanDecisionUseCase`:** coordena o fluxo de deliberação de uma revisão humana com injeção obrigatória de `HumanReviewClaimRepository` e aplicação da Reviewer Claim Eligibility Policy como gate obrigatório de autorização pré-write em quatro fases canônicas de execução: na Fase 1 (domínio em memória / zero I/O), prepara e valida deterministicamente todos os artefatos de domínio, onde qualquer violação aborta a execução antes de qualquer leitura ou escrita (`0 reads → 0 writes`); na Fase 2 (gate de elegibilidade pré-write), após o sucesso da Fase 1, realiza exatamente uma consulta a `HumanReviewClaimRepository` (cujas falhas físicas ou corrupção propagam a exceção original do repositório de forma *fail-closed* com zero escritas), projeta o estado factual via `project_human_review_claim_state` e avalia a autoridade normativa via `evaluate_reviewer_claim_eligibility`, levantando `ReviewerNotEligibleError` (preservando `ReviewerEligibilityDecision`) exclusivamente quando o status retornado pela Policy for diferente de `ELIGIBLE` (`CLAIM_REQUIRED`, `CLAIMANT_MISMATCH`, `MULTIPLE_CLAIMS_CONFLICT`), garantindo zero escritas; na Fase 3 (persistência sequencial), autoriza as gravações em `AuditRepository` seguido de `WorkflowLifecycleRepository` estritamente quando `ELIGIBLE`, mantendo o dual-write deliberadamente não-atômico (sem 2PC, rollback ou compensação) verificável via `verify_dual_write_consistency`; e na Fase 4 (retorno), retorna `RecordHumanDecisionResult` inalterado, sem armazenar elegibilidade redundante. *(Nota: este caso de uso não cria nem grava `MaterialRevision`, que pertence a um contrato e repositório independentes).*
- **`ListPendingHumanReviewsUseCase`:** expõe a consulta da fila ativa de workflows pendentes de revisão humana através da projeção determinística `project_pending_human_review_queue`.
- **`RecordHumanReviewClaimUseCase`:** coordena a assunção voluntária de um workflow pendente por especialista verificado (`claim_pending_human_review`) e sua persistência append-only via `HumanReviewClaimRepository`, sem alterar o status do workflow e sem eleger claim ativo.
- **`ListPendingHumanReviewsWithClaimStateUseCase`:** expõe a consulta da fila ativa de workflows pendentes de revisão humana combinada de forma determinística com o estado factual de claims (`HumanReviewClaimState`) de cada item via `PendingHumanReviewWithClaimStateItem`. Opera com snapshot local único por repositório durante a execução, sem reordenação na camada de aplicação, com validação relacional de `workflow_id` e sem atribuir semântica operacional ou de lock a `sole_claim`.
- **`ReleaseHumanReviewClaimUseCase`:** coordena a liberação voluntária de uma reivindicação de revisão humana (`release_human_review_claim`) e sua persistência append-only via `HumanReviewClaimReleaseRepository`, validando exclusivamente tipos estruturais de borda e delegando as regras de negócio ao domínio. Falhas de domínio ocorrem antes de qualquer escrita; falhas de persistência são propagadas sem mascaramento, retry, rollback ou compensação. Não consulta histórico prévio, não altera o status do workflow e não determina claim ativo, owner, winner ou assignment, responsabilidades reservadas a projeções e políticas futuras.

### Camada de Política e Governança Normativa (Policy Layer)

A camada de Policy introduz regras puras, determinísticas e em memória (zero-I/O), posicionada conceitualmente entre a projeção factual e a coordenação de aplicação (`Repository preserva → Projection interpreta → Policy governa → Application coordena e aplica`):

- **`evaluate_reviewer_claim_eligibility`:** avalia deterministicamente se uma identidade verificada (`VerifiedSpecialistIdentity`) possui elegibilidade normativa para revisar um workflow com base no seu estado factual de claims (`HumanReviewClaimState`), retornando um `ReviewerEligibilityDecision` imutável com `status: ReviewerEligibilityStatus` (`ELIGIBLE`, `CLAIM_REQUIRED`, `CLAIMANT_MISMATCH`, `MULTIPLE_CLAIMS_CONFLICT`). Adota equivalência estrita de Principal Estável `(specialist_id, identity_provider, identity_subject)` isolando metadados de verificação (`verification_id`, `verified_at`), mantém cardinalidade governada pela Projection (`MULTIPLE_CLAIMS` sempre em conflito, inclusive para o mesmo principal estável) e valida defensivamente os tipos de entrada (`TypeError`). *(Nota: a política estabelece autoridade normativa pura e determinística em memória com zero I/O; ela não implementa active claim, ownership, assignment, winner election, locking ou SLA, sendo aplicada operacionalmente como gate de autorização pré-write pelo `RecordHumanDecisionUseCase`).*

### Camada de Ground Truth e Avaliação Metrológica (Ground Truth & Evaluation Layer)

A camada de Ground Truth e Avaliação introduz modelos e rotinas puras, determinísticas e em memória (zero-I/O), segregando formalmente referências de verdade, coleções de teste e instrumentos de aferição (`Ground Truth representa expectativa de referência → Dataset organiza coleção canônica → Evaluator compara predição contra Ground Truth → Evaluation Report agrega resultados`):

- **Contratos atômicos de Ground Truth (`ground_truth.py`):** modelos imutáveis com proveniência explícita (`LabelProvenance`) que formalizam expectativas factuais ou normativas sobre conformidade cadastral (`MaterialRuleGroundTruth`), duplicidades de materiais (`DuplicatePairGroundTruth`) e recomendações de governança (`DecisionRecommendationGroundTruth`).
- **Datasets canônicos de avaliação (`ground_truth.py`):** contêineres imutáveis (`MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset`, `DecisionRecommendationGroundTruthDataset`) que organizam itens em coleções canônicas ordenadas deterministicamente por `(evaluation_case_id, ground_truth_id)` com garantia de unicidade estrita de identificadores em v1.
- **Aferição determinística de recomendações (`ground_truth_evaluation.py`):** instrumentos puros de avaliação metrológica para recomendações algorítmicas de governança:
  - `evaluate_decision_recommendation`: afere deterministicamente uma `DecisionRecommendation` contra um `DecisionRecommendationGroundTruth`, emitindo diagnóstico imutável `DecisionRecommendationCaseEvaluation` (`is_match` / `is_mismatch`) com validação relacional fail-closed de `material_id`.
  - `evaluate_decision_recommendations`: afere coleções completas contra `DecisionRecommendationGroundTruthDataset` com pareamento obrigatório 1:1 por `evaluation_case_id`, gerando relatório imutável `DecisionRecommendationEvaluationReport` com métricas consolidadas de exatidão categórica (`accuracy`, onde coleções vazias retornam `accuracy is None`).

*(Nota: a avaliação implementada opera exclusivamente em memória sobre recomendações de decisão; avaliadores para regras de materiais e duplicidades, persistência/loaders de datasets, runners de benchmark e métricas multiclasses não estão implementados).*

A fronteira de LLM está desenhada de forma desacoplada de provedores externos via abstração `LLMProvider`, permitindo testes unitários e de integração determinísticos sem custos de rede ou dependências externas.


## Módulos fundacionais (Base da Release v0.1.0)

A release formal **v0.1.0** (*Governed Agent Workflow Baseline*) consolidou os módulos fundacionais do projeto, protegida por um baseline de 206 testes automatizados:

### Módulo 0 — Fundação
- Definição do problema de governança, fronteiras de decisão, contratos de dados sintéticos e modelos de domínio iniciais.

### Módulo 1 — Baseline determinístico
- Leitura tipada, normalização textual, validação de regras e identificação léxica de duplicidades.
- Conjunto de desafio separado e métrica ponderada de custo dos erros sem uso de LLM.

### Módulo 2 — Saída estruturada e fronteira LLM
- Contrato `GovernanceAgentOutput` com Pydantic e JSON Schema exportável.
- Abstração `LLMProvider`, fake provider determinístico e guardrail semântico de identidade do material com erro explícito diante de divergências.

### Módulo 3 — Evidence Engine e recomendação de decisão
- Estruturação e agregação imutável de evidências (`EvidenceCollection`) e derivação de `DecisionRecommendation` com score de confiança e rastreabilidade.

### Módulo 4 — Human-in-the-Loop e trilha de auditoria
- Contratos `HumanDecision`, `CorrectionRequest`, `HumanReview` e `AuditEvent`.
- Separação estrita entre recomendação automática e decisão humana.

### Módulo 5 — Persistência auditável v1
- `JsonlAuditRepository` append-only durável (`flush` + `os.fsync`), versionamento de schema e leitura *fail-closed*.

### Módulo 6 — Identidade verificável e workflow temporal
- Contrato `VerifiedSpecialistIdentity` e máquina de estados em memória `GovernanceWorkflow` (`PENDING_HUMAN_REVIEW` e `REVIEWED`) com derivação de lead time.

### Módulo 7 — Persistência de abertura de workflow e reidratação v1
- Evento `WorkflowOpened`, repositório append-only `JsonlWorkflowLifecycleRepository` e projeção pura `rehydrate_pending_workflow`.

---

## Incrementos pós-v0.1.0 integrados na main

Após o fechamento da release v0.1.0, o projeto evoluiu continuamente através de incrementos funcionais protegidos por SPECs e testes automatizados:

- **Workflow Conclusion Persistence (Issue #52):** persistência append-only do evento `WorkflowConcluded` no repositório de lifecycle e projeção pura `rehydrate_workflow` para os estados `PENDING_HUMAN_REVIEW` e `REVIEWED`.
- **Dual-Write Consistency Check (Issue #55):** verificação determinística e somente-leitura de consistência cruzada entre as trilhas desacopladas de lifecycle e auditoria (`verify_dual_write_consistency` e `verify_repositories_consistency`).
- **Correction Follow-up Workflow Contract (Issue #58):** contrato de domínio para abertura de novo ciclo de governança sucessor (`open_correction_follow_up`) a partir de revisões com solicitação de correção, preservando o predecessor imutável.
- **Correction Follow-up Lineage Persistence (Issue #61):** persistência de eventos `WorkflowOpened` com rastreamento explícito de linhagem causal (`predecessor_workflow_id` e `triggering_review_id`) e versionamento de schema v2 retrocompatível.
- **Material Revision Provenance (Issue #64):** modelo de domínio imutável `MaterialRevision` para capturar proveniência, rastreabilidade e histórico de modificações cadastrais (`predecessor_revision_id`, `source_review_id`, etc.).
- **Material Revision Persistence (Issue #68):** repositório append-only durável `JsonlMaterialRevisionRepository` com serialização versionada para gravação segura de revisões de materiais.
- **Material Revision Lineage Projection (Issue #71):** projeção pura `project_material_revision_lineage` para reconstruir a topologia causal de revisões (roots, heads, órfãos, forks, múltiplas raízes e ciclos), sem eleger latest head ou ordenar semanticamente por timestamp.
- **Human Review Application Use Case (Issue #74):** caso de uso `RecordHumanDecisionUseCase` com boundary explícito de coordenação, preparação zero-I/O e persistência sequencial (Audit → Lifecycle).
- **Pending Human Review Queue Projection (Issue #77):** projeção pura `project_pending_human_review_queue` para identificar workflows abertos que aguardam revisão humana.
- **Pending Human Review Queue Application Use Case (Issue #81):** caso de uso de aplicação `ListPendingHumanReviewsUseCase` para consulta estruturada da fila ativa de pendências do especialista.
- **Human Review Claim Domain Contract (Issue #85):** contrato puro de domínio em memória (`HumanReviewClaim` e `claim_pending_human_review`) para assunção voluntária de workflows pendentes por especialistas verificados, com tipagem estrita, imutabilidade, validação fail-closed de elegibilidade (`PENDING_HUMAN_REVIEW`) e cronologia.
- **Human Review Claim Persistence (Issue #88):** persistência append-only durável em JSONL (`JsonlHumanReviewClaimRepository`) com serialização canônica versionada (`schema_version = 1`), validação fail-closed estrita, suporte a múltiplos claims por `workflow_id` na ordem física de append, integridade pós-restart e exportação da API pública.
- **Record Human Review Claim Application Use Case (Issue #91):** caso de uso de aplicação `RecordHumanReviewClaimUseCase` para coordenação explícita da criação determinística e persistência de `HumanReviewClaim` via `HumanReviewClaimRepository`, com integração vertical validada contra `JsonlHumanReviewClaimRepository` e exportação da API pública.
- **Human Review Claim State Projection (Issue #94):** projeção pura e determinística em memória (`project_human_review_claim_state`) e read-model imutável (`HumanReviewClaimState`) sobre fatos de claims persistidos, classificando fielmente os estados factuais `NO_CLAIM`, `SINGLE_CLAIM` e `MULTIPLE_CLAIMS`, com propriedades puramente derivadas (sem armazenamento redundante de `state` ou `claim_count`), ordenação canônica determinística `(claimed_at ASC, claim_id ASC)` sem autoridade operacional de vencedor ou precedência, validação fail-closed estrita de todos os elementos antes da filtragem, integração vertical pós-restart com `JsonlHumanReviewClaimRepository` e exportação pública no pacote `agent_lab`.
- **Pending Human Review Queue with Claim State Application Use Case (Issue #97):** caso de uso de aplicação `ListPendingHumanReviewsWithClaimStateUseCase` e read-model imutável `PendingHumanReviewWithClaimStateItem` compondo de forma somente-leitura a fila de pendências (`project_pending_human_review_queue`) com o estado factual de claims (`project_human_review_claim_state`), categorizado em `NO_CLAIM`, `SINGLE_CLAIM` e `MULTIPLE_CLAIMS`. Garante a pending queue como conjunto condutor (driver set), preserva a ordenação FIFO, executa snapshot local único por repositório (`list_all_events()` e `list_all()`), elimina chamadas N+1, propaga falhas de forma fail-closed sem resultados parciais, mantém `sole_claim` como cardinalidade puramente factual (sem semântica de active claim, owner, winner, exclusividade ou lock) e comprova integração vertical JSONL real pós-restart.
- **Reviewer Claim Eligibility Policy (Issue #100):** política normativa pura e determinística de governança em memória (`evaluate_reviewer_claim_eligibility`), enum canônico `ReviewerEligibilityStatus` (`ELIGIBLE`, `CLAIM_REQUIRED`, `CLAIMANT_MISMATCH`, `MULTIPLE_CLAIMS_CONFLICT`) e read-model imutável `ReviewerEligibilityDecision`, avaliando a autoridade de deliberação a partir de `HumanReviewClaimState` com equivalência estrita de Principal Estável `(specialist_id, identity_provider, identity_subject)` isolando metadados de verificação `(verification_id, verified_at)` do Principal Estável, classificando `MULTIPLE_CLAIMS` deterministicamente como `MULTIPLE_CLAIMS_CONFLICT`, inclusive quando os claims pertencem ao mesmo Principal Estável, e sem active claim, owner, assignment, winner ou locking.
- **Reviewer Claim Eligibility Runtime Enforcement (Issue #103):** enforcement em tempo de execução da Reviewer Claim Eligibility Policy como gate obrigatório de autorização pré-write em `RecordHumanDecisionUseCase`. Injeta `HumanReviewClaimRepository` como dependência obrigatória, preserva a Fase 1 de domínio em memória (`0 reads → 0 writes` em falhas de domínio), executa exatamente uma leitura de claims após a Fase 1 válida, projeta via `project_human_review_claim_state`, avalia via `evaluate_reviewer_claim_eligibility`, levanta `ReviewerNotEligibleError` (preservando `ReviewerEligibilityDecision`) de forma *fail-closed* para `CLAIM_REQUIRED`, `CLAIMANT_MISMATCH` e `MULTIPLE_CLAIMS_CONFLICT` com zero writes em Audit e Lifecycle, propaga falhas e corrupção física do repositório de claims fail-closed com sua exceção original, autoriza a persistência sequencial `Audit → Lifecycle` estritamente quando `ELIGIBLE`, comprova persistência em JSONL e reidratação pós-restart autorizada via `RecordHumanReviewClaimUseCase` com relatório de consistência limpo, e preserva `RecordHumanDecisionResult` inalterado.
- **Human Review Claim Release Domain Contract (Issue #106):** contrato puro de domínio em memória (`HumanReviewClaimRelease` e `release_human_review_claim`) formalizando o fato imutável de liberação voluntária de claim por especialista verificado, com validação relacional de Stable Principal, invariantes temporais (`released_at >= claimed_at`), operação zero-I/O e sem alterar o workflow ou o claim histórico.
- **Human Review Claim Release Persistence (Issue #109):** persistência append-only durável em JSONL (`JsonlHumanReviewClaimReleaseRepository`) com serialização canônica versionada (`schema_version = 1`), garantia de durabilidade via `flush` + `os.fsync`, unicidade estrita de `release_id`, leitura fail-closed e recuperação de integridade pós-restart.
- **Release Human Review Claim Application Use Case (Issue #112):** caso de uso de aplicação `ReleaseHumanReviewClaimUseCase` coordenando o fluxo de liberação voluntária de claims em duas etapas estritas (domínio prepara o fato imutável em memória e repositório persiste o registro append-only), com propagação fail-closed de falhas e sem introduzir semântica de active claim.
- **Ground Truth Pure Domain Contracts v1 (Issue #115):** contratos puros e imutáveis de domínio em memória (`MaterialRuleGroundTruth`, `DuplicatePairGroundTruth` e `DecisionRecommendationGroundTruth`) com proveniência explícita (`LabelProvenance`), formalizando expectativas factuais ou normativas de governança segregadas de predições algorítmicas (`Ground Truth != Prediction`) com operação zero-I/O.
- **Ground Truth Dataset Contract v1 (Issue #119):** coleções canônicas imutáveis (`MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset` e `DecisionRecommendationGroundTruthDataset`) agregando itens com `dataset_id` obrigatório e normalizado, unicidade estrita de `ground_truth_id` e `evaluation_case_id` em v1, ordenação canônica determinística por `(evaluation_case_id, ground_truth_id)` e suporte a datasets vazios válidos.
- **Ground Truth Decision Recommendation Evaluator v1 (Issue #124):** camada de metrologia determinística pura em memória (`DecisionRecommendationCaseEvaluation`, `DecisionRecommendationEvaluationReport`, `evaluate_decision_recommendation` e `evaluate_decision_recommendations`) com pareamento estrito 1:1 por `evaluation_case_id`, validação relacional por `material_id`, acurácia categórica de exact-match (com `accuracy is None` para coleções vazias) e operação zero-I/O.


## Resultados do baseline

| Conjunto | Registros | Correspondência exata | Precisão de duplicidade | Recall de duplicidade |
|---|---:|---:|---:|---:|
| Desenvolvimento | 20 | 100% | 100% | 100% |
| Desafio | 10 | 80% | 0% | 0% |

O conjunto de desafio preserva duas limitações conhecidas:

- uma duplicidade semanticamente equivalente não identificada;
- uma revisão desnecessária causada por unidade considerada suspeita.

Esses erros foram preservados deliberadamente para evitar ajuste retrospectivo ao conjunto de avaliação.

## Custo ponderado dos erros

A hipótese inicial do laboratório considera:

- falso negativo de duplicidade: peso 5;
- revisão desnecessária: peso 1.

No conjunto de desafio:

```text
Custo = 1 × 5 + 1 × 1 = 6
```

O peso 5:1 é uma hipótese experimental e deverá ser calibrado futuramente com evidências reais de negócio.

## Engenharia e governança do repositório

O desenvolvimento segue um fluxo rigoroso e rastreável:

```text
Issue → análise → SPEC → TDD → implementação → Pull Request
      → CI → revisão → merge → release
```

O projeto conta com:

- templates de Issue e Pull Request;
- SPECs versionadas e detalhadas em `docs/specs/`;
- desenvolvimento orientado por testes (TDD);
- GitHub Actions com Python 3.11;
- **830 testes automatizados (100% GREEN)** na branch `main` cobrindo domínio, serialização, persistência append-only, consistência cruzada, proveniência, contratos de claim, persistência e release de claims, casos de uso de aplicação, projeções de claims, composição factual de fila pendente com claims, política pura de elegibilidade de revisores, enforcement de elegibilidade em tempo de execução (gate pré-write em `RecordHumanDecisionUseCase`), contratos puros de ground truth, datasets canônicos de avaliação, avaliador determinístico de recomendações de governança e integração vertical JSONL pós-restart;
- baseline fundacional da release **v0.1.0** preservado (206 testes);
- proteção de branch com status check de CI obrigatório antes de qualquer merge;
- política estrita de Versionamento Semântico e registro de mudanças em `CHANGELOG.md`;
- revisão humana obrigatória preservada em todas as camadas de governança.

## Estrutura principal do projeto

```text
agent-lab-pascoal/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   └── PULL_REQUEST_TEMPLATE.md
├── data/
│   ├── README.md
│   └── synthetic/
│       ├── materials.csv
│       └── materials_challenge.csv
├── docs/
│   ├── specs/
│   ├── 01_problem_definition.md
│   ├── 02_learning_roadmap.md
│   ├── 03_module_01_baseline.md
│   ├── 04_engineering_workflow.md
│   └── PROJECT_COMPASS.md
├── src/
│   └── agent_lab/
│       ├── __init__.py
│       ├── audit.py
│       ├── audit_repository.py
│       ├── audit_serialization.py
│       ├── baseline.py
│       ├── cli.py
│       ├── consistency.py
│       ├── data_io.py
│       ├── decision.py
│       ├── domain.py
│       ├── duplicates.py
│       ├── evidence.py
│       ├── ground_truth.py
│       ├── ground_truth_evaluation.py
│       ├── human_review.py
│       ├── human_review_claim.py
│       ├── human_review_claim_projection.py
│       ├── human_review_claim_release_repository.py
│       ├── human_review_claim_release_serialization.py
│       ├── human_review_claim_release_use_case.py
│       ├── human_review_claim_repository.py
│       ├── human_review_claim_serialization.py
│       ├── human_review_claim_use_case.py
│       ├── human_review_use_case.py
│       ├── llm_provider.py
│       ├── llm_schema.py
│       ├── llm_service.py
│       ├── material_revision.py
│       ├── material_revision_projection.py
│       ├── material_revision_repository.py
│       ├── material_revision_serialization.py
│       ├── metrics.py
│       ├── normalization.py
│       ├── pending_human_reviews_use_case.py
│       ├── pending_human_reviews_with_claim_state_use_case.py
│       ├── reviewer_eligibility_policy.py
│       ├── rules.py
│       ├── validator.py
│       ├── workflow.py
│       ├── workflow_events.py
│       ├── workflow_projection.py
│       ├── workflow_repository.py
│       └── workflow_serialization.py
├── tests/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── VERSIONING.md
├── pyproject.toml
└── README.md
```

## Executando os testes

Requer Python 3.11 ou superior.

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Executando o baseline

```powershell
$env:PYTHONPATH="src"
python -m agent_lab.cli data/synthetic/materials.csv
python -m agent_lab.cli data/synthetic/materials_challenge.csv
```

## O que ainda não está implementado

Para manter a documentação tecnicamente honesta, o laboratório ainda **não** possui:

- integração com provider real de LLM (OpenAI, Anthropic, Gemini);
- benchmark comparativo amplo entre modelos, Benchmark Runner ou orquestrador automatizado de benchmarks (os contratos atômicos de Ground Truth, os datasets canônicos e o avaliador determinístico de recomendações de decisão com exact-match accuracy foram entregues nas Issues #115, #119 e #124; permanecem não implementados os avaliadores de conformidade de regras de materiais e de duplicidades, persistência e serialização durável de Ground Truth e datasets, loaders externos, datasets industriais reais, matrizes de confusão, métricas multiclasses adicionais, precision/recall/F1 agregados para governança, calibração, threshold tuning, adjudicação/consenso e UI/API de benchmark);
- detecção semântica de duplicidades por embeddings ou similaridade vetorial;
- RAG (Retrieval-Augmented Generation) sobre normas, catálogos técnicos ou procedimentos;
- autenticação e autorização corporativa real (SSO, OAuth2, RBAC);
- banco de dados relacional remoto ou arquitetura cliente/servidor;
- controle de concorrência multiprocesso, múltiplos escritores simultâneos ou locking distribuído;
- projeção de claims ativos (Active Claim Projection / Active Claim Policy), atribuição gerencial (assignment), ownership operacional, estados de atendimento, locking / checkout, exclusividade, desempate / Last-Claim-Wins e controle concorrente de itens na fila de revisão (a composição factual da fila pendente com estado de claims foi entregue na Issue #97, a política pura normativa de elegibilidade de revisores foi entregue na Issue #100, o enforcement de elegibilidade em tempo de execução no `RecordHumanDecisionUseCase` foi entregue na Issue #103 e a liberação voluntária de claims foi entregue nas Issues #106, #109 e #112; a política de claim ativo e mecanismos de locking/assignment permanecem estritamente fora do escopo atual);
- gestão de SLAs, prazos e priorização operacional de atendimento;
- interface operacional (UI/Web/CLI) para o especialista de governança;
- validação de carga e escala industrial (pressão arquitetural P-07: throughput, memória sob grandes volumes);
- linhagem de sucessão e substituição de materiais (pressão arquitetural P-08: `MaterialRevision != MaterialReplacement`);
- integração ou injeção direta em sistemas ERP/MDM legados;
- observabilidade de produção (telemetria, tracing distribuído, métricas Prometheus/OpenTelemetry);
- aprendizado automático ou fine-tuning a partir do feedback do especialista;
- aplicação automática de correções (`CorrectionRequest`): a aplicação automática em cadastros reais permanece deliberadamente fora do escopo, preservando a soberania humana.

## Próximas frentes

Próxima âncora arquitetural: a definir após planejamento humano (zero Issues funcionais abertas).

A esteira de **Ground Truth & Benchmark** encontra-se em execução, tendo consolidado a sequência conceitual:
`Ground Truth Contracts → Canonical Datasets → Decision Recommendation Evaluator → próximos incrementos sujeitos a Architectural Alignment Gate`.

Entre as frentes futuras candidatas permanecem a expansão metrológica de Ground Truth (avaliadores adicionais de regras materiais e duplicidades, persistência durável, loaders de datasets, benchmark runner, métricas estatísticas e validação em escala industrial), bem como a evolução do fluxo operacional de revisão humana (projeção/política de active claim, assignment/ownership operacional, estados de atendimento, SLA e interface do especialista), cada uma estritamente condicionada a nova análise arquitetural, Issue e SPEC explicitamente aprovadas por decisão humana.

Frentes evolutivas e pressões arquiteturais no backlog incluem:

1. evolução do atendimento operacional de revisão (coordenação de claims, estados de atendimento, SLA e interface do especialista);
2. expansão da esteira de Ground Truth e benchmark (persistência, novos avaliadores, benchmark runner, loaders e métricas multiclasses);
3. integração de um provider real sem quebrar a abstração `LLMProvider`;
4. introdução de detecção semântica de duplicidades por similaridade vetorial;
5. expansão de evidências e justificativas auditáveis;
6. teste de arquitetura híbrida de regras + similaridade + RAG + LLM;
7. acompanhamento de precision, recall, falsos negativos, revisões desnecessárias, custo, latência e risco;
8. validação de carga e escala industrial (pressão arquitetural P-07);
9. linhagem de substituição e sucessão de materiais no catálogo (pressão arquitetural P-08);
10. evolução para uma PoC de diagnóstico de qualidade cadastral antes de qualquer promessa de produto industrial.

## Segurança dos dados

Este repositório é público. Não devem ser enviados:

- cadastros reais de empresas;
- códigos internos ou informações comerciais;
- documentos proprietários;
- nomes ou dados pessoais sem autorização;
- credenciais, tokens ou chaves de API.

Os dados atuais são inteiramente sintéticos. Dados reais somente poderão ser utilizados após anonimização, autorização e definição apropriada de governança.

## Responsabilidade humana

O sistema produz recomendações de apoio à governança. Ele não deve aprovar, rejeitar, classificar ou alterar definitivamente materiais de uma organização sem um processo autorizado.

A decisão final permanece humana.

## Estado do laboratório

*(Estado registrado em 16/09/2026 — pós-15/09/2026)*

✅ **Módulos 0 a 7 concluídos (Release v0.1.0):** fundação do domínio, baseline determinístico, saída estruturada, Evidence Engine, Human-in-the-Loop v1, persistência auditável durável, identidade verificável e persistência de abertura de workflow.

✅ **Incrementos pós-v0.1.0 integrados na main (Issues #52 a #124):** persistência de conclusão (`WorkflowConcluded`), verificação de consistência dual-write, contratos e persistência de linhagem para follow-up de correção (`predecessor_workflow_id`, `triggering_review_id`), proveniência e projeção de linhagem de revisões de materiais (`project_material_revision_lineage`), casos de uso `RecordHumanDecisionUseCase` e `ListPendingHumanReviewsUseCase`, trilhas de reivindicação e liberação voluntária de revisão humana (contratos `HumanReviewClaim` e `HumanReviewClaimRelease`, persistência append-only durável `JsonlHumanReviewClaimRepository` e `JsonlHumanReviewClaimReleaseRepository`, projeção factual `project_human_review_claim_state`, política pura de elegibilidade `evaluate_reviewer_claim_eligibility`, enforcement em tempo de execução via gate pré-write em `RecordHumanDecisionUseCase`, e casos de uso `RecordHumanReviewClaimUseCase`, `ListPendingHumanReviewsWithClaimStateUseCase` e `ReleaseHumanReviewClaimUseCase` — Issues #85 a #112), contratos puros de Ground Truth (`MaterialRuleGroundTruth`, `DuplicatePairGroundTruth`, `DecisionRecommendationGroundTruth`, `LabelProvenance` — Issue #115), coleções canônicas de avaliação (`MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset`, `DecisionRecommendationGroundTruthDataset` — Issue #119), e camada pura de metrologia determinística para recomendações algorítmicas de governança (`DecisionRecommendationCaseEvaluation`, `DecisionRecommendationEvaluationReport`, `evaluate_decision_recommendation` e `evaluate_decision_recommendations` — Issue #124, integrada via PR funcional #126 / merge `05eed90` e reconciliada via PR #127; SPEC-0124 com status `IMPLEMENTED`).

🧪 **830 testes automatizados (100% GREEN)** protegem o comportamento atual na branch `main` com `unittest` (frente aos 206 testes do baseline fundacional da release v0.1.0 e 776 testes pré-Issue #124).

➡️ **Próxima âncora arquitetural:** a definir após planejamento humano. A branch `main` encontra-se protegida, sincronizada com `origin/main` e com zero Issues e zero PRs abertas. A esteira de Ground Truth & Benchmark encontra-se em execução. Nenhum incremento funcional subsequente foi autorizado automaticamente; qualquer nova capacidade permanece estritamente condicionada a análise arquitetural, Issue e SPEC explicitamente aprovadas por decisão humana.
