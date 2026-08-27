# SPEC 0071 — Material Revision Lineage Projection v1

> Especificação técnica da projeção pura, determinística e somente-leitura (`read-only`)
> de linhagem de revisões de materiais (`MaterialRevision`) no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0071` |
| Status | `IMPLEMENTED / Concluído e integrado à main` |
| Issue relacionada | `#71` |
| PR relacionado | `#72` |
| Merge commit | `eea57ee` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-27` |
| Data de conclusão | `2026-08-27` |
| Última atualização | `2026-08-27` |
| Baseline de entrada | `397 testes aprovados` |
| Baseline final | `412 testes aprovados (+15 testes)` |
| Runner oficial | `unittest` / Python 3.11 |

---

## 1. Contexto

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais PDM/BOM. O baseline atual integrado na branch `main` possui **397 testes aprovados** (`unittest`, Python 3.11) e consolida:

- validação cadastral determinística e fronteira LLM estruturada com guardrails de identidade;
- Evidence Engine multiorigem (`RULE`, `VALIDATION`, `DUPLICATE`, `LLM`) e pipeline de recomendação determinístico com `requires_human_decision = True`;
- deliberação humana estruturada via `HumanReview` com `VerifiedSpecialistIdentity`;
- persistência durável append-only de auditoria (`AuditEvent` com `schema_version = 1` e `JsonlAuditRepository`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow`);
- persistência durável append-only de abertura e conclusão de ciclo de vida (`WorkflowOpened` v1/v2, `WorkflowConcluded` v1 e `JsonlWorkflowLifecycleRepository`);
- projeção determinística de reidratação de workflow (`rehydrate_workflow`) reconstruindo `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` e `REVIEWED`;
- verificação somente-leitura de consistência cruzada dual-write (`verify_dual_write_consistency`, `verify_repositories_consistency`);
- linhagem causal de follow-up pós-correção (`open_correction_follow_up`) com persistência versionada (`schema_version = 2`);
- contrato factual de proveniência de revisões de material em memória (`MaterialRevision` e `create_successor_revision`, Issue #64);
- persistência append-only durável e fail-closed de revisões factuais de materiais (`schema_version = 1` e `JsonlMaterialRevisionRepository`, Issue #68).

Baseline oficial verificado:

```text
Ran 397 tests in 1.642s
OK
```

Runner oficial:

```powershell
python -m unittest discover -s tests -v
```

---

## 2. Separação conceitual: Repository vs. Projection

A arquitetura do Agent Lab opera sob o princípio constitucional mandatório:

```text
Repository != Projection
```

- **`Repository` (`JsonlMaterialRevisionRepository`):** Responde exclusivamente **quais fatos foram persistidos em disco**. Sua responsabilidade é armazenar registros em formato append-only com durabilidade física (`flush` + `os.fsync`), garantir unicidade do identificador da linha (`revision_id`), recuperar linhas na ordem física de inserção e acusar corrupção com `line_number`. O repositório **não** interpreta causalidade de domínio, **não** valida integridade referencial global entre revisões e **não** ordena registros logicamente. A ordem física do arquivo JSONL é apenas a cronologia de escrita em disco.
- **`Projection` (esta SPEC):** É uma função pura e determinística em memória que recebe uma coleção de fatos persistidos (`Sequence[MaterialRevision]`) e **interpreta a topologia e a estrutura de linhagem formada por esses fatos**. A projeção não executa I/O, não muta objetos, não preserva a ordem física de entrada e não altera o repositório.

---

## 3. Problema, evidências e impacto

### Problema

Atualmente, o repositório armazena revisões individuais de forma append-only sem impor regras globais de integridade referencial. Consequentemente, uma coleção de revisões persistidas para um mesmo material pode conter:

1. **Predecessor inexistente / Órfão (`Orphan`):** Uma revisão declara `predecessor_revision_id = "REV-X"`, mas `REV-X` não existe na coleção;
2. **Múltiplas Raízes (`Multiple Roots`):** Mais de uma revisão declara `predecessor_revision_id = None` para o mesmo `material_id` (raízes desconectadas / floresta);
3. **Bifurcações / Ramificações (`Forks`):** Múltiplas revisões distintas apontam para o mesmo `predecessor_revision_id`;
4. **Ciclos Indiretos (`Cycles`):** Ciclos de dependência de tamanho $\ge 2$ (ex: `REV-A` $\rightarrow$ `REV-B` $\rightarrow$ `REV-A`), uma vez que o contrato individual de `MaterialRevision` bloqueia apenas auto-referência direta de tamanho 1 (`predecessor_revision_id == revision_id`);
5. **Múltiplas Folhas (`Multiple Heads`):** Consequência de forks ou múltiplas raízes, onde mais de uma revisão é candidata a estado final;
6. **Mistura de Materiais (`Material Mix`):** Fornecimento acidental de revisões de diferentes `material_id` para uma projeção de linhagem.

O sistema hoje **não possui nenhum read-model (projeção)** capaz de inspecionar, diagnosticar e estruturar essas condições de linhagem.

### Evidências

- Em `src/agent_lab/material_revision_repository.py`, as listagens (`list_by_material`, `list_all`) retornam unicamente tuplas de revisões na ordem física de escrita;
- Inexistência de um módulo `src/agent_lab/material_revision_projection.py`;
- `docs/PROJECT_COMPASS.md` registrava a projeção de grafo e linhagem de revisões como decisão deliberadamente adiada.

### Impacto

- Impossibilidade de reconstruir com segurança a história evolutiva de um material;
- Impossibilidade de detectar anomalias ou bifurcações cadastrais persistidas;
- Risco de componentes consumidores assumirem erroneamente que a última linha gravada no JSONL é a "revisão atual" de um material.

---

## 4. Decisão humana de arquitetura e diretrizes centrais

1. **Sem eleição arbitrária de revisão atual:** Esta versão v1 **NÃO** introduz os conceitos de `latest revision`, `current revision` ou `canonical head`. Quando existirem ambiguidades (múltiplas heads, forks, múltiplas roots ou órfãos), a projeção deve **representar e diagnosticar explicitamente todas as heads concorrentes e anomalias topológicas**, sem escolher silenciosamente uma delas com base em timestamp ou ordem física.
2. **Determinismo rigoroso (incluindo `revisions`):** A interpretação de linhagem deve produzir exatamente a mesma estrutura em todas as saídas independentemente da permutação física de entrada. Não apenas as tuplas de identificadores (`*_ids`) são ordenadas lexicograficamente, como também a tupla `revisions` é retornada de forma canônica e determinística ordenada por `revision_id` em ordem lexicográfica ascendente (`sorted(revisions, key=lambda r: r.revision_id)`). A ordem física de append/entrada **nunca** é preservada semanticamente pela Projection.
3. **Imutabilidade estrita:** O read-model projetado deve ser uma estrutura congelada e imutável (`dataclass(frozen=True, slots=True)` com tuplas imutáveis).
4. **Fronteira pura:** A projeção opera estritamente em memória; não realiza I/O, não acessa disco, não altera repositórios, não repara dados e não muta instâncias de `MaterialRevision` ou `MaterialRecord`.
5. **Rejeição fail-closed de sequência vazia:** `project_material_revision_lineage(())` deve levantar `ValueError`. Sem nenhuma `MaterialRevision`, a função não possui fonte válida para determinar o `material_id`, que permanece obrigatoriamente `str` (sem coerção para `None` ou tipo opcional `str | None`).

---

## 5. Objetivo

Implementar o módulo `src/agent_lab/material_revision_projection.py` contendo:

1. O modelo de leitura imutável `MaterialRevisionLineage`;
2. A função pura e determinística `project_material_revision_lineage(revisions: Sequence[MaterialRevision]) -> MaterialRevisionLineage`;
3. Diagnóstico formal e tipado de:
   - Raízes (`root_revision_ids`);
   - Folhas / Cabeças (`head_revision_ids`);
   - Órfãos (`orphan_revision_ids`);
   - Bifurcações / Predecessores bifurcados (`fork_predecessor_ids`);
   - Ciclos indiretos (`cycle_revision_ids`);
4. Validação estrita de homogeneidade de `material_id` (rejeição de mistura de materiais com `ValueError`);
5. Rejeição fail-closed de sequências vazias com `ValueError`;
6. Cobertura integral dos cenários e critérios de aceite definidos nesta SPEC por testes unitários e de integração com `JsonlMaterialRevisionRepository` após restart.

---

## 6. Escopo

### Incluído

1. **Módulo de Projeção (`src/agent_lab/material_revision_projection.py`):**
   - Dataclass imutável `MaterialRevisionLineage`:
     - `material_id: str` (identificador do material, derivado estritamente das revisões fornecidas)
     - `revisions: tuple[MaterialRevision, ...]` (revisões projetadas, obrigatoriamente ordenadas por `revision_id` em ordem lexicográfica ascendente)
     - `root_revision_ids: tuple[str, ...]` (IDs das revisões raiz, ordenadas lexicograficamente)
     - `head_revision_ids: tuple[str, ...]` (IDs das revisões folha/head, ordenadas lexicograficamente)
     - `orphan_revision_ids: tuple[str, ...]` (IDs das revisões cujo predecessor inexiste no conjunto, ordenadas lexicograficamente)
     - `fork_predecessor_ids: tuple[str, ...]` (IDs dos predecessores referenciados por >1 revisão, ordenados lexicograficamente)
     - `cycle_revision_ids: tuple[str, ...]` (IDs das revisões que participam efetivamente de ciclos de linhagem, ordenadas lexicograficamente)
     - Propriedades auxiliares booleanas:
       - `is_linear: bool` (`len(root_revision_ids) == 1 and len(head_revision_ids) == 1 and not has_orphans and not has_forks and not has_cycles`)
       - `has_orphans: bool`
       - `has_forks: bool`
       - `has_multiple_roots: bool`
       - `has_cycles: bool`
       - `has_ambiguities: bool` (`has_orphans or has_forks or has_multiple_roots or has_cycles or len(head_revision_ids) != 1`)
   - Função pura `project_material_revision_lineage(revisions: Sequence[MaterialRevision]) -> MaterialRevisionLineage`:
     - Validação de tipo de entrada (`isinstance(revisions, collections.abc.Sequence)`, rejeitando tipos não-sequência com `TypeError`);
     - Validação de elementos (cada item deve ser `MaterialRevision`, rejeitando tipos inválidos com `TypeError`);
     - Validação de não-vacuidade (rejeitando sequência vazia com `ValueError`);
     - Validação de unicidade de `material_id` (rejeitando mistura de materiais com `ValueError`);
     - Validação de unicidade de `revision_id` no conjunto de entrada (rejeitando duplicatas com `ValueError`);
     - Algoritmo determinístico de identificação de raízes, cabeças, órfãos, forks e ciclos (via detecção de ciclos em grafo direcionado);
     - Ordenação canônica e determinística da tupla `revisions` e de todas as tuplas de identificadores resultantes.
2. **Suíte de Testes:**
   - `tests/test_material_revision_projection.py`: testes unitários exaustivos cobrindo linhagens lineares, permutações de ordem de entrada, órfãos, forks (com predecessor existente e inexistente), múltiplas raízes, ciclos de diferentes tamanhos e ciclos com caudas, mistura de `material_id`, duplicidades de `revision_id`, sequência vazia, tipos não-sequência e propriedades diagnósticas;
   - `tests/test_material_revision_lineage_projection_integration.py`: teste de integração demonstrando a composição `JsonlMaterialRevisionRepository.list_by_material` $\rightarrow$ `project_material_revision_lineage` após restart simulado por nova instância de repositório.

### Explicitamente fora do escopo

Em estrita consonância com os princípios constitucionais do Agent Lab:

1. **`latest revision` / `current revision` / `canonical head`:** A projeção não elege nem assume uma revisão "atual" ou canônica;
2. **Consistência temporal global:** A Projection v1 é estritamente topológica e estrutural. Ficam fora do escopo:
   - Validação global de monotonicidade temporal entre revisões relacionadas;
   - Diagnóstico ou rejeição de `successor.revised_at < predecessor.revised_at` no grafo;
   - Eleição ou desempate de revisão atual com base em timestamp `revised_at`.
   *(Nota: `create_successor_revision` preserva seu próprio contrato temporal na criação em memória; a projeção interpreta a topologia dos fatos persistidos sem auditoria temporal global).*
3. **Resolução automática de fork ou reparo:** A projeção não funde ramos (sem merge), não escolhe um ramo vencedor e não altera arquivos JSONL;
4. **Mutação de Entidades:** Nenhuma instância de `MaterialRevision` ou `MaterialRecord` é modificada;
5. **Aplicação de `CorrectionRequest`:** Nenhuma semântica `CORRECTION_APPLIED` ou aplicação de correções;
6. **Cálculo de `changed_fields` / `diff`:** Não computar ou persistir diffs de atributos entre revisões;
7. **Integração com Evidence / Decision:** `MaterialRevisionLineage` não é conectada a `EvidenceCollection` ou `DecisionRecommendation`;
8. **Reexecução de Regras / LLM:** Nenhuma invocação de motor de regras ou LLM;
9. **I/O, Locking, Banco Relacional ou ERP:** Nenhuma operação de escrita, fsync, concorrência distribuída ou integração externa.

---

## 7. Semântica Formal de Linhagem

Seja $\mathcal{R}$ a sequência finita e não-vazia de instâncias de `MaterialRevision` pertencentes a um mesmo `material_id`.

Para cada revisão $r \in \mathcal{R}$:
- $\text{id}(r) = r.\text{revision_id}$
- $\text{pred}(r) = r.\text{predecessor_revision_id}$

Definem-se os conjuntos projetados:

1. **Raízes (`root_revision_ids`):**
   $$\text{Roots} = \{ \text{id}(r) \mid r \in \mathcal{R} \land \text{pred}(r) = \text{None} \}$$

2. **Órfãos (`orphan_revision_ids`):**
   Revisões cujo predecessor declarado não pertence a $\mathcal{R}$:
   $$\text{Orphans} = \{ \text{id}(r) \mid r \in \mathcal{R} \land \text{pred}(r) \neq \text{None} \land \text{pred}(r) \notin \{ \text{id}(x) \mid x \in \mathcal{R} \} \}$$

3. **Predecessores Bifurcados (`fork_predecessor_ids`):**
   Identificadores de predecessor que são apontados por mais de uma revisão em $\mathcal{R}$, **inclusive quando o predecessor for inexistente na coleção**:
   $$\text{Forks} = \{ p \mid p \in \text{Strings} \land |\{ r \in \mathcal{R} \mid \text{pred}(r) = p \}| > 1 \}$$
   *Exemplo formal:* Se `REV-A` (`pred="REV-X"`) e `REV-B` (`pred="REV-X"`), e `REV-X` inexiste em $\mathcal{R}$, tem-se simultaneamente:
   - `orphan_revision_ids = ("REV-A", "REV-B")`
   - `fork_predecessor_ids = ("REV-X",)`

4. **Cabeças / Folhas (`head_revision_ids`):**
   Revisões de $\mathcal{R}$ cujo $\text{id}(r)$ não é referenciado como predecessor de nenhuma outra revisão em $\mathcal{R}$, excluindo aquelas que participam exclusivamente de ciclos sem saída:
   $$\text{Heads} = \{ \text{id}(r) \mid r \in \mathcal{R} \land \nexists s \in \mathcal{R} .\, \text{pred}(s) = \text{id}(r) \}$$

5. **Ciclos Indiretos (`cycle_revision_ids`):**
   Identificadores de todas as revisões $r \in \mathcal{R}$ que pertencem **efetivamente** a pelo menos um ciclo direcionado no grafo formado pelos pares $(\text{pred}(r), \text{id}(r))$. Nós que apenas conduzem ao ciclo ou que derivam do ciclo como cauda/ramo **não** pertencem ao ciclo e são excluídos de `cycle_revision_ids`.

6. **Regra Canônica de Ordenação:**
   - A tupla `revisions` é ordenada por `r.revision_id` em ordem lexicográfica ascendente;
   - Todos os conjuntos retornados como tuplas (`root_revision_ids`, `head_revision_ids`, `orphan_revision_ids`, `fork_predecessor_ids`, `cycle_revision_ids`) são ordenados de forma ascendente via ordenação lexicográfica padrão (`sorted(..., key=str)`).

---

## 8. Taxonomia de Erros e Validações de Entrada

`project_material_revision_lineage` adota validação defensiva *fail-closed*:

1. **Não-sequência de entrada:** Se o argumento `revisions` não for uma instância de `collections.abc.Sequence` (ex: sets, generators, mappings, inteiros), levanta `TypeError`;
2. **Elementos inválidos:** Se qualquer elemento da sequência não for instância de `MaterialRevision`, levanta `TypeError`;
3. **Sequência vazia:** Se `len(revisions) == 0`, levanta `ValueError` (ausência de fonte para determinar `material_id`);
4. **Mistura de materiais:** Se existirem duas revisões $r_1, r_2 \in \mathcal{R}$ com $r_1.\text{material_id} \neq r_2.\text{material_id}$, levanta `ValueError` acusando a divergência;
5. **Duplicidade de `revision_id`:** Se a coleção de entrada contiver mais de uma instância com o mesmo `revision_id`, levanta `ValueError` (a unicidade na entrada é pré-requisito para análise topológica).

---

## 9. Estratégia TDD Planejada

A implementação seguirá ciclo estrito de micro-TDD em fatias incrementais:

```text
Fatia 1 (RED → GREEN) — Projeção Linear Simples (1 root, 1 head, is_linear=True)
Fatia 2 (RED → GREEN) — Determinismo e Independência da Ordem de Entrada (incluindo revisions)
Fatia 3 (RED → GREEN) — Detecção e Diagnóstico de Predecessor Inexistente (Orphan)
Fatia 4 (RED → GREEN) — Detecção e Diagnóstico de Bifurcações (Forks com e sem predecessor existente)
Fatia 5 (RED → GREEN) — Detecção e Diagnóstico de Múltiplas Raízes (Multiple Roots)
Fatia 6 (RED → GREEN) — Detecção e Isolamento Exato de Ciclos Indiretos (Cycles >= 2 e Ciclos com Cauda)
Fatia 7 (RED → GREEN) — Rejeição Defensiva de Sequência Vazia, Tipos Não-Sequência, Mistura de material_id e Duplicatas
Fatia 8 (RED → GREEN) — Diagnóstico de Múltiplas Heads e Propriedades Auxiliares
Fatia 9 (RED → GREEN) — Integração Ponta a Ponta com JsonlMaterialRevisionRepository após Restart
Regressão Geral       — python -m unittest discover -s tests -v (397 + novos testes)
```

### Detalhamento das Fatias

- **Fatia 1 — Projeção Linear Simples (`tests/test_material_revision_projection.py`):**
  - Projeção de cadeia canônica `REV-1 (root)` $\rightarrow$ `REV-2` $\rightarrow$ `REV-3`;
  - Verificação de `root_revision_ids = ("REV-1",)`, `head_revision_ids = ("REV-3",)`;
  - Verificação de `revisions = (REV-1, REV-2, REV-3)`;
  - Verificação de `is_linear = True`, `has_ambiguities = False`.
- **Fatia 2 — Determinismo Integral e Ordem de Entrada (`tests/test_material_revision_projection.py`):**
  - Fornecer revisões em permutações de ordem física `[REV-3, REV-1, REV-2]` e `[REV-2, REV-3, REV-1]`;
  - Comprovar que `MaterialRevisionLineage` resultante é 100% idêntico em todas as saídas, incluindo a tupla `revisions` ordenada lexicograficamente por `revision_id` (`("REV-1", "REV-2", "REV-3")`).
- **Fatia 3 — Diagnóstico de Órfãos (`tests/test_material_revision_projection.py`):**
  - Projeção contendo `REV-2` com `predecessor_revision_id = "REV-999"` (inexistente);
  - Verificação de `orphan_revision_ids = ("REV-2",)`, `has_orphans = True`, `is_linear = False`.
- **Fatia 4 — Diagnóstico de Forks com Predecessor Existente e Inexistente (`tests/test_material_revision_projection.py`):**
  - Caso 4A: `REV-1 (root)`, `REV-2A (pred=REV-1)` e `REV-2B (pred=REV-1)` $\rightarrow$ `fork_predecessor_ids = ("REV-1",)`, `orphan_revision_ids = ()`;
  - Caso 4B: `REV-A (pred=REV-X)` e `REV-B (pred=REV-X)` com `REV-X` ausente $\rightarrow$ `fork_predecessor_ids = ("REV-X",)`, `orphan_revision_ids = ("REV-A", "REV-B")`.
- **Fatia 5 — Diagnóstico de Múltiplas Raízes (`tests/test_material_revision_projection.py`):**
  - Projeção contendo `REV-1 (root)` e `REV-10 (root)` para o mesmo material;
  - Verificação de `root_revision_ids = ("REV-1", "REV-10")`, `has_multiple_roots = True`.
- **Fatia 6 — Diagnóstico e Isolamento Exato de Ciclos Indiretos (`tests/test_material_revision_projection.py`):**
  - Caso 6A: ciclo puro de tamanho 2 (`REV-A` $\rightarrow$ `REV-B` $\rightarrow$ `REV-A`) $\rightarrow$ `cycle_revision_ids = ("REV-A", "REV-B")`;
  - Caso 6B: ciclo puro de tamanho 3 (`REV-1` $\rightarrow$ `REV-2` $\rightarrow$ `REV-3` $\rightarrow$ `REV-1`) $\rightarrow$ `cycle_revision_ids = ("REV-1", "REV-2", "REV-3")`;
  - Caso 6C (Ciclo com Cauda): ciclo `REV-A` $\leftrightarrow$ `REV-B` e cauda `REV-C` com `predecessor_revision_id = "REV-B"`. Boundary test comprovando que `cycle_revision_ids = ("REV-A", "REV-B")` e que `REV-C` **não** é marcado como participante de ciclo.
- **Fatia 7 — Validações Defensivas de Entrada (`tests/test_material_revision_projection.py`):**
  - Rejeição de sequência vazia `()` levantando `ValueError`;
  - Rejeição de tipos não-sequência (ex: `set`, geradores) levantando `TypeError`;
  - Rejeição de elementos que não sejam `MaterialRevision` levantando `TypeError`;
  - Rejeição de `material_id` misturado levantando `ValueError`;
  - Rejeição de duplicidade de `revision_id` na coleção de entrada levantando `ValueError`.
- **Fatia 8 — Múltiplas Heads e Combinações Complexas (`tests/test_material_revision_projection.py`):**
  - Projeção de grafo complexo contendo simultaneamente fork, orphan e múltiplas heads;
  - Validação de todas as propriedades booleanas e imutabilidade dos atributos retornados.
- **Fatia 9 — Integração pós-Restart (`tests/test_material_revision_lineage_projection_integration.py`):**
  - Persistência de revisões intercaladas em `JsonlMaterialRevisionRepository`;
  - Reinicialização com nova instância de repositório;
  - Recuperação via `list_by_material` e projeção via `project_material_revision_lineage`;
  - Verificação de integridade e equivalência causal.

---

## 10. Critérios de Aceite

- [x] Suíte de 397 testes existentes preservada 100% GREEN;
- [x] Novos testes implementados exclusivamente via `unittest` em Python 3.11;
- [x] Projeção linear simples identificando fielmente raiz, cabeça única e tupla `revisions` canônica;
- [x] Determinismo integral comprovado: qualquer permutação da sequência de entrada produz o mesmo `MaterialRevisionLineage` (incluindo `revisions` ordenada por `revision_id`);
- [x] Detecção e diagnóstico exato de revisões órfãs (`orphan_revision_ids`);
- [x] Detecção e diagnóstico exato de bifurcações (`fork_predecessor_ids`), inclusive quando o predecessor bifurcado for órfão/inexistente;
- [x] Detecção e diagnóstico exato de múltiplas raízes (`root_revision_ids`);
- [x] Detecção e isolamento exato de ciclos indiretos de tamanho $\ge 2$ (`cycle_revision_ids`), sem incluir nós de cauda externos ao ciclo;
- [x] Identificação de múltiplas heads em cenários de fork ou floresta sem eleição arbitrária de uma delas;
- [x] Rejeição fail-closed com `ValueError` para sequência vazia `()`;
- [x] Rejeição fail-closed com `TypeError` para argumentos que não sejam `Sequence` ou contenham itens não-`MaterialRevision`;
- [x] Rejeição fail-closed com `ValueError` para mistura de `material_id`;
- [x] Rejeição fail-closed com `ValueError` para duplicidade de `revision_id` na entrada da projeção;
- [x] Estrutura `MaterialRevisionLineage` estritamente imutável (`frozen=True`, `slots=True`);
- [x] Nenhuma alteração de schema ou semântica no `JsonlMaterialRevisionRepository`;
- [x] Nenhuma operação de escrita, reparo ou I/O executada pela projeção;
- [x] Nenhuma validação temporal global e nenhuma eleição de revisão atual por timestamp;
- [x] Teste de integração comprovando a composição repositório $\rightarrow$ projeção pós-restart.

---

## 11. Riscos e Mitigações

| Risco | Severidade | Mitigação Arquitetural |
| --- | --- | --- |
| Dependência implícita da ordem de append do repositório | Alta | Testes exaustivos de permutação na Fatia 2 e ordenação lexicográfica de `revisions` e de todos os conjuntos resultantes. |
| Eleição acidental de "latest revision" com base em `revised_at` | Alta | Proibição explícita na SPEC e ausência deliberada de campos como `latest_revision` ou `current_revision` no contrato do read-model. |
| Loop infinito na presença de ciclos de linhagem | Alta | Algoritmo formal de busca em profundidade com controle de visitados e pilha de recursão para detecção e isolamento exato de ciclos. |
| Falso positivo de ciclo em nós de cauda | Média | Teste de boundary na Fatia 6 isolando estritamente os nós que participam de ciclos fechados. |
| Supor que a projeção repara o arquivo JSONL | Média | Princípio `Repository != Projection` mantido; a projeção é função pura somente-leitura. |

---

## 12. Impacto Arquitetural

```text
JsonlMaterialRevisionRepository (I/O, append-only, durabilidade)
        ↓
    list_by_material(material_id) -> tuple[MaterialRevision, ...] (ordem física)
        ↓
project_material_revision_lineage(revisions: Sequence[MaterialRevision]) (função pura em memória)
        ↓
MaterialRevisionLineage (read-model imutável com diagnóstico topológico determinístico)
```

Nenhum contrato existente (`MaterialRecord`, `MaterialRevision`, `JsonlMaterialRevisionRepository`, `GovernanceWorkflow`, `AuditEvent`) é modificado.
