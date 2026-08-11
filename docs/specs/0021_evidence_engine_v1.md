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

O estado atual também já utiliza evidências em dois pontos do domínio:

- `GovernanceAssessment.evidence` é representado como `tuple[str, ...]`;
- `GovernanceAgentOutput.evidence` é representado como `tuple[str, ...]`.

Esses campos permitem transportar texto, mas ainda não formam um contrato
estruturado capaz de registrar de maneira uniforme:

- a identidade do material;
- a origem da evidência;
- o tipo de problema observado;
- a observação produzida.

A Issue #21 propõe criar essa camada antes de evoluir o sistema para um Decision
Engine mais sofisticado.

O princípio arquitetural é:

```text
Evidence != Decision
```

A evidência registra o que foi observado. A decisão será responsabilidade de uma
camada posterior.

## 2. Problema, evidências e impacto

### Problema

Os sinais produzidos durante uma análise ainda não possuem uma representação
central, tipada e auditável.

Hoje, evidências podem existir como strings ou ser inferidas indiretamente de
`GovernanceIssue`, regras, duplicidades ou da saída LLM.

Isso dificulta estabelecer uma fronteira clara entre:

```text
observação
↓
evidência estruturada
↓
interpretação
↓
decisão
```

Sem essa separação, existe risco de acoplamento entre a detecção de um sinal e a
decisão final de governança.

### Evidências

Estado observado antes da implementação:

- `MaterialRecord` já identifica inequivocamente o material por `material_id`;
- `IssueType` já fornece uma taxonomia inicial de problemas;
- `GovernanceAssessment.evidence` ainda utiliza `tuple[str, ...]`;
- `GovernanceAgentOutput.evidence` ainda utiliza `tuple[str, ...]`;
- existe módulo dedicado à detecção de duplicidades;
- existem regras determinísticas PDM/BOM;
- existe fronteira LLM estruturada;
- existe guardrail garantindo consistência de `material_id` na fronteira LLM;
- não existe um tipo de domínio dedicado a uma evidência;
- não existe uma coleção de evidências que imponha a invariância de identidade
  entre a análise e cada evidência;
- o último baseline conhecido após a Issue #17 foi de `34/34` testes aprovados,
  devendo o baseline ser confirmado novamente antes do RED desta Issue.

### Impacto

Sem uma camada estruturada de evidências:

- decisões futuras podem ser difíceis de explicar;
- revisão humana perde rastreabilidade;
- auditoria fica dependente de texto livre;
- falsos positivos e falsos negativos ficam mais difíceis de diagnosticar;
- torna-se difícil medir qualidade da evidência separadamente da qualidade da
  decisão;
- regras, Duplicate Intelligence e LLM podem produzir sinais em formatos
  diferentes;
- benchmarks futuros contra ground truth ficam menos informativos;
- o sistema corre risco de transformar uma decisão correta em uma "caixa preta"
  cuja cadeia causal não pode ser reconstruída.

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

O incremento não calculará `APPROVE`, `REVIEW` ou `REJECT`.

## 4. Escopo

### Incluído

- criar um tipo controlado para origem da evidência;
- criar representação imutável de uma evidência;
- exigir `material_id` não vazio;
- exigir observação não vazia;
- associar cada evidência a um `IssueType`;
- criar representação para coleção de múltiplas evidências;
- garantir que todas as evidências da coleção pertençam ao mesmo `material_id`;
- rejeitar divergência de identidade;
- preservar ordem de inserção das evidências;
- criar testes unitários para cenários válidos e inválidos;
- documentar invariantes, riscos e limitações;
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

A integração dos contratos de evidência com `GovernanceAssessment` e
`GovernanceAgentOutput` deverá ocorrer em incremento posterior, depois que o
contrato básico estiver estabilizado.

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

- `RF-01` — Deve existir uma representação estruturada de uma evidência.
- `RF-02` — Toda evidência deve possuir `material_id`.
- `RF-03` — `material_id` vazio deve ser rejeitado.
- `RF-04` — Toda evidência deve possuir uma origem controlada.
- `RF-05` — Toda evidência deve possuir um `IssueType`.
- `RF-06` — Toda evidência deve possuir uma observação não vazia.
- `RF-07` — Deve ser possível representar múltiplas evidências para um material.
- `RF-08` — Uma coleção deve possuir um único `material_id` de referência.
- `RF-09` — Evidência cujo `material_id` divergir do material da coleção deve
  ser rejeitada.
- `RF-10` — A ordem das evidências deve permanecer determinística.
- `RF-11` — O contrato não deve possuir campo de decisão.
- `RF-12` — O componente não deve corrigir silenciosamente identificadores.

### Requisitos de qualidade

