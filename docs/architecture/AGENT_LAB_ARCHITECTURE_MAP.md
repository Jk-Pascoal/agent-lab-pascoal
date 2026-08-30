# Agent Lab Architecture Map

> Contrato da representação arquitetural visual oficial do Agent Lab Pascoal.

## Status

- **Artefato visual oficial:** `docs/architecture/agent_lab_architecture_graph_complete_v1_v2.html`
- **Fonte arquitetural consolidada:** `docs/PROJECT_COMPASS.md`
- **Escopo visual:** V1 fundacional + V2 atual
- **Baseline integrado representado:** 438/438 testes GREEN
- **Última Issue funcional representada:** #77 — Pending Human Review Queue Projection v1
- **Pressões visíveis, não implementadas:** P-07 e P-08
- **Data de formalização:** 2026-08-29

## 1. Papel do grafo

O **Agent Lab Architecture Graph** é a projeção visual oficial e complementar do `PROJECT_COMPASS`.

Ele existe para facilitar reentrada cognitiva, estudo espacial da arquitetura, leitura das relações entre fluxos, módulos, contratos, Issues e invariantes, além de permitir acompanhar a evolução do projeto.

O grafo **interpreta o sistema; não legisla sobre ele**. Uma conexão desenhada no HTML não cria, por si só, um contrato arquitetural.

## 2. Hierarquia de autoridade

Em caso de divergência:

```text
Código + testes integrados
        ↓
SPECs concluídas
        ↓
PROJECT_COMPASS
        ↓
Architecture Graph
```

O grafo deve ser corrigido sempre que divergir do estado integrado.

## 3. Leitura V1 — Fundação

A visão V1 mostra a formação do sistema governado antes de sua expansão temporal e factual:

```text
repositório
├── docs/  → promessa e governança escrita
├── tests/ → promessa executável
└── src/   → implementação
```

Ela preserva a cadeia evolutiva fundacional: harness determinístico, fronteira LLM estruturada, Evidence Engine, Recommendation Pipeline, autoridade humana, memória auditável e identidade verificável.

## 4. Leitura V2 — Estado arquitetural atual

O Agent Lab atual é representado por **três fluxos de domínio interligados**.

### 4.1 Análise e Recomendação

```text
MaterialRecord
→ normalização
→ regras / duplicidades / métricas
→ validação
→ evidências
→ DecisionRecommendation
```

### 4.2 Governança Humana e Temporal

```text
DecisionRecommendation
→ GovernanceWorkflow
→ PENDING_HUMAN_REVIEW
→ HumanReview
→ REVIEWED
→ lifecycle + audit
→ reconstrução / projeção
```

Inclui `RecordHumanDecisionUseCase` e a projeção da fila pendente introduzida pela Issue #77.

### 4.3 Evolução Factual do Material

```text
MaterialRevision
→ persistência factual append-only
→ MaterialRevisionLineage
→ roots / heads / orphans / forks / cycles
```

## 5. Infraestrutura transversal

Persistência, auditoria, serialização, consistency check, projeções e reconstrução pós-restart sustentam mais de um fluxo. Elas **não formam um quarto fluxo de negócio**.

```text
             ┌─ Análise e Recomendação
             │
Material ────┼─ Governança Humana e Temporal
             │
             └─ Evolução Factual do Material

       ↕ persistência · auditoria · projeções · reconstrução
```

## 6. Categorias visuais

O grafo completo usa:

- **Raiz**;
- **Fases V1/V2**;
- **Fluxos**;
- **Estrutura / Docs**;
- **Módulos `src/`**;
- **Contratos / Objetos**;
- **Marcos / Issues**;
- **Invariantes**;
- **Pressões**.

As pressões são visualmente distintas e **não representam capacidade implementada**.

## 7. Princípios arquiteturais representados

```text
Evidence ≠ Decision
Recommendation ≠ HumanReview
confidence ≠ authority
WorkflowLifecycleEvent ≠ AuditEvent
Repository ≠ Projection
CorrectionRequest ≠ MaterialRevision
lineage ≠ current
diagnóstico ≠ reparo
```

Separação de responsabilidades:

```text
Application coordena.
Domain decide.
Repository preserva fatos.
Projection interpreta.
```

## 8. Pressões arquiteturais

O mapa pode exibir pressões ainda não implementadas quando isso ajuda a leitura de fronteira do sistema, desde que estejam marcadas explicitamente como tal.

### P-07 — Industrial Load / Scale Validation

Pressão para validação em 100k+ SKUs, com candidate generation e blocking sem comparação `all-vs-all`.

Princípios candidatos registrados:

- **Semantic Blocking before Similarity**;
- **Classification guides search; it does not constrain truth**;
- classificação declarada não pode funcionar como filtro rígido;
- benchmark deve conter sujeira cadastral real.

### P-08 — Material Supersession / Replacement Lineage

Pressão para representar descontinuação e substituição entre materiais distintos.

Regra candidata:

```text
MaterialRevision ≠ MaterialReplacement
```

P-07 e P-08 continuam **não implementadas** e não são tratadas como Issues funcionais aprovadas.

## 9. Protocolo de atualização

Após um incremento funcional integrado:

```text
merge na main
→ suíte canônica GREEN
→ PROJECT_COMPASS atualizado
→ avaliar impacto topológico
→ atualizar Architecture Graph quando necessário
```

Atualizar o grafo quando houver novo fluxo, boundary, contrato central, relação causal/temporal, infraestrutura transversal relevante, invariante ou Issue que altere significativamente a topologia.

## 10. Regra de divergência

Se `PROJECT_COMPASS` e Architecture Graph divergirem:

1. verificar código, testes e SPECs integrados;
2. usar o `PROJECT_COMPASS` como ponto oficial de reentrada consolidada;
3. corrigir o grafo;
4. registrar a atualização documental pelo fluxo normal de Git/PR.

## 11. Estado representado nesta versão

A visão completa preserva a fundação V1 e acompanha a evolução V2 até:

- #71 — Material Revision Lineage Projection v1 — baseline 412;
- #74 — Human Review Application Use Case v1 — baseline 423;
- #77 — Pending Human Review Queue Projection v1 — baseline 438.

O arquivo possui presets de navegação **Macro**, **V1 Fundação**, **V2 Atual** e **Tudo**, permitindo estudar a arquitetura em diferentes níveis sem criar fontes de verdade concorrentes.
