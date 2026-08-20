# Changelog

Todas as mudanças relevantes do Agent Lab Pascoal serão registradas neste
arquivo.

O formato é inspirado em *Keep a Changelog* e o projeto adota Versionamento
Semântico conforme definido em `VERSIONING.md`.

## Como interpretar este arquivo

- `Unreleased` reúne mudanças incorporadas ou em preparação que ainda não
  receberam uma release formal.
- Uma versão somente é considerada publicada quando existir uma tag Git e uma
  GitHub Release correspondentes.
- O número existente no `pyproject.toml`, isoladamente, não comprova que uma
  release foi publicada.
- O histórico prioriza mudanças percebidas por pessoas, contratos e processos;
  não é uma cópia automática de todos os commits.

As mudanças são classificadas em:

- `Added`: funcionalidades, documentos ou capacidades novas;
- `Changed`: alterações em comportamento ou estrutura existente;
- `Deprecated`: recursos mantidos temporariamente antes da remoção;
- `Removed`: recursos eliminados;
- `Fixed`: correções de defeitos;
- `Security`: correções e controles de segurança.

## [Unreleased]

## [0.1.0] - 2026-08-20

### Added

#### Fundação determinística e baseline
- Estrutura inicial do laboratório em Python 3.11 com pacote organizado em `src/agent_lab`.
- Modelo de domínio para registros de materiais, decisões de governança, alertas e avaliações (`domain.py`).
- Validador determinístico de governança de materiais PDM/BOM (`validator.py`).
- Regras determinísticas para campos críticos, atributos técnicos, unidades suspeitas, descrições ambíguas e possíveis duplicidades (`rules.py`).
- Normalização de textos com remoção de acentos e pontuação, separação de números unidos a letras e expansão de abreviações de categoria (`normalization.py`).
- Detecção determinística de duplicidade por fabricante, código de peça e categoria (`duplicates.py`).
- Interface de linha de comando para execução do baseline sobre dados sintéticos (`cli.py`).

#### Avaliação e risco de negócio
- Dataset sintético rotulado para avaliação reproduzível do baseline (`materials.csv`).
- Conjunto de desafio separado para revelar limitações que não aparecem no conjunto principal (`materials_challenge.csv`).
- Métricas de correspondência exata, cobertura do rótulo esperado, precisão e recall de duplicidade (`metrics.py`).
- Contagem de falsos negativos de duplicidade e revisões humanas desnecessárias.
- Métrica de custo ponderado dos erros ($5 \times \text{falsos negativos de duplicidade} + 1 \times \text{revisões desnecessárias}$).
- Testes de qualidade mínima e de processamento do conjunto completo.

#### Fronteira estruturada para agentes e guardrails (Issues #15, #17)
- Contrato `GovernanceAgentOutput` com Pydantic para representar respostas estruturadas de agentes, com campos obrigatórios e tipados, `confidence` restrita a [0, 1], `extra="forbid"` e `frozen=True` (`llm_schema.py`).
- Exportação do contrato como JSON Schema para integração com modelos e ferramentas que suportem saídas estruturadas.
- Contrato `LLMProvider` independente de fornecedor e serviço determinístico de construção de prompts (`llm_service.py`).
- Fake Provider para testes de integração e execução determinística sem chamadas de rede.
- Guardrail semântico de identidade do material lançando erro explícito `MaterialIdentityMismatchError` quando o `material_id` retornado diverge do registro analisado.

#### Workflow de engenharia e CI (Issues #8, #10, #12)
- Formulários de Issue para propostas de funcionalidade e relatos de defeito (`.github/ISSUE_TEMPLATE/`).
- Template de Pull Request com rastreabilidade, testes, riscos, segurança e responsabilidade humana.
- Template reutilizável de especificação técnica em `docs/specs/SPEC_TEMPLATE.md`.
- Automação de testes em Python 3.11 via GitHub Actions (`.github/workflows/ci.yml`).
- Proteção da branch `main` com status check de CI obrigatório antes do merge.
- Guia de contribuição em `CONTRIBUTING.md` e política de versionamento em `VERSIONING.md`.

