# PROJECT COMPASS — Agent Lab Pascoal

> Ponto oficial de reentrada cognitiva e operacional do projeto.
>
> Leia este documento antes de propor uma nova Issue, SPEC ou alteração de código.

## 1. Identidade do projeto

- **Projeto:** Agent Lab Pascoal
- **Repositório:** `Jk-Pascoal/agent-lab-pascoal`
- **Domínio:** governança de materiais PDM/BOM e Master Data
- **Linguagem:** Python 3.11
- **Runner oficial de testes:** `unittest`
- **Branch protegida:** `main`
- **Estado registrado em:** 2026-08-20
- **Baseline integrado na main:** 206 testes aprovados
- **Última entrega funcional integrada na main:** Workflow Opening Persistence v1
- **Última Issue funcional concluída na main:** #47
- **Último PR funcional integrado na main:** #48
- **Último merge funcional:** `eabd659` — Merge pull request #48
- **Última SPEC integrada:** `docs/specs/0047_workflow_opening_persistence_v1.md`
- **Incremento funcional atual:** Nenhum incremento funcional aberto — próxima âncora a definir
- **Release formal atual:** `v0.1.0` — Governed Agent Workflow Baseline
- **Status da release:** publicada / Latest
- **Tag:** `v0.1.0`
- **Commit âncora da release:** `c5a9e462d535f90212c59c6f3f7b1354450170de`
- **PR de preparação da release:** #50 — docs: preparar release v0.1.0

> **Distinção de governança:** Merge fecha um incremento; release fecha uma versão coerente.

## 2. Propósito

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais. Seu objetivo é apoiar a análise de cadastros PDM/BOM por meio de uma arquitetura híbrida que combina:

- regras determinísticas;
- normalização e validação de dados;
- detecção de duplicidades;
- saídas estruturadas de LLM;
- evidências auditáveis;
- recomendações de decisão;
- revisão humana obrigatória;
- ciclo de vida temporal de governança em memória com persistência append-only de abertura e reidratação;
- trilha de auditoria append-only desacoplada.

O sistema não substitui o especialista de governança. Ele organiza evidências, detecta riscos, gerencia o ciclo temporal de revisão e produz recomendações para apoiar uma decisão humana rastreável.

## 3. Tese arquitetural

O projeto segue uma rigorosa separação de responsabilidades em duas trilhas persistentes complementares e desacopladas:

```text
Decision Recommendation
        ↓
GovernanceWorkflow
        ↓
┌────────────────────────────────────┐
│                                    │
│ abertura do ciclo                  │ decisão humana
│                                    │
▼                                    ▼
WorkflowOpened                    HumanReview
        ↓                            ↓
Workflow lifecycle              AuditEvent
serialization v1                    ↓
        ↓                        Audit serialization v1
Workflow lifecycle                  ↓
repository JSONL                 Audit repository JSONL
        ↓
rehydrate_pending_workflow
        ↓
GovernanceWorkflow
(PENDING_HUMAN_REVIEW)
```

Separação conceitual mandatória:
- **`WorkflowOpened ≠ AuditEvent`**
- **Workflow lifecycle persistence (`WorkflowOpened`):** preserva os fatos do ciclo temporal de governança operacional e viabiliza a reidratação determinística de workflows pendentes após reinicialização do processo;
- **Audit persistence (`AuditEvent`):** preserva a evidência imutável da deliberação do especialista humano pós-decisão;
- Não fundir as duas responsabilidades em uma mesma entidade ou repositório.

Princípio central:

```text
A IA recomenda; o humano decide; a auditoria preserva o percurso; o lifecycle preserva o estado operacional.
```

## 4. Estado arquitetural atual

### 4.1 Baseline versionado atual (v0.1.0)

A versão `v0.1.0 — Governed Agent Workflow Baseline` é a primeira release formal e versionada do laboratório. Ela consolida uma linha de base fundacional composta por:

- baseline determinístico e validação cadastral de materiais;
- fronteira LLM estruturada, tipada e com guardrail de identidade (`MaterialIdentityMismatchError`);
- Evidence Engine multiorigem (`RULE`, `VALIDATION`, `DUPLICATE`, `LLM`);
- recommendation pipeline determinístico com compulsoriedade de `requires_human_decision = True`;
- deliberação humana estruturada via `HumanReview` com `VerifiedSpecialistIdentity`;
- persistência auditável durável append-only (`AuditEvent` com `schema_version = 1` e `JsonlAuditRepository`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow` com `opened_at`, `closed_at`, `review_lead_time`);
- evento de domínio imutável `WorkflowOpened`;
- persistência de lifecycle de abertura append-only (`JsonlWorkflowLifecycleRepository` com `schema_version = 1`);
- projeção pura de reidratação de workflows pendentes (`rehydrate_pending_workflow`) sem reexecução de regras ou chamadas a LLM.

### 4.2 Núcleo normativo implementado

O sistema já representa e valida:

- materiais e atributos relevantes;
- normalização de descrições;
- validações cadastrais;
- possíveis duplicidades;
- issues estruturadas;
- severidade de problemas;
- evidências de regras e LLM;
- recomendações `APPROVE`, `REVIEW` e `REJECT`;
- confiança da recomendação;
- revisão humana;
- aprovação, reprovação e solicitação de correção;
- concordância e divergência humano–sistema;
- `VerifiedSpecialistIdentity`;
- proveniência da identidade humana;
- correlação entre `specialist_id`, `HumanReview` e `AuditEvent`;
- `WorkflowStatus.PENDING_HUMAN_REVIEW` e `WorkflowStatus.REVIEWED`;
- `GovernanceWorkflow` imutável e temporal em memória;
- transição pura canônica via `conclude_governance_workflow`;
- `opened_at` explícito e timezone-aware;
- propriedades derivadas `material_id`, `status`, `closed_at` e `review_lead_time`;
- validação temporal cronológica `opened_at <= reviewed_at`;
- validação de coerência de material e do parecer (`review.system_recommendation == recommendation.decision`);
- bloqueio estrito de dupla conclusão;
- integração ponta a ponta entre `GovernanceWorkflow`, `HumanReview`, `AuditEvent` e `JsonlAuditRepository`;
- eventos de auditoria imutáveis com `schema_version = 1` isolado;
- persistência local append-only de auditoria com `JsonlAuditRepository`;
- evento de domínio imutável `WorkflowOpened` com `event_id`, `workflow_id`, `recommendation` e `opened_at`;
- serialização versionada de lifecycle (`schema_version = 1`) com preservação integral de `DecisionRecommendation` e `GovernanceEvidence`;
- repositório `JsonlWorkflowLifecycleRepository` append-only com escrita durável (`flush` + `os.fsync`);
- leitura *fail-closed* com identificação precisa de `line_number` em caso de corrupção;
- bloqueio de `event_id` duplicado (`DuplicateWorkflowEventError`) e bloqueio de segunda abertura para o mesmo `workflow_id` (`WorkflowAlreadyOpenedError`);
- projeção pura `rehydrate_pending_workflow` reconstituindo fielmente `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` sem reexecução de regras ou LLM;
- conclusão de workflow reidratado via `conclude_governance_workflow` com validação de ciclo completo.

### 4.3 Limite atual

A versão atual possui:

- apenas o fato de **abertura** (`WorkflowOpened`) possui persistência de lifecycle implementada;
- `WorkflowConcluded` ainda não existe;
- `HumanReview` não possui representação completa serializada no repositório de lifecycle;
- o estado `REVIEWED` ainda não pode ser reconstituído a partir do log de lifecycle (somente o estado `PENDING_HUMAN_REVIEW` sobrevive a restart);
- `closed_at` não é persistido no lifecycle log;
- `review_lead_time` continua derivado em memória no domínio;
- múltiplos ciclos de workflow e reabertura após correção permanecem fora do escopo;
- execução síncrona/monoprocesso;
- ausência de autenticação e autorização real (RBAC);
- ausência de filas e SLAs operacionais;
- ausência de integração com ERP.

### 4.4 Próxima âncora

Próxima âncora arquitetural: a definir após análise explícita da limitação atual.

A evolução para persistência do fechamento de ciclo (`WorkflowConcluded`) constitui uma extensão natural futura, mas permanece explicitamente fora do escopo atual até definição em nova Issue.

Sequência evolutiva recomendada:

```text
Contrato
  → Memória persistente
  → Identidade verificável
  → Workflow temporal
  → Persistência de abertura de workflow (concluída na #47)
  → Persistência de conclusão de workflow
  → Integração ERP
```

## 5. Invariantes constitucionais

Estas regras não devem ser alteradas incidentalmente:

1. A recomendação automática nunca é uma decisão humana.
2. `requires_human_decision` permanece `True` no escopo atual.
3. Confiança não concede autoridade operacional.
4. A recomendação original não pode ser sobrescrita pela decisão humana.
5. Divergências humano–sistema devem permanecer auditáveis.
6. Revisões concluídas e eventos de auditoria e lifecycle são imutáveis.
7. Reprovação exige justificativa.
8. Solicitação de correção exige justificativa e correção estruturada.
9. Aprovação não pode conter correções pendentes.
10. Timestamps de abertura de workflow, revisão e auditoria devem conter timezone.
11. A integração com ERP não deve executar apenas com base em recomendação automática.
12. O histórico não deve ser reconstruído somente a partir do estado final.
13. Concordância humano–IA não equivale automaticamente à verdade.
14. Casos objetivos devem ser resolvidos por regras antes de recorrer à LLM.
15. A LLM deve operar com contratos de saída estruturados e validados.
16. A recomendação do sistema permanece imutável e atemporal; o tempo pertence ao ciclo de vida (`GovernanceWorkflow`).
17. Um workflow não pode ser concluído mais de uma vez e a transição deve ser pura e determinística.
18. O repositório de ciclo de vida é append-only e opera sob o princípio `Repository != Projection`.

Qualquer mudança nessas regras exige:

- Issue explícita;
- evidências;
- análise de impacto;
- nova SPEC ou atualização deliberada de SPEC;
- testes que demonstrem o novo comportamento;
- revisão humana no PR.

## 6. Contratos e módulos centrais

### 6.1 Domínio e validação

```text
src/agent_lab/domain.py
src/agent_lab/normalization.py
src/agent_lab/validator.py
src/agent_lab/decision.py
```

Responsabilidades:

- tipos centrais;
- normalização;
- validação determinística;
- recomendação de decisão atemporal.

### 6.2 LLM e evidências

```text
src/agent_lab/llm_schema.py
src/agent_lab/llm_service.py
src/agent_lab/evidence.py
```

Responsabilidades:

- contrato estruturado da LLM;
- fronteira de execução da LLM;
- evidências originadas por regras e modelo;
- preservação da identidade do material;
- integração evidência–decisão.

### 6.3 Human-in-the-Loop

```text
src/agent_lab/human_review.py
```

Contratos principais:

- `VerifiedSpecialistIdentity`;
- `HumanDecision`;
- `CorrectionRequest`;
- `HumanReview`.

Responsabilidades:

- representar a decisão final humana;
- preservar a recomendação automática;
- registrar especialista e timestamp timezone-aware;
- estruturar correções;
- indicar concordância ou divergência.

### 6.4 Workflow Temporal de Domínio

```text
src/agent_lab/workflow.py
```

Contratos principais:

- `WorkflowStatus`;
- `GovernanceWorkflow`;
- `conclude_governance_workflow`.

Responsabilidades:

- representar o ciclo de vida temporal da governança em memória;
- abrir ciclos em estado `PENDING_HUMAN_REVIEW` com timestamp `opened_at` timezone-aware;
- derivar `material_id`, `status`, `closed_at` e `review_lead_time` sem duplicação de estado;
- executar a transição canônica pura para `REVIEWED` ao receber deliberação de `HumanReview`;
- validar consistência de material, coerência do parecer e invariantes cronológicas (`opened_at <= reviewed_at`);
- manter o objeto estritamente imutável.

### 6.5 Ciclo de Vida: Eventos, Projeção, Serialização e Repositório

```text
src/agent_lab/workflow_events.py
src/agent_lab/workflow_projection.py
src/agent_lab/workflow_serialization.py
src/agent_lab/workflow_repository.py
```

Contratos principais:

- `WorkflowOpened`: evento de domínio imutável da abertura do ciclo;
- `rehydrate_pending_workflow`: projeção pura reconstruindo `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW`;
- `workflow_opened_to_record` / `workflow_opened_from_record`: serialização versionada (`schema_version = 1`);
- `WorkflowLifecycleRepository` (Protocol) / `JsonlWorkflowLifecycleRepository`: repositório append-only em JSONL com escrita durável (`os.fsync`) e leitura *fail-closed*;
- `WorkflowPersistenceError`, `DuplicateWorkflowEventError`, `WorkflowAlreadyOpenedError`, `WorkflowCorruptionError`.

### 6.6 Auditoria

```text
src/agent_lab/audit.py
```

Contratos principais:

- `AuditEventType`;
- `AuditEvent`;
- `HumanReviewResult`;
- `record_human_review`.

Responsabilidades:

- criar evento correlacionado à revisão humana;
- congelar metadados defensivamente;
- preservar material, especialista, instante e decisão;
- produzir resultado auditável sem persistência ou efeitos externos.

### 6.7 Persistência e repositório de auditoria

```text
src/agent_lab/audit_serialization.py
src/agent_lab/audit_repository.py
```

Contratos principais:

- `audit_event_to_record`;
- `audit_event_from_record`;
- `AuditRepository`;
- `JsonlAuditRepository`;
- `AuditPersistenceError`;
- `DuplicateAuditEventError`;
- `AuditCorruptionError`.

Responsabilidades:

- serializar e desserializar `AuditEvent` com versão de schema explícita (`schema_version = 1`);
- persistir eventos de forma append-only em arquivo JSONL local;
- garantir sincronização em disco com `flush` e `os.fsync`;
- recuperar histórico por `event_id`, `material_id` e listagem completa;
- falhar de forma *fail-closed* diante de corrupção ou duplicidade.

## 7. Comando canônico de testes e baseline

Use sempre:

```powershell
python -m unittest discover -s tests -v
```

Baseline oficial integrado na `main`:

```text
Ran 206 tests
OK
```

Incremento da Issue #47: +54 testes sobre o baseline anterior de 152.

Não assumir `pytest`.

Uma migração de runner somente poderá ocorrer por decisão explícita, documentada e testada.

## 8. Métrica de custo do baseline

O baseline utiliza uma função de custo ponderado inicial:

```text
duplicidade não detectada = custo 5
revisão humana desnecessária = custo 1
```

Representação:

```text
custo = 5 × falsos negativos de duplicidade
      + 1 × revisões desnecessárias
```

Interpretação:

- deixar uma duplicidade entrar tende a produzir efeitos sistêmicos;
- uma revisão desnecessária tende a produzir custo localizado de tempo e fila;
- o valor 5:1 é uma hipótese inicial de risco, não uma constante universal;
- a razão deverá ser calibrada com dados industriais reais.

## 9. Fronteira de autoridade

`DecisionRecommendation` é uma recomendação, não uma autorização.

Mesmo quando:

```text
decision = APPROVE
confidence = 1.0
```

o contrato deve preservar:

```text
requires_human_decision = True
```

Razão:

```text
confiança epistemológica ≠ autoridade operacional
```

Uma integração futura com ERP deverá exigir decisão humana válida e auditável, e não apenas recomendação automática.

## 10. Protocolo diário de reentrada

Ao iniciar uma nova rotina do Agent Lab, seguir esta ordem.

### Passo 1 — Ler este Compass

Confirmar:

- propósito;
- estado arquitetural;
- baseline;
- última entrega;
- próxima âncora;
- invariantes.

### Passo 2 — Verificar o Git

```powershell
git status
git branch --show-current
git log -5 --oneline
```

Confirmar:

- branch atual;
- sincronização com `origin/main`;
- working tree;
- últimos commits.

### Passo 3 — Confirmar o contrato operacional

Antes de recomendar comandos:

- verificar Python configurado;
- verificar workflow da CI;
- verificar runner oficial;
- verificar estrutura de arquivos;
- não substituir fatos do repositório por convenções genéricas.

### Passo 4 — Executar o baseline

```powershell
python -m unittest discover -s tests -v
```

Não iniciar nova implementação se o baseline estiver vermelho sem diagnóstico explícito.

### Passo 5 — Recapitular o estado

Registrar em poucas linhas:

```text
Núcleo atual:
Última entrega:
Baseline:
Limitação principal:
Próxima âncora:
```

### Passo 6 — Somente então abrir nova Issue

Toda Issue deve conter, conforme aplicável:

- problema;
- contexto;
- objetivo;
- evidências;
- solução ou hipóteses;
- escopo;
- fora do escopo;
- riscos e limitações;
- impactos;
- critérios de aceite;
- estratégia de validação.

## 11. Fluxo de engenharia

Fluxo padrão:

```text
Issue
  → branch
  → SPEC
  → commit documental
  → teste RED
  → commit do teste
  → implementação GREEN
  → regressão completa
  → atualização da SPEC
  → push
  → Pull Request
  → CI
  → merge
  → exclusão da branch
  → sincronização da main
  → validação pós-merge
  → Relatório Diário
```

O Relatório Diário é uma etapa obrigatória do encerramento técnico.

## 12. Hierarquia das fontes de verdade

Em caso de dúvida ou conflito, usar esta ordem:

1. comportamento validado pelos testes atuais;
2. código integrado à `main`;
3. SPEC implementada mais recente;
4. workflows e configurações do repositório;
5. este `PROJECT_COMPASS.md`;
6. Relatórios Diários;
7. memória conversacional;
8. convenções genéricas de engenharia.

Se este Compass divergir da `main`, a `main` e seus testes prevalecem e o Compass deve ser atualizado.

## 13. Decisões deliberadamente adiadas

- persistência de fechamento de ciclo (`WorkflowConcluded`);
- reconstrução do estado `REVIEWED` a partir do lifecycle log;
- múltiplos ciclos de workflow ou reabertura após solicitação de correção;
- persistência em banco de dados;
- proteção física ou criptográfica contra adulteração do histórico;
- event sourcing completo;
- autenticação e autorização;
- papéis e segregação de funções;
- taxonomia completa de motivos;
- filas e SLAs;
- notificações e escalonamento;
- interface do especialista;
- integração e fila de injeção ERP;
- idempotência e retentativas da integração;
- métricas de override humano–IA;
- benchmark industrial com ground truth;
- automação parcial por classe de risco.

Não implementar uma decisão adiada incidentalmente dentro de outra Issue.

## 14. Esteira evolutiva

Frentes oficiais de evolução:

- PoC vendável de diagnóstico de qualidade cadastral;
- Duplicate Intelligence;
- prevenção de novos cadastros duplicados;
- copiloto do analista PDM;
- arquitetura híbrida de regras, similaridade, RAG e LLM;
- Evidence Engine;
- Human-in-the-Loop;
- workflow temporal e métricas de ciclo de revisão;
- persistência e reidratação de lifecycle de workflow;
- benchmark com ground truth;
- métricas de precision, recall e F1;
- versionamento de dados;
- dashboards;
- integração com CSV, Excel, SQL e ERP.

Essas frentes formam uma esteira; não são autorização para desenvolvimento simultâneo.

## 15. Critérios para a próxima Issue

Antes de abrir a próxima Issue, responder:

1. Qual limitação atual ela resolve?
2. Qual evidência demonstra que a limitação importa agora?
3. Qual é a menor entrega vertical testável?
4. Quais invariantes ela deve preservar?
5. O que ficará explicitamente fora do escopo?
6. Como saberemos que a implementação funcionou?
7. Quantos novos riscos operacionais ela introduz?
8. A nova camada pode ser removida ou substituída sem corromper o domínio?

## 16. Política de atualização deste Compass

Atualizar este documento quando houver mudança em:

- baseline de testes;
- comando canônico;
- arquitetura;
- invariantes;
- última entrega;
- próxima âncora;
- módulos centrais;
- limites do sistema;
- decisões deliberadamente adiadas.

Não atualizar o Compass por alterações cosméticas ou tarefas que não modifiquem o estado estrutural do projeto.

Toda atualização deve ocorrer na mesma branch da mudança que a tornou necessária, ou em uma Issue documental explicitamente vinculada.

## 17. Estado resumido para reentrada rápida

```text
AGENT LAB PASCOAL

Propósito:
Governança assistida de materiais PDM/BOM.

Release formal atual:
v0.1.0 — Governed Agent Workflow Baseline (publicada / Latest | tag v0.1.0 | commit c5a9e46).

Distinção de governança:
Merge fecha um incremento; release fecha uma versão coerente.

Arquitetura atual:
Regras + LLM estruturada + evidências + recomendação + identidade verificável
+ decisão humana + workflow temporal + persistência append-only de WorkflowOpened
+ reidratação de workflow pendente + auditoria append-only desacoplada.

Autoridade:
A IA recomenda; o humano decide.

Baseline:
206 testes | unittest | Python 3.11.

Última entrega funcional integrada na main:
Issue #47 | Workflow Opening Persistence v1 | PR #48 (merge eabd659).

Incremento funcional atual:
Nenhum incremento funcional aberto.

Limite atual:
Abertura de workflow sobrevive a restart; conclusão/REVIEWED continua sem
reconstrução integral de lifecycle; sem autenticação/autorização real, filas, SLAs ou ERP.

Próxima âncora:
A definir por nova análise/Issue (WorkflowConcluded permanece extensão futura candidata).

Comando oficial:
python -m unittest discover -s tests -v
```
