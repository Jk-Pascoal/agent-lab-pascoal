# SPEC 0021 — Evidence Engine v1: evidências estruturadas para governança

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0021` |
| Status | `Aprovada` |
| Issue relacionada | `#21` — `[FEATURE] Evidence Engine v1 — evidências estruturadas para decisões de governança` |
| Responsável | Jakson Pascoal (`Jk-Pascoal`) |
| Data de criação | `2026-08-11` |
| Última atualização | `2026-08-11` |
| Área | Governança / Evidence Engine / Explainability |

## 1. Contexto

O Agent Lab Pascoal já possui contratos estruturados para materiais e saídas de
agentes, regras determinísticas de governança, análise de duplicidades, fronteira
LLM independente de provider, validação estrutural por Pydantic, GitHub Actions e
guardrail de identidade de `material_id`.

O estado anterior à Issue #21 também já utilizava evidências em dois pontos do
domínio:

- `GovernanceAssessment.evidence` representado como `tuple[str, ...]`;
- `GovernanceAgentOutput.evidence` representado como `tuple[str, ...]`.

Esses campos permitem transportar texto, mas não formam um contrato estruturado
capaz de registrar de maneira uniforme:

- a identidade do material;
- a origem da evidência;
- o tipo de problema observado;
- a observação produzida.

A Issue #21 cria uma camada de domínio dedicada para evidências antes da evolução
do sistema para um Decision Engine mais sofisticado.

O princípio arquitetural permanece:

```text
Evidence != Decision
```

A evidência registra o que foi observado. A decisão pertence a uma camada
posterior.

## 2. Problema, evidências e impacto

### Problema

Os sinais produzidos durante uma análise não possuíam uma representação central,
tipada e auditável.

Antes desta implementação, evidências podiam existir como strings ou ser
inferidas indiretamente de `GovernanceIssue`, regras, duplicidades ou da saída
LLM.

Isso dificultava estabelecer uma fronteira clara entre:

```text
observação
↓
evidência estruturada
↓
interpretação
↓
decisão
```

Sem essa separação, existia risco de acoplamento entre a detecção de um sinal e a
decisão final de governança.

### Evidências

Estado observado antes da implementação:

- `MaterialRecord` já identificava inequivocamente o material por `material_id`;
- `IssueType` já fornecia uma taxonomia inicial de problemas;
- `GovernanceAssessment.evidence` utilizava `tuple[str, ...]`;
- `GovernanceAgentOutput.evidence` utilizava `tuple[str, ...]`;
- existia módulo dedicado à detecção de duplicidades;
- existiam regras determinísticas PDM/BOM;
- existia fronteira LLM estruturada;
- existia guardrail garantindo consistência de `material_id` na fronteira LLM;
- não existia um tipo de domínio dedicado a uma evidência;
- não existia coleção de evidências com invariância de identidade.

Baseline confirmado antes do TDD da Issue #21:

```text
Ran 34 tests in 0.035s
OK
```

Resultado final local:

```text
Ran 46 tests in 0.029s
OK
```

### Impacto

Sem uma camada estruturada de evidências:

- decisões futuras seriam mais difíceis de explicar;
- revisão humana perderia rastreabilidade;
- auditoria dependeria de texto livre;
- falsos positivos e falsos negativos seriam mais difíceis de diagnosticar;
- seria difícil medir qualidade da evidência separadamente da qualidade da
  decisão;
- regras, Duplicate Intelligence e LLM poderiam produzir sinais em formatos
  diferentes;
- benchmarks futuros contra ground truth seriam menos informativos;
- o sistema correria risco de transformar uma decisão correta em uma caixa-preta
  cuja cadeia causal não pudesse ser reconstruída.

Em governança PDM/BOM, não basta registrar o resultado. É necessário preservar o
caminho de evidências que sustentou a recomendação.

## 3. Objetivo

Criar a primeira versão do Evidence Engine como uma camada pequena,
determinística e independente de provider capaz de:

1. representar uma evidência individual de forma estruturada;
2. associar toda evidência a um `material_id`;
3. identificar a origem da evidência;
4. reutilizar a taxonomia `IssueType` para classificar o sinal observado;
5. registrar uma observação objetiva;
6. agrupar múltiplas evidências para o mesmo material;
7. rejeitar inconsistências de identidade dentro de uma coleção;
8. permanecer completamente separado de `GovernanceDecision`.

O incremento não calcula `APPROVE`, `REVIEW` ou `REJECT`.

## 4. Escopo

### Incluído