#### Evidence Engine e pipeline de recomendação determinística (Issues #21, #24, #27, #30)
- Contratos estruturados e imutáveis `GovernanceEvidence` e `EvidenceCollection` em `src/agent_lab/evidence.py`.
- Transformação de Issues determinísticas em evidências estruturadas (`build_evidence_collection`).
- Transformação de saídas estruturadas de LLM em evidências com severidade `WARNING` (`build_llm_evidence_collection`), impedindo que a LLM cause rejeição automática.
- Pipeline determinístico `recommend_decision` gerando `DecisionRecommendation` com `APPROVE`, `REVIEW` ou `REJECT`, justificativa estruturada e compulsoriedade de `requires_human_decision = True` (`decision.py`).

#### Human-in-the-Loop e identidade verificável de especialista (Issues #33, #41)
- Contratos imutáveis `HumanDecision`, `CorrectionRequest` e `HumanReview` em `src/agent_lab/human_review.py`.
- Contrato de identidade verificável `VerifiedSpecialistIdentity` com rastreamento de provedor, sujeito, identificador de verificação e timestamp auditável.
- Validação estrita de deliberação: justificativa obrigatória para rejeição e solicitação de correção; pelo menos uma correção para `REQUEST_CORRECTION`; proibição de correções pendentes para `APPROVE`; validação de consistência cronológica (`verified_at <= reviewed_at`).
- Derivação automática de concordância ou divergência humano–sistema (`agrees_with_system`).
- Serviço atômico em memória `record_human_review` que correlaciona a revisão humana ao evento de auditoria `AuditEvent` (`audit.py`).

#### Persistência auditável durável v1 (Issue #37)
- Serialização e desserialização versionadas de `AuditEvent` (`schema_version = 1`) com preservação estrita de timezone e integridade de tipos (`audit_serialization.py`).
- Protocolo `AuditRepository` e implementação `JsonlAuditRepository` com persistência local append-only pela API.
- Escrita síncrona durável com `flush` e `os.fsync`.
- Leitura e recuperação *fail-closed* diante de corrupção ou registros inválidos, expondo `line_number`.
- Detecção e rejeição explícita de `event_id` duplicado (`DuplicateAuditEventError`).

#### Ciclo de vida temporal de governança em memória (Issue #44)
- Contêiner temporal `GovernanceWorkflow` em `src/agent_lab/workflow.py` com estados `WorkflowStatus.PENDING_HUMAN_REVIEW` e `WorkflowStatus.REVIEWED`.
- Transição de estado pura canônica `conclude_governance_workflow` com validação cronológica (`opened_at <= reviewed_at`), coerência de material e bloqueio contra dupla conclusão.
- Propriedades derivadas `material_id`, `status`, `closed_at` e `review_lead_time`.

#### Persistência de abertura de workflow e reidratação pendente v1 (Issue #47)
- Evento de domínio imutável `WorkflowOpened` em `src/agent_lab/workflow_events.py` contendo `event_id`, `workflow_id`, `recommendation` e `opened_at` (timezone-aware).
- Serialização versionada (`schema_version = 1`) preservando integralmente `DecisionRecommendation` e todas as `GovernanceEvidence` associadas (`workflow_serialization.py`).
- Protocolo `WorkflowLifecycleRepository` e implementação append-only `JsonlWorkflowLifecycleRepository` em `src/agent_lab/workflow_repository.py` com escrita durável (`flush` + `os.fsync`).
- Projeção pura `rehydrate_pending_workflow` em `src/agent_lab/workflow_projection.py` que reconstrói `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` após reinício de processo sem reexecutar regras ou chamadas a LLM.
- Suíte automatizada integrada com 206 testes cobrindo estruturalmente as principais camadas, contratos, invariantes e integrações da versão.

### Changed

- Evolução do projeto de um conjunto inicial de regras para um laboratório com baseline mensurável, fronteira formal para respostas de agentes, ciclo de vida temporal de workflow e dupla trilha persistente desacoplada.
- Critérios técnicos consideram o custo de negócio dos erros, evitando avaliar qualidade somente por acurácia agregada.
- Respostas externas são tratadas como dados não confiáveis até serem validadas pelo contrato Pydantic.
- Separação mandatória entre a persistência de ciclo de vida operacional (`WorkflowOpened`) e a persistência de deliberação pós-decisão (`AuditEvent`).
- Desenvolvimento orientado por testes (TDD) com fluxo rastreável de engenharia.

