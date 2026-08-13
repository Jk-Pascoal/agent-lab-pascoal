# SPEC 0027 — Integração de evidências estruturadas à fronteira LLM

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0027` |
| Status | `Concluída` |
| Issue relacionada | `#27` — `[FEATURE] Integrar evidências estruturadas à fronteira LLM` |
| Responsável | Jakson Pascoal (`Jk-Pascoal`) |
| Data de criação | `2026-08-13` |
| Última atualização | `2026-08-13` |
| Área | Governança / Evidence Engine / Fronteira LLM |
| Baseline inicial | `53 testes — OK` |
| Baseline final | `59 testes — OK` |
| Pull Request | `#28` — `feat: integra evidencias LLM ao Evidence Engine` |
| CI | `GitHub Actions / Python 3.11 — aprovado` |
| Fechamento | `2026-08-13` |

---

## 1. Contexto

O Agent Lab Pascoal possui uma fronteira de execução LLM independente de provider,
com parsing e validação estruturada de `GovernanceAgentOutput`, além de guardrail
de identidade de `material_id`.

O projeto também possui um Evidence Engine v1 baseado em:

- `EvidenceSource`;
- `GovernanceEvidence`;
- `EvidenceCollection`.

A SPEC 0024 integrou o Evidence Engine ao baseline determinístico, estabelecendo
a transformação:

```text
MaterialRecord
→ GovernanceIssue[]
→ GovernanceEvidence[]
→ EvidenceCollection
```

A fronteira LLM, entretanto, ainda termina em `GovernanceAgentOutput`.

O incremento desta SPEC cria a ponte explícita:

```text
GovernanceAgentOutput
→ GovernanceEvidence[]
→ EvidenceCollection
```

sem criar um Decision Engine e sem transformar a recomendação da LLM em decisão
final de governança.

---

## 2. Problema

Atualmente existem dois caminhos arquiteturais parcialmente separados:

```text
MaterialRecord
→ regras determinísticas
→ GovernanceIssue[]
→ GovernanceEvidence[]
→ EvidenceCollection
```

e:

```text
MaterialRecord
→ fronteira LLM
→ GovernanceAgentOutput
```

Embora `GovernanceAgentOutput` seja estruturalmente validado, suas Issues ainda
não são representadas pelo contrato comum do Evidence Engine.

Isso fragmenta a rastreabilidade por origem e faria um futuro Decision Engine
precisar conhecer detalhes específicos de cada produtor de sinais.

---

## 3. Objetivo

Permitir a transformação explícita e determinística de um
`GovernanceAgentOutput` validado em uma `EvidenceCollection`.

Para cada Issue apropriada da saída LLM, deverá ser possível produzir uma
`GovernanceEvidence` que preserve:

- `material_id`;
- origem LLM;
- `IssueType`;
- observação derivada explicitamente da Issue;
- ordem original e determinística.

A transformação não deverá atribuir autoridade decisória à LLM.

---

## 4. Invariantes

### 4.1 Identidade

Toda evidência produzida a partir de uma saída LLM deverá possuir o mesmo
`material_id` do `GovernanceAgentOutput` de origem.

Formalmente:

```text
∀ e ∈ EvidenceCollection:
e.material_id = GovernanceAgentOutput.material_id
```

A coleção também deverá respeitar:

```text
EvidenceCollection.material_id = GovernanceAgentOutput.material_id
```

### 4.2 Origem

Evidências derivadas da fronteira LLM deverão possuir uma origem controlada e
inequívoca correspondente à LLM.

A implementação deverá reutilizar `EvidenceSource` e estendê-lo somente se a
origem necessária ainda não existir no contrato atual.

### 4.3 Preservação do tipo

Quando uma Issue da saída possuir `IssueType`, esse tipo deverá ser preservado
na evidência correspondente.

### 4.4 Ordem determinística

Para Issues:

```text
[i1, i2, ..., in]
```

a coleção deverá preservar a ordem:

```text
[e1, e2, ..., en]
```

sem ranking, reordenação probabilística ou deduplicação semântica.

### 4.5 Separação entre evidência e decisão

A transformação não poderá converter automaticamente:

```text
GovernanceAgentOutput.decision
```

em decisão final de domínio.

Deve permanecer verdadeiro:

```text
Evidence != Decision
```

e:

```text
LLM recommendation != final governance decision
```

### 4.6 Confidence

`GovernanceAgentOutput.confidence` não deverá ser interpretado nesta camada como
probabilidade calibrada, score de risco ou peso automático da evidência.