- criar `EvidenceSource`;
- criar `GovernanceEvidence`;
- criar `EvidenceCollection`;
- exigir `material_id` não vazio em evidências;
- exigir `material_id` não vazio em coleções;
- exigir observação não vazia;
- exigir `EvidenceSource` válido em runtime;
- exigir `IssueType` válido em runtime;
- permitir múltiplas evidências;
- preservar ordem de inserção das evidências;
- permitir coleção vazia para material válido;
- garantir que todas as evidências da coleção pertençam ao mesmo `material_id`;
- rejeitar divergência de identidade;
- manter estruturas imutáveis;
- manter o contrato sem campo de decisão;
- criar testes unitários para cenários válidos, inválidos e invariantes;
- documentar resultados de TDD, regressão, riscos e limitações;
- manter o componente independente de LLM e de chamadas de rede.

### Fora do escopo

- substituir nesta Issue os campos `evidence: tuple[str, ...]` existentes em
  `GovernanceAssessment` e `GovernanceAgentOutput`;
- alterar o contrato JSON da fronteira LLM;
- decidir automaticamente `APPROVE`, `REVIEW` ou `REJECT`;
- implementar Decision Engine;
- score de severidade ou risco;
- score probabilístico de confiança;
- calibração;
- ranking ou ponderação de evidências;
- resolução automática de conflito entre evidências;
- persistência em banco;
- embeddings;
- RAG;
- banco vetorial;
- integração com provider real;
- chamadas HTTP;
- interface gráfica;
- workflow completo human-in-the-loop;
- alteração das regras determinísticas PDM/BOM existentes;
- migração de dados;
- geração textual livre de justificativas.

A integração dos novos contratos com `GovernanceAssessment` e
`GovernanceAgentOutput` permanece para incremento posterior, após estabilização
do contrato básico.

## 5. Responsabilidade humana e limites do agente

O Evidence Engine v1 registra sinais observados. Ele não transforma esses sinais
automaticamente em decisão final.

Uma evidência como:

```text
issue_type = SUSPICIOUS_UNIT
```

não implica necessariamente:

```text
decision = REJECT
```

A interpretação dependerá futuramente de regras adicionais, contexto,
criticidade, combinação de evidências e política de governança.

Portanto:

```text
evidência estruturada ≠ evidência verdadeira
evidência verdadeira ≠ decisão automática
```

A decisão final de domínio continua sob responsabilidade humana.

## 6. Requisitos

### Requisitos funcionais

- `RF-01` — Deve existir uma representação estruturada de uma evidência. ✅
- `RF-02` — Toda evidência deve possuir `material_id`. ✅
- `RF-03` — `material_id` vazio deve ser rejeitado. ✅
- `RF-04` — Toda evidência deve possuir uma origem controlada. ✅
- `RF-05` — Toda evidência deve possuir um `IssueType`. ✅
- `RF-06` — Toda evidência deve possuir uma observação não vazia. ✅
- `RF-07` — Deve ser possível representar múltiplas evidências para um material. ✅
- `RF-08` — Uma coleção deve possuir um único `material_id` de referência. ✅
- `RF-09` — Evidência cujo `material_id` divergir do material da coleção deve
  ser rejeitada. ✅
- `RF-10` — A ordem das evidências deve permanecer determinística. ✅
- `RF-11` — O contrato não deve possuir campo de decisão. ✅
- `RF-12` — O componente não deve corrigir silenciosamente identificadores. ✅

### Requisitos de qualidade

- `RQ-01` — O componente deve ser independente de provider LLM. ✅
- `RQ-02` — Nenhuma chamada de rede deve ser necessária. ✅
- `RQ-03` — Nenhum SDK externo novo deve ser adicionado. ✅
- `RQ-04` — As estruturas devem ser imutáveis após criação. ✅
- `RQ-05` — Os testes devem ser determinísticos. ✅
- `RQ-06` — Nenhum dado empresarial real deve ser utilizado. ✅
- `RQ-07` — Nenhuma regra PDM/BOM existente deve ser alterada. ✅
- `RQ-08` — O contrato deve reutilizar `IssueType` em vez de duplicar a
  taxonomia existente. ✅
- `RQ-09` — O incremento deve manter compatibilidade com os testes existentes. ✅
- `RQ-10` — A decisão final deve permanecer humana. ✅

## 7. Implementação técnica

### Visão geral

Foi criado:

```text
src/agent_lab/evidence.py
```

com os contratos:

```text
EvidenceSource
GovernanceEvidence
EvidenceCollection
```

A implementação utiliza apenas biblioteca padrão e tipos de domínio já
existentes.