### Security

- Registro explícito de que o repositório é público e deve conter somente dados sintéticos, anonimizados e autorizados.
- Proibição documentada de credenciais, chaves de API, documentos proprietários e cadastros reais de empresas.
- Validação estrita da fronteira JSON para impedir que campos inesperados sejam aceitos silenciosamente.
- Preservação obrigatória da revisão humana nas deliberações de governança PDM/BOM (`requires_human_decision = True`).
- Escritas duráveis com sincronização forçada em disco (`flush` + `os.fsync`) e leituras *fail-closed* contra registros corrompidos ou estruturalmente inválidos.

### Deprecated

- Nenhum recurso foi depreciado nesta versão.

### Removed

- Nenhum recurso foi removido nesta versão.

### Fixed

- Nenhuma correção sobre versão pública anterior (primeira release formal do projeto).

## Histórico de versões

- `v0.1.0` — 2026-08-20 — Governed Agent Workflow Baseline.

## Critérios para novas entradas

Inclua uma entrada em `Unreleased` quando uma mudança:

- adicionar funcionalidade ou comportamento público;
- alterar contrato, regra, decisão ou alerta;
- corrigir defeito percebido por usuários;
- modificar instalação, configuração ou execução;
- introduzir depreciação ou remoção;
- alterar segurança, privacidade ou revisão humana;
- mudar resultados ou métricas de avaliação;
- exigir instrução de migração.

Mudanças exclusivamente editoriais podem ser omitidas quando não alterarem o
entendimento ou o uso do projeto.

## Padrão para escrever entradas

Uma boa entrada deve:

- começar pelo resultado observado;
- ser compreensível sem consultar o diff;
- evitar jargão desnecessário;
- identificar incompatibilidade ou migração;
- citar Issue, SPEC ou Pull Request quando isso melhorar a rastreabilidade;
- não incluir dados sensíveis;
- não prometer desempenho que não tenha sido medido.

Prefira:

```text
- Adiciona validação de confiança entre 0 e 1 na saída estruturada.
```

Evite:

```text
- Ajustes no código.
```

## Procedimento de release

Ao preparar uma release:

1. revise todas as entradas de `Unreleased`;
2. remova duplicidades e detalhes puramente internos;
3. identifique mudanças incompatíveis e instruções de migração;
4. defina a versão conforme `VERSIONING.md`;
5. crie a seção `## [X.Y.Z] - AAAA-MM-DD`;
6. mova para ela somente as mudanças incluídas na release;
7. mantenha uma seção `Unreleased` vazia para o próximo ciclo;
8. alinhe o número no `pyproject.toml`;
9. execute os testes e as verificações do Pull Request;
10. crie a tag e a GitHub Release somente após o merge aprovado.

## Responsabilidade humana

As decisões `APPROVE`, `REVIEW` e `REJECT` representam recomendações do sistema.
Nenhuma entrada neste changelog deve sugerir que o agente substitui a decisão de
um profissional autorizado sobre materiais, cadastros ou estruturas PDM/BOM.

Mudanças que alterem evidências, confiança, alertas ou revisão humana devem ser
destacadas de forma explícita.

## Referências de rastreabilidade

- Repositório: <https://github.com/Jk-Pascoal/agent-lab-pascoal>
- Workflow de engenharia: `docs/04_engineering_workflow.md`
- Template de SPEC: `docs/specs/SPEC_TEMPLATE.md`
- SPEC da governança: `docs/specs/0008_engineering_workflow.md`
- Guia de contribuição: `CONTRIBUTING.md`
- Política de versionamento: `VERSIONING.md`

<!--
Links de comparação entre versões devem ser adicionados depois da criação das
tags formais. Não inventar referências para tags ainda inexistentes.

Exemplo futuro:
[Unreleased]: https://github.com/Jk-Pascoal/agent-lab-pascoal/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Jk-Pascoal/agent-lab-pascoal/releases/tag/v0.1.0
-->
