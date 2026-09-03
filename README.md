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
                       │ (RecordHumanDecisionUseCase: gravação sequencial não-atômica)
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
│ TRILHA DE HUMAN REVIEW CLAIM (Append-only, desacoplada)                                │
│                                                                                        │
│  HumanReviewClaim                                                                      │
│       │                                                                                │
│       ▼                                                                                │
│  JsonlHumanReviewClaimRepository (Append-only)                                         │
│       │                                                                                │
│       ▼                                                                                │
│  Claim JSONL                                                                           │
│       │                                                                                │
│       ▼                                                                                │
│  project_human_review_claim_state (Projeção pura determinística)                       │
│       │                                                                                │
│       ▼                                                                                │
│  NO_CLAIM / SINGLE_CLAIM / MULTIPLE_CLAIMS                                             │
│  (factual projection != active claim policy / Repository não elege claim ativo)        │
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
```

### Camada de Aplicação (Application Layer)

Os casos de uso de Application oferecem boundaries explícitos de coordenação:

- **`RecordHumanDecisionUseCase`:** coordena o fluxo de conclusão de uma revisão humana. Executa primeiro a preparação determinística em memória (zero-I/O) e, em seguida, realiza a persistência sequencial explícita: grava primeiro o `AuditEvent` no repositório de auditoria e, em seguida, o `WorkflowConcluded` no repositório de lifecycle. O dual-write desse fluxo é deliberadamente não-atômico (sem 2PC, rollback ou compensação), permitindo verificar eventuais divergências via `verify_dual_write_consistency`. *(Nota: este caso de uso não cria nem grava `MaterialRevision`, que pertence a um contrato e repositório independentes).*
- **`ListPendingHumanReviewsUseCase`:** expõe a consulta da fila ativa de workflows pendentes de revisão humana através da projeção determinística `project_pending_human_review_queue`.
- **`RecordHumanReviewClaimUseCase`:** coordena a assunção voluntária de um workflow pendente por especialista verificado (`claim_pending_human_review`) e sua persistência append-only via `HumanReviewClaimRepository`, sem alterar o status do workflow e sem eleger claim ativo.

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
- **531 testes automatizados (100% GREEN)** na branch `main` cobrindo domínio, serialização, persistência append-only, consistência cruzada, proveniência, contratos de claim, persistência de claim, casos de uso de aplicação e projeções de claims;
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
│       ├── human_review.py
│       ├── human_review_claim.py
│       ├── human_review_claim_projection.py
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
- benchmark de qualidade comparativo entre modelos reais;
- detecção semântica de duplicidades por embeddings ou similaridade vetorial;
- RAG (Retrieval-Augmented Generation) sobre normas, catálogos técnicos ou procedimentos;
- autenticação e autorização corporativa real (SSO, OAuth2, RBAC);
- banco de dados relacional remoto ou arquitetura cliente/servidor;
- controle de concorrência multiprocesso, múltiplos escritores simultâneos ou locking distribuído;
- projeção de claims ativos, caso de uso de aplicação de claim, atribuição gerencial (assignment) e controle concorrente/ownership de itens na fila de revisão;
- gestão de SLAs, prazos e priorização operacional de atendimento;
- interface operacional (UI/Web/CLI) para o especialista de governança;
- validação de carga e escala industrial (pressão arquitetural P-07: throughput, memória sob grandes volumes);
- linhagem de sucessão e substituição de materiais (pressão arquitetural P-08: `MaterialRevision != MaterialReplacement`);
- integração ou injeção direta em sistemas ERP/MDM legados;
- observabilidade de produção (telemetria, tracing distribuído, métricas Prometheus/OpenTelemetry);
- aprendizado automático ou fine-tuning a partir do feedback do especialista;
- aplicação automática de correções (`CorrectionRequest`): a aplicação automática em cadastros reais permanece deliberadamente fora do escopo, preservando a soberania humana.

## Próximas frentes

Próxima fase planejada: evoluir o Human-in-the-Loop para operação de PoC — projeção de claims ativos, caso de uso de aplicação, assignment, estados de atendimento, SLA e preparação da interface do especialista — mediante novas Issues pequenas e explicitamente aprovadas.

Frentes evolutivas e pressões arquiteturais no backlog incluem:

1. evolução do atendimento operacional de revisão (coordenação de claims, estados de atendimento, SLA e interface do especialista);
2. integração de um provider real sem quebrar a abstração `LLMProvider`;
3. medição da LLM contra o baseline determinístico e benchmark com ground truth;
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

✅ **Módulos 0 a 7 concluídos (Release v0.1.0):** fundação do domínio, baseline determinístico, saída estruturada, Evidence Engine, Human-in-the-Loop v1, persistência auditável durável, identidade verificável e persistência de abertura de workflow.

✅ **Incrementos pós-v0.1.0 integrados na main (Issues #52 a #88):** persistência de conclusão (`WorkflowConcluded`), verificação de consistência dual-write, contratos e persistência de linhagem para follow-up de correção (`predecessor_workflow_id`, `triggering_review_id`), proveniência e projeção de linhagem de revisões de materiais (`project_material_revision_lineage`), caso de uso `RecordHumanDecisionUseCase`, projeção de fila pendente, caso de uso `ListPendingHumanReviewsUseCase`, contrato de domínio `HumanReviewClaim` e persistência de claims (`JsonlHumanReviewClaimRepository`).

🧪 **503 testes automatizados (100% GREEN)** protegem o comportamento atual na branch `main` com `unittest` (frente aos 206 testes do baseline fundacional da release v0.1.0).

➡️ **Próxima etapa:** evoluir o Human-in-the-Loop para operação de PoC — projeção de claims ativos, caso de uso de aplicação, assignment, estados de atendimento, SLA e preparação da interface do especialista — mediante novas Issues pequenas e explicitamente aprovadas.
