# Agent Lab Architecture Map

> Contrato da representação arquitetural visual oficial do Agent Lab Pascoal.

## Status

- **Artefato visual oficial:** `docs/architecture/agent_lab_architecture_graph_v2.html`
- **Fonte arquitetural consolidada:** `docs/PROJECT_COMPASS.md`
- **Baseline representado:** 438/438 testes GREEN
- **Última Issue funcional representada:** #77 — Pending Human Review Queue Projection v1
- **Data de formalização:** 2026-08-29

## 1. Papel do grafo

O **Agent Lab Architecture Graph** é a projeção visual oficial e complementar do `PROJECT_COMPASS`.

Ele existe para:

- facilitar reentrada cognitiva no projeto;
- permitir estudo espacial da arquitetura;
- tornar visíveis relações entre fluxos, módulos, contratos, Issues e invariantes;
- ajudar a detectar lacunas, acoplamentos e pressões arquiteturais;
- acompanhar a evolução do sistema sem substituir os artefatos normativos.

O grafo **interpreta o sistema; não legisla sobre ele**.

Uma conexão desenhada no HTML não cria, por si só, um contrato arquitetural. Relações arquiteturais precisam estar sustentadas pelo estado integrado do projeto — código, testes, SPECs e `PROJECT_COMPASS`.

## 2. Hierarquia de autoridade

Em caso de divergência, usar esta ordem de verificação:

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

## 3. Leitura macro oficial

O Agent Lab é representado por **três fluxos de domínio interligados**:

### 3.1 Análise e Recomendação

```text
MaterialRecord
→ normalização
→ regras / duplicidades / métricas
→ validação
→ evidências
→ DecisionRecommendation
```

Pergunta central: **o que os dados e as evidências permitem recomendar?**

### 3.2 Governança Humana e Temporal

```text
DecisionRecommendation
→ GovernanceWorkflow
→ PENDING_HUMAN_REVIEW
→ HumanReview
→ REVIEWED
→ lifecycle + audit
→ reconstrução / projeção
```

Inclui o primeiro boundary explícito de Application Layer (`RecordHumanDecisionUseCase`) e a projeção da fila pendente.

Pergunta central: **como a decisão humana é coordenada, preservada e reconstruída no tempo?**

### 3.3 Evolução Factual do Material

```text
MaterialRevision
→ persistência factual append-only
→ MaterialRevisionLineage
→ roots / heads / orphans / forks / cycles
```

Pergunta central: **como a história factual do material evolui sem reescrever o passado?**

## 4. Infraestrutura transversal

Persistência, auditoria, serialização, projeções e reconstrução de estado sustentam mais de um fluxo. Elas **não formam um quarto fluxo de negócio**.

Síntese:

```text
             ┌─ Análise e Recomendação
             │
Material ────┼─ Governança Humana e Temporal
             │
             └─ Evolução Factual do Material

       ↕ persistência · auditoria · projeções · reconstrução
```

## 5. Categorias visuais

O grafo usa as seguintes categorias:

- **Raiz:** visão integrada do Agent Lab;
- **Fluxos:** os três caminhos macro de domínio;
- **Módulos `src/`:** localização da implementação;
- **Contratos/objetos:** entidades, eventos e read-models relevantes;
- **Marcos (Issues):** incrementos que alteraram a topologia arquitetural;
- **Invariantes:** condições que devem permanecer verdadeiras para preservar coerência.

## 6. Princípios arquiteturais representados

Entre os princípios e separações canônicas:

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

E a separação de responsabilidades:

```text
Application coordena.
Domain decide.
Repository preserva fatos.
Projection interpreta.
```

## 7. Protocolo de atualização

Após um incremento funcional integrado:

```text
merge na main
→ suíte canônica GREEN
→ PROJECT_COMPASS atualizado
→ avaliar se a topologia arquitetural mudou
→ atualizar Architecture Graph quando necessário
```

Atualizar o grafo quando houver, por exemplo:

- novo fluxo ou subfluxo relevante;
- novo boundary arquitetural;
- novo contrato central;
- nova relação causal ou temporal;
- nova infraestrutura transversal relevante;
- nova invariante;
- Issue que altere significativamente a topologia existente.

Não é necessário atualizar o grafo para mudanças internas que não alterem sua leitura arquitetural.

## 8. Regra de divergência

Se `PROJECT_COMPASS` e Architecture Graph divergirem:

1. não reinterpretar silenciosamente o código para fazer o desenho “caber”;
2. verificar código, testes e SPECs integrados;
3. usar o `PROJECT_COMPASS` como ponto oficial de reentrada consolidada;
4. corrigir o grafo;
5. registrar a atualização documental no fluxo normal de Git/PR.

## 9. Estado representado nesta versão

A V2 formalizada incorpora a evolução até:

- #71 — Material Revision Lineage Projection v1 — baseline 412;
- #74 — Human Review Application Use Case v1 — baseline 423;
- #77 — Pending Human Review Queue Projection v1 — baseline 438.

Pressões arquiteturais ainda não implementadas, como **P-07 (Industrial Load / Scale Validation)** e **P-08 (Material Supersession / Replacement Lineage)**, não são desenhadas como capacidades existentes. Elas só devem entrar na topologia oficial quando houver decisão arquitetural ou incremento integrado que justifique sua representação.