---

## 5. Arquitetura proposta

```text
                    MaterialRecord
                          │
               ┌──────────┴──────────┐
               ▼                     ▼
      regras determinísticas     fronteira LLM
               │                     │
               ▼                     ▼
       GovernanceIssue[]     GovernanceAgentOutput
               │                     │
               ▼                     ▼
      GovernanceEvidence[]   GovernanceEvidence[]
               │                     │
               └──────────┬──────────┘
                          ▼
                    Evidence Layer
                          │
                     [futuro]
                          ▼
                   Decision Engine
                          │
                          ▼
                 Human-in-the-Loop
```

A transformação LLM → Evidence Layer deverá ser pequena, explícita, testável e
independente do provider utilizado.

---

## 6. Contrato conceitual da transformação

Entrada:

```text
GovernanceAgentOutput
├── material_id
├── decision
├── confidence
└── issues[]
```

Saída:

```text
EvidenceCollection
├── material_id
└── evidence[]
    └── GovernanceEvidence
        ├── material_id
        ├── source = LLM
        ├── issue_type
        └── observation
```

Mapeamento conceitual:

```text
output.material_id → collection.material_id
output.material_id → evidence.material_id
issue.issue_type   → evidence.issue_type
issue.message      → evidence.observation
LLM                → evidence.source
```

O mapeamento deverá seguir os nomes e contratos efetivamente existentes no
domínio. Caso o modelo atual use outro nome para a descrição da Issue, a
implementação deverá adaptar o mapeamento sem ampliar o escopo.

---

## 7. Comportamentos esperados

### Cenário A — uma Issue

Uma saída LLM contendo uma Issue deverá produzir uma coleção com uma evidência.

### Cenário B — múltiplas Issues

Uma saída contendo N Issues deverá produzir N evidências, preservando ordem e
identidade.

### Cenário C — nenhuma Issue

Uma saída válida sem Issues deverá produzir uma `EvidenceCollection` válida e
vazia para o mesmo `material_id`.

### Cenário D — identidade preservada

Todas as evidências e a coleção deverão manter o identificador da saída validada.

### Cenário E — recomendação da LLM

Os campos `decision` e `confidence` poderão existir na entrada, mas não deverão
alterar o contrato da evidência nem criar decisão final nesta transformação.

---

## 8. TDD

A implementação seguirá RED → GREEN → REFACTOR.

### 8.1 RED

Antes da implementação, adicionar testes que expressem a capacidade ainda
inexistente.

Cobertura mínima:

1. transformação de uma Issue LLM em uma evidência;
2. transformação de múltiplas Issues;
3. saída sem Issues produz coleção vazia;
4. preservação de `material_id`;
5. origem da evidência identificada como LLM;
6. preservação de `IssueType`;
7. preservação da ordem;
8. ausência de decisão automática durante a transformação.

O RED deverá falhar pela ausência da nova capacidade, e não por erro de sintaxe,
fixture inválida ou quebra artificial de código existente.

### 8.2 GREEN

Implementar somente o necessário para satisfazer os testes da SPEC e preservar
toda a suíte anterior.

Baseline anterior obrigatório:

```text
Ran 53 tests
OK
```

Após o incremento:

```text
Ran 59 tests
OK
```

Resultado efetivo do incremento:

- baseline anterior preservado: `53/53`;
- novos testes da integração LLM → Evidence: `6/6`;
- suíte completa final: `59/59`;
- regressões detectadas: `0`;
- GitHub Actions / Python 3.11: aprovado.

### 8.3 REFACTOR

Após GREEN:

- remover duplicação relevante;
- manter nomes orientados ao domínio;
- preservar separação entre fronteira LLM e Evidence Engine;
- não introduzir abstrações sem necessidade comprovada;
- executar novamente a suíte completa.

---

## 9. Escopo

Incluído:

- transformação explícita de `GovernanceAgentOutput` para evidências;
- produção de `EvidenceCollection`;
- origem LLM controlada;
- preservação de identidade;
- preservação de `IssueType`;
- observação estruturada;
- múltiplas evidências;
- coleção vazia quando não houver Issues;
- ordem determinística;
- testes automatizados;
- TDD;
- documentação da integração;
- manutenção da independência de provider.

---

## 10. Fora do escopo

Não serão implementados nesta SPEC:

- Decision Engine;
- alteração automática de `APPROVE / REVIEW / REJECT`;
- combinação automática RULE × LLM;
- resolução automática de conflitos;
- deduplicação semântica;
- score global de risco;
- scoring ou ranking de evidências;
- ponderação automática por origem;
- calibração estatística de `confidence`;
- benchmark contra ground truth;
- provider real;
- chamadas de rede;
- OpenAI, Anthropic ou Gemini SDK;
- embeddings;
- RAG;
- banco vetorial;
- persistência;
- interface gráfica;
- workflow completo human-in-the-loop;
- decisão autônoma de cadastro.

---

## 11. Critérios de aceite

- [x] existe transformação explícita de `GovernanceAgentOutput` em evidências;
- [x] a origem LLM é identificável;
- [x] `material_id` é preservado;
- [x] `IssueType` é preservado quando aplicável;
- [x] observações são derivadas explicitamente das Issues;
- [x] uma Issue produz uma evidência;
- [x] múltiplas Issues produzem múltiplas evidências;
- [x] ausência de Issues produz coleção vazia válida;
- [x] ordem determinística é preservada;
- [x] Evidence permanece separado de `GovernanceDecision`;
- [x] recomendação LLM não se torna decisão final;
- [x] `confidence` não é tratada como probabilidade calibrada;
- [x] implementação permanece independente de provider;
- [x] TDD RED é demonstrável;
- [x] todos os novos testes passam;
- [x] os 53 testes anteriores continuam aprovados;
- [x] GitHub Actions / Python 3.11 permanece aprovado;
- [x] nenhuma chamada real de rede é adicionada;
- [x] nenhuma credencial ou dado proprietário é incluído;
- [x] nenhuma regra PDM/BOM existente é alterada;
- [x] Pull Request referencia Issue #27 e SPEC 0027;
- [x] decisão final de governança permanece humana.

---

## 12. Riscos e limitações

### 12.1 Saída válida não implica verdade semântica

Uma resposta pode respeitar integralmente o schema e ainda conter uma análise
semanticamente incorreta.

```text
estrutura válida != evidência verdadeira
```

### 12.2 Confidence não calibrada

Um valor como:

```text
confidence = 0.95
```

não deverá ser interpretado como 95% de probabilidade real de correção.

### 12.3 Contradição entre fontes

RULE e LLM poderão produzir evidências incompatíveis ou contraditórias.

Esta SPEC preserva as evidências; não resolve o conflito.

### 12.4 Duplicidade

Uma mesma anomalia poderá ser detectada por mais de uma fonte.

Deduplicação semântica pertence a incremento posterior.

### 12.5 Expansão prematura

O maior risco arquitetural é transformar esta ponte em um Decision Engine
disfarçado.

A implementação deverá permanecer limitada à transformação e transporte de
evidências.

---

## 13. Segurança e governança

- nenhum dado empresarial real foi necessário;
- nenhuma credencial foi armazenada;
- nenhuma chamada de rede foi adicionada;
- testes permaneceram determinísticos;
- provider real permaneceu fora do escopo;
- a LLM produz recomendação, não decisão final;
- autoridade final de governança permanece humana.

---

## 14. Evidência de conclusão

A SPEC foi concluída com a seguinte cadeia de evidências:

```text
Issue #27
↓
SPEC 0027
↓
TDD RED
↓
implementação
↓
6/6 testes específicos GREEN
↓
59/59 testes da suíte completa GREEN
↓
Pull Request #28
↓
GitHub Actions / Python 3.11 aprovado
↓
revisão do diff — 3 arquivos no escopo
↓
merge em main
↓
Issue #27 encerrada
```

### 14.1 Resultado final

- Issue: `#27` — concluída;
- Pull Request: `#28` — mergeado em `main`;
- arquivos alterados no PR: `3`;
- baseline antes do incremento: `53 testes — OK`;
- novos testes: `6`;
- baseline final: `59 testes — OK`;
- CI obrigatória: aprovada;
- branch de feature remota: removida após o merge;
- branch de feature local: removida após sincronização;
- `main`: sincronizada com `origin/main`;
- regressões detectadas: `0`.

### 14.2 Invariante de governança preservado

A conclusão desta SPEC não introduziu autoridade decisória autônoma para a LLM.

Permanece válido:

```text
LLM recommendation != final governance decision
Evidence != Decision
```

A decisão final de governança permanece humana.

---

## 15. Próximo incremento provável

Após esta integração, a arquitetura estará preparada para discutir um
**Decision Engine v1** que consuma evidências estruturadas sem acoplar-se aos
produtores individuais.

Esse incremento deverá possuir Issue e SPEC próprias.

A existência do Evidence Layer não autoriza antecipar essa lógica nesta SPEC.