### EvidenceSource

Fontes implementadas:

```text
RULE
VALIDATION
DUPLICATE
LLM
```

A enumeração representa origem lógica da evidência, não fornecedor.

Não existem valores específicos como `OPENAI`, `ANTHROPIC` ou `GEMINI`.

### GovernanceEvidence

Contrato implementado:

```text
GovernanceEvidence
├── material_id: str
├── source: EvidenceSource
├── issue_type: IssueType
└── observation: str
```

Invariantes implementadas:

```text
material_id != ""
observation != ""
source é EvidenceSource
issue_type é IssueType
objeto é imutável
```

Valores apenas textualmente equivalentes aos enums são rejeitados em runtime.

Exemplo:

```text
source = EvidenceSource.RULE  → aceito
source = "RULE"               → rejeitado
```

### EvidenceCollection

Contrato implementado:

```text
EvidenceCollection
├── material_id: str
└── evidence: tuple[GovernanceEvidence, ...]
```

Invariantes implementadas:

```text
material_id != ""

para toda evidência e:
e.material_id == EvidenceCollection.material_id
```

A coleção:

- aceita múltiplas evidências;
- preserva a ordem;
- pode estar vazia quando o `material_id` da coleção é válido;
- é imutável;
- rejeita evidência pertencente a outro material.

Não existe normalização automática, fuzzy matching ou correção silenciosa de
identificador.

### Fluxo resultante

```text
MaterialRecord
      ↓
Regras / Validações / Duplicate Intelligence / LLM
      ↓
GovernanceEvidence
      ↓
EvidenceCollection
      ↓
futura camada de interpretação
      ↓
futuro Decision Engine
      ↓
revisão humana
```

### Contratos não alterados

Nesta Issue não foram alterados:

- JSON Schema do agente;
- `GovernanceAgentOutput`;
- `GovernanceAssessment`;
- `MaterialRecord`;
- `GovernanceDecision`;
- contratos de provider;
- regras determinísticas PDM/BOM;
- workflows do GitHub Actions.

### Arquivos da implementação

- `src/agent_lab/evidence.py` — contratos e invariantes do Evidence Engine v1;
- `tests/test_evidence.py` — suíte TDD e testes de contrato;
- `docs/specs/0021_evidence_engine_v1.md` — esta especificação.

## 8. Estratégia de testes e TDD

### Baseline

Executado antes da implementação produtiva:

```text
Ran 34 tests in 0.035s
OK
```

### RED 1 — módulo inexistente

O primeiro teste tentou importar:

```text
agent_lab.evidence
```

Resultado:

```text
ModuleNotFoundError: No module named 'agent_lab.evidence'

Ran 1 test
FAILED (errors=1)
```

A implementação mínima criou `EvidenceSource` e `GovernanceEvidence`.

GREEN:

```text
Ran 1 test
OK
```

### RED 2 — `material_id` vazio em evidência

Resultado:

```text
AssertionError: ValueError not raised

Ran 2 tests
FAILED (failures=1)
```

Foi adicionada validação explícita de `material_id`.

GREEN:

```text
Ran 2 tests
OK
```

### RED 3 — observação vazia

Resultado:

```text
AssertionError: ValueError not raised

Ran 3 tests
FAILED (failures=1)
```

Foi adicionada validação explícita de `observation`.

GREEN:

```text
Ran 3 tests
OK
```

### Verificação — imutabilidade de `GovernanceEvidence`

A imutabilidade já existia por `dataclass(frozen=True, slots=True)` e ganhou
teste explícito.

Resultado:

```text
Ran 4 tests
OK
```

### RED 4 — coleção inexistente

O teste tentou importar `EvidenceCollection`.

Resultado:

```text
ImportError: cannot import name 'EvidenceCollection'

Ran 5 tests
FAILED (errors=1)
```

Foi criada a representação mínima da coleção.

GREEN:

```text
Ran 5 tests
OK
```

### RED 5 — evidência pertencente a outro material

Resultado:

```text
AssertionError: ValueError not raised

Ran 6 tests
FAILED (failures=1)
```

Foi adicionada a invariância de identidade entre coleção e evidências.

GREEN:

```text
Ran 6 tests
OK
```

### RED 6 — `material_id` vazio na coleção

Resultado:

```text
AssertionError: ValueError not raised

Ran 7 tests
FAILED (failures=1)
```

Foi adicionada validação explícita da identidade da coleção.

GREEN:

```text
Ran 7 tests
OK
```

### RED 7 — origem não controlada

O teste demonstrou que a anotação Python não impedia uma string comum:

```text
source = "RULE"
```

Resultado:

```text
AssertionError: ValueError not raised

Ran 8 tests
FAILED (failures=1)
```

Foi adicionada validação de runtime com `EvidenceSource`.

GREEN:

```text
Ran 8 tests
OK
```

### RED 8 — `issue_type` não controlado

O teste demonstrou que uma string comum poderia ser aceita:

```text
issue_type = "SUSPICIOUS_UNIT"
```

Resultado:

```text
AssertionError: ValueError not raised

Ran 9 tests
FAILED (failures=1)
```

Foi adicionada validação de runtime com `IssueType`.

GREEN:

```text
Ran 9 tests
OK
```

### Verificações finais do contrato

Foram adicionados testes para:

- coleção vazia com material válido;
- imutabilidade de `EvidenceCollection`;
- ausência de campo `decision` nos contratos de evidência.

Resultado específico final:

```text
Ran 12 tests in 0.001s
OK
```

### Regressão completa

Resultado final:

```text
Ran 46 tests in 0.029s
OK
```

A suíte evoluiu de:

```text
34 testes
```

para:

```text
46 testes
```

sem regressões.

## 9. Gates de qualidade

### Gates locais concluídos

- baseline `34/34`; ✅
- REDs comportamentais registrados; ✅
- GREENs incrementais registrados; ✅
- testes específicos finais `12/12`; ✅
- regressão completa `46/46`; ✅
- `git diff --check` sem saída/erros; ✅
- nenhum SDK novo; ✅
- nenhuma chamada de rede; ✅
- nenhuma credencial; ✅
- nenhum dado empresarial real; ✅
- nenhum provider específico; ✅
- nenhuma regra PDM/BOM alterada; ✅
- nenhum Decision Engine introduzido; ✅
- alteração funcional limitada a `evidence.py` e `test_evidence.py`; ✅

Estado observado antes do commit funcional:

```text
## feature/issue-21-evidence-engine-v1
?? src/agent_lab/evidence.py
?? tests/test_evidence.py
```

Observação:

`git diff --stat` não apresentou os dois arquivos nesse momento porque ambos
ainda estavam `untracked`. A estatística relevante deverá ser verificada após
`git add`, usando `git diff --cached --stat`.

### Gate remoto pendente

No Pull Request ainda será necessário:

- push da branch;
- GitHub Actions executado;
- `Testes / Python 3.11` aprovado;
- required check satisfeito;
- revisão final;
- merge na `main`.

## 10. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Confundir evidência com decisão | Alta | Alto | Manter `GovernanceDecision` fora do novo contrato |
| Transformar v1 em mecanismo de scoring | Média | Alto | Limitar escopo a representação e invariantes |
| Duplicar taxonomia de problemas | Média | Médio | Reutilizar `IssueType` |
| Divergência silenciosa de identidade | Média | Alto | Rejeitar `material_id` incompatível |
| Acoplar origem ao fornecedor LLM | Baixa | Médio | Usar fonte lógica `LLM`, não nome de provider |
| Alterar contratos existentes cedo demais | Média | Alto | Não migrar `evidence: tuple[str, ...]` nesta Issue |
| Evidência estruturalmente válida ser semanticamente incorreta | Alta | Alto | Documentar limite e manter revisão humana |
| Taxonomia atual não representar evidências positivas futuras | Média | Médio | Tratar expansão de taxonomia em Issue própria |

### Limitações restantes

Após esta Issue:

- `GovernanceAssessment.evidence` continua baseado em strings;
- `GovernanceAgentOutput.evidence` continua baseado em strings;
- não há geração automática de evidências a partir das regras existentes;
- não há integração automática com Duplicate Intelligence;
- não há integração automática com LLM;
- não há scoring;
- não há validação de verdade semântica;
- não há Decision Engine;
- não há persistência.

O incremento cria a fundação contratual. A integração permanece deliberadamente
posterior.

## 11. Plano de reversão

Caso a implementação introduza regressão:

1. não realizar merge enquanto os checks estiverem falhando;
2. corrigir na branch da Issue;
3. caso já tenha ocorrido merge, reverter o Pull Request;
4. remover `src/agent_lab/evidence.py`;
5. remover `tests/test_evidence.py`;
6. restaurar eventual alteração adicional estritamente relacionada à Issue;
7. executar a suíte completa;
8. confirmar que contratos LLM e regras PDM/BOM voltaram ao estado anterior.

Como a primeira versão não altera persistência nem contratos existentes, a
reversão possui baixo risco.

## 12. Versionamento e release