- `RQ-01` — O componente deve ser independente de provider LLM.
- `RQ-02` — Nenhuma chamada de rede deve ser necessária.
- `RQ-03` — Nenhum SDK externo novo deve ser adicionado.
- `RQ-04` — As estruturas devem ser imutáveis após criação.
- `RQ-05` — Os testes devem ser determinísticos.
- `RQ-06` — Nenhum dado empresarial real deve ser utilizado.
- `RQ-07` — Nenhuma regra PDM/BOM existente deve ser alterada.
- `RQ-08` — O contrato deve reutilizar `IssueType` em vez de duplicar a
  taxonomia existente.
- `RQ-09` — O incremento deve manter compatibilidade com os testes existentes.
- `RQ-10` — A decisão final deve permanecer humana.

## 7. Proposta técnica

### Visão geral

Criar um módulo de domínio dedicado a evidências:

```text
src/agent_lab/evidence.py
```

A proposta inicial utiliza apenas recursos da biblioteca padrão e os tipos de
domínio já existentes.

O módulo deverá conter conceitualmente:

```text
EvidenceSource
GovernanceEvidence
EvidenceCollection
```

### EvidenceSource

Enumeração inicial de fontes:

```text
RULE
VALIDATION
DUPLICATE
LLM
```

A enumeração representa a origem lógica da evidência, não um fornecedor.

Por isso não serão criados valores como `OPENAI`, `ANTHROPIC` ou `GEMINI`.

### GovernanceEvidence

Contrato conceitual:

```text
GovernanceEvidence
├── material_id: str
├── source: EvidenceSource
├── issue_type: IssueType
└── observation: str
```

Invariantes:

```text
material_id != ""
observation != ""
source é EvidenceSource
issue_type é IssueType
objeto é imutável
```

### EvidenceCollection

Contrato conceitual:

```text
EvidenceCollection
├── material_id: str
└── evidence: tuple[GovernanceEvidence, ...]
```

Invariante principal:

```text
para toda evidência e:

e.material_id == EvidenceCollection.material_id
```

Quando houver divergência:

```text
rejeitar
```

Não haverá normalização automática, fuzzy matching ou correção silenciosa do
identificador.

### Fluxo esperado

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

### Contratos de dados

Nesta Issue serão adicionados contratos internos de domínio.

Não serão alterados:

- JSON Schema do agente;
- `GovernanceAgentOutput`;
- `GovernanceAssessment`;
- `MaterialRecord`;
- `GovernanceDecision`;
- contratos de provider.

Essa decisão reduz o blast radius da primeira versão e permite estabilizar o
modelo antes da integração com outras fronteiras.

### Arquivos previstos

- `src/agent_lab/evidence.py` — tipos e invariantes do Evidence Engine v1;
- `tests/test_evidence.py` — TDD e testes de contrato;
- `docs/specs/0021_evidence_engine_v1.md` — esta especificação.

Arquivos que inicialmente não devem ser alterados:

- `src/agent_lab/llm_schema.py`;
- `src/agent_lab/llm_service.py`;
- `src/agent_lab/llm_provider.py`;
- `src/agent_lab/domain.py`, salvo se surgir necessidade técnica comprovada;
- `src/agent_lab/duplicates.py`;
- regras determinísticas existentes;
- workflows do GitHub Actions.

## 8. Estratégia de testes e TDD

### Baseline

Antes de qualquer teste novo, executar:

```powershell
python -m unittest discover -s tests -v
```

Registrar o número real de testes aprovados.

O último baseline conhecido é `34/34`, mas esse valor deve ser tratado apenas
como referência histórica até nova execução local.

### Vermelho

Criar primeiro `tests/test_evidence.py` importando os contratos que ainda não
existem.

O RED deverá demonstrar a ausência da capacidade de evidência estruturada.

Primeiros comportamentos a especificar:

1. criar evidência válida;
2. rejeitar `material_id` vazio;
3. rejeitar observação vazia;
4. aceitar múltiplas evidências do mesmo material;
5. rejeitar uma evidência pertencente a outro material.

O primeiro teste deve falhar antes da implementação produtiva.

### Verde

Criar a menor implementação em `src/agent_lab/evidence.py` capaz de satisfazer
os testes definidos.

Não integrar ainda o novo contrato aos modelos existentes.

### Refactor

Depois do GREEN:

- remover duplicação estritamente local;
- manter nomes de domínio claros;
- não ampliar o escopo;
- preservar imutabilidade;
- preservar separação entre evidência e decisão.

### Regressão

Executar a suíte completa:

```powershell
python -m unittest discover -s tests -v
```

Todos os testes anteriores e novos devem permanecer aprovados.

### Testes previstos

- `T-01` — evidência válida pode ser criada;
- `T-02` — `material_id` vazio é rejeitado;
- `T-03` — observação vazia é rejeitada;
- `T-04` — origem válida é preservada;
- `T-05` — `IssueType` é preservado;
- `T-06` — objeto de evidência é imutável;
- `T-07` — coleção aceita múltiplas evidências do mesmo material;
- `T-08` — coleção preserva a ordem das evidências;
- `T-09` — coleção rejeita divergência de `material_id`;
- `T-10` — coleção vazia é permitida, desde que o `material_id` seja válido;
- `T-11` — Evidence Engine não introduz `GovernanceDecision`;
- `T-12` — regressão completa do projeto.