### Impacto SemVer

`MINOR`

Justificativa: o incremento adiciona nova capacidade de domínio compatível com
as capacidades existentes, sem remover ou modificar contratos publicados.

### Publicação prevista

- versão planejada: `Unreleased`;
- criação de tag: não;
- criação de GitHub Release: não;
- atualização do `CHANGELOG.md`: conforme política vigente.

## 13. Critérios de aceite

- [x] existe representação estruturada de evidência;
- [x] toda evidência possui `material_id`;
- [x] `material_id` vazio é rejeitado em `GovernanceEvidence`;
- [x] origem da evidência é controlada;
- [x] valor textual não tipado de origem é rejeitado;
- [x] o sinal observado utiliza `IssueType`;
- [x] valor textual não tipado de `issue_type` é rejeitado;
- [x] observação vazia é rejeitada;
- [x] múltiplas evidências podem ser agrupadas;
- [x] coleção vazia é permitida para material válido;
- [x] `material_id` vazio é rejeitado na coleção;
- [x] divergência de identidade dentro da coleção é rejeitada;
- [x] a ordem das evidências é determinística;
- [x] `GovernanceEvidence` é imutável;
- [x] `EvidenceCollection` é imutável;
- [x] Evidence permanece separado de `GovernanceDecision`;
- [x] nenhum score de risco foi introduzido;
- [x] nenhuma decisão automática foi introduzida;
- [x] TDD RED foi documentado;
- [x] testes específicos foram criados;
- [x] testes específicos finais `12/12` aprovados;
- [x] os 34 testes anteriores continuam aprovados;
- [x] a suíte completa `46/46` está aprovada;
- [x] `git diff --check` está aprovado;
- [ ] GitHub Actions / Python 3.11 está aprovado;
- [x] nenhum SDK externo novo foi adicionado;
- [x] nenhuma chamada de rede foi adicionada;
- [x] nenhuma credencial foi adicionada;
- [x] nenhum dado empresarial real foi utilizado;
- [x] nenhuma regra determinística PDM/BOM existente foi alterada;
- [x] riscos e limitações estão documentados;
- [x] a decisão final permanece humana;
- [ ] o Pull Request referencia a Issue #21 e esta SPEC.

## 14. Questões em aberto

1. **Integração com os campos `evidence` existentes**
   - `GovernanceAssessment` e `GovernanceAgentOutput` ainda usam strings;
   - a migração fica fora desta Issue;
   - após estabilizar o contrato, deverá ser avaliada em Issue própria.

2. **Taxonomia de fontes**
   - v1 utiliza `RULE`, `VALIDATION`, `DUPLICATE` e `LLM`;
   - novas fontes só devem ser adicionadas quando existir caso de uso concreto.

3. **Evidências positivas**
   - `IssueType` representa atualmente problemas ou sinais de atenção;
   - fatos positivos poderão exigir uma taxonomia mais ampla no futuro;
   - não ampliar o modelo sem evidência de necessidade.

4. **Serialização**
   - o contrato v1 é interno;
   - JSON Schema ou integração Pydantic deverá ser tratada apenas quando uma
     fronteira externa realmente necessitar desse formato.

5. **Integração automática**
   - regras, Duplicate Intelligence e LLM ainda não produzem automaticamente
     `GovernanceEvidence`;
   - essa ligação deve ser feita em incrementos próprios para preservar
     auditabilidade e TDD.

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `2026-08-11` | Criar Issue #21 para Evidence Engine v1 | Separar observação estruturada de decisão | Jakson Pascoal |
| `2026-08-11` | Manter a v1 sem Decision Engine | Evitar acoplamento e expansão prematura de escopo | Jakson Pascoal |
| `2026-08-11` | Reutilizar `IssueType` inicialmente | Evitar duplicar taxonomia já existente | Jakson Pascoal |
| `2026-08-11` | Não migrar ainda os campos `evidence` existentes | Reduzir blast radius e estabilizar primeiro o contrato | Jakson Pascoal |
| `2026-08-11` | Validar `EvidenceSource` e `IssueType` em runtime | Tipagem estática isolada não garante invariantes em execução | Jakson Pascoal |
| `2026-08-11` | Permitir coleção vazia para material válido | Ausência de evidência pode ser um estado legítimo de uma análise | Jakson Pascoal |
| `2026-08-11` | Manter decisão final humana | Princípio de governança do Agent Lab Pascoal | Jakson Pascoal |
| `2026-08-11` | Encerrar implementação local com `46/46` testes | Regressão completa aprovada antes do PR | Jakson Pascoal |