## 9. Gates de qualidade

Antes do Pull Request:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios mínimos:

- baseline registrado antes do RED;
- RED observado e registrado;
- GREEN específico registrado;
- suíte completa aprovada;
- `git diff --check` sem erros;
- nenhuma credencial;
- nenhum dado empresarial real;
- nenhuma chamada de rede;
- nenhum SDK externo novo;
- nenhum provider específico;
- nenhuma decisão automática;
- alteração limitada aos arquivos previstos;
- documentação atualizada;
- GitHub Actions / Python 3.11 aprovado antes do merge.

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

- `GovernanceAssessment.evidence` continuará baseado em strings;
- `GovernanceAgentOutput.evidence` continuará baseado em strings;
- não haverá geração automática de evidências a partir das regras existentes;
- não haverá integração automática com Duplicate Intelligence;
- não haverá integração automática com LLM;
- não haverá scoring;
- não haverá validação de verdade semântica;
- não haverá Decision Engine;
- não haverá persistência.

O incremento cria a fundação contratual. A integração será deliberadamente
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
reversão deve possuir baixo risco.

## 12. Versionamento e release

### Impacto SemVer

`MINOR`

Justificativa: o incremento adiciona uma nova capacidade de domínio compatível
com as capacidades existentes, sem remover ou modificar contratos publicados.

### Publicação prevista

- versão planejada: `Unreleased`;
- criação de tag: não;
- criação de GitHub Release: não;
- atualização do `CHANGELOG.md`: conforme política vigente.

## 13. Critérios de aceite

- [ ] existe representação estruturada de evidência;
- [ ] toda evidência possui `material_id`;
- [ ] `material_id` vazio é rejeitado;
- [ ] origem da evidência é controlada;
- [ ] o sinal observado utiliza `IssueType`;
- [ ] observação vazia é rejeitada;
- [ ] múltiplas evidências podem ser agrupadas;
- [ ] divergência de identidade dentro da coleção é rejeitada;
- [ ] a ordem das evidências é determinística;
- [ ] os objetos criados são imutáveis;
- [ ] Evidence permanece separado de `GovernanceDecision`;
- [ ] nenhum score de risco foi introduzido;
- [ ] nenhuma decisão automática foi introduzida;
- [ ] existe TDD RED documentado;
- [ ] testes específicos foram criados;
- [ ] os testes anteriores continuam aprovados;
- [ ] a suíte completa está aprovada;
- [ ] `git diff --check` está aprovado;
- [ ] GitHub Actions / Python 3.11 está aprovado;
- [ ] nenhum SDK externo novo foi adicionado;
- [ ] nenhuma chamada de rede foi adicionada;
- [ ] nenhuma credencial foi adicionada;
- [ ] nenhum dado empresarial real foi utilizado;
- [ ] nenhuma regra determinística PDM/BOM existente foi alterada;
- [ ] riscos e limitações estão documentados;
- [ ] a decisão final permanece humana;
- [ ] o Pull Request referencia a Issue #21 e esta SPEC.

## 14. Questões em aberto

1. **Integração com os campos `evidence` existentes**
   - `GovernanceAssessment` e `GovernanceAgentOutput` ainda usam strings;
   - a migração fica fora desta Issue;
   - após estabilizar o contrato, deverá ser avaliada em Issue própria.

2. **Taxonomia de fontes**
   - v1 propõe `RULE`, `VALIDATION`, `DUPLICATE` e `LLM`;
   - novas fontes só devem ser adicionadas quando existir caso de uso concreto.

3. **Evidências positivas**
   - `IssueType` representa atualmente problemas ou sinais de atenção;
   - fatos positivos poderão exigir uma taxonomia mais ampla no futuro;
   - não ampliar o modelo nesta Issue sem evidência de necessidade.

4. **Serialização**
   - o contrato v1 será interno;
   - JSON Schema ou integração Pydantic deverá ser tratada apenas quando uma
     fronteira externa realmente necessitar desse formato.

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `2026-08-11` | Criar Issue #21 para Evidence Engine v1 | Separar observação estruturada de decisão | Jakson Pascoal |
| `2026-08-11` | Manter a v1 sem Decision Engine | Evitar acoplamento e expansão prematura de escopo | Jakson Pascoal |
| `2026-08-11` | Reutilizar `IssueType` inicialmente | Evitar duplicar taxonomia já existente | Jakson Pascoal |
| `2026-08-11` | Não migrar ainda os campos `evidence` existentes | Reduzir blast radius e estabilizar primeiro o contrato | Jakson Pascoal |
| `2026-08-11` | Manter decisão final humana | Princípio de governança do Agent Lab Pascoal | Jakson Pascoal |
