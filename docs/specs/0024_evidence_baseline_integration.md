# SPEC 0024 — Integração do Evidence Engine ao baseline determinístico

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0024` |
| Status | `Proposta` |
| Issue relacionada | `#24` — `[FEATURE] Integrar Evidence Engine ao baseline determinístico` |
| Responsável | Jakson Pascoal (`Jk-Pascoal`) |
| Data de criação | `2026-08-12` |
| Última atualização | `2026-08-12` |
| Área | Governança / Evidence Engine / Baseline determinístico |

## 1. Contexto

O Agent Lab Pascoal já possui um baseline determinístico de governança PDM/BOM
que analisa um `MaterialRecord`, executa regras explícitas, detecta possíveis
duplicidades e produz um `GovernanceAssessment`.

O fluxo atual é, de forma simplificada:

```text
MaterialRecord
      ↓
run_rules()
      ↓
GovernanceIssue[]
      ↓
find_duplicate_candidates()
      ↓
GovernanceIssue[] consolidado
      ↓
DeterministicGovernanceValidator
      ↓
GovernanceAssessment
      ├── decision
      ├── issues
      └── evidence: tuple[str, ...]
```

A Issue #21 criou o Evidence Engine v1 e estabilizou três contratos:

```text
EvidenceSource
GovernanceEvidence
EvidenceCollection
```

Esses contratos já são imutáveis, independentes de provider e possuem
invariantes explícitas de identidade por `material_id`.

A própria `SPEC-0021` deixou deliberadamente fora de escopo a substituição dos
campos antigos de evidência em `GovernanceAssessment` e
`GovernanceAgentOutput`, registrando que a integração deveria ocorrer em um
incremento posterior.

Esse incremento posterior é a Issue #24.

O baseline confirmado antes da abertura da Issue #24 é:

```text
Ran 46 tests
OK
```

Portanto, o problema atual não é ausência de um contrato de evidência.

O problema é que o contrato existe, mas ainda não participa da cadeia real de
execução do baseline determinístico.

O princípio arquitetural desta SPEC é:

```text
Issue != Evidence
Evidence != Decision
```

Uma `GovernanceIssue` representa um problema detectado.

Uma `GovernanceEvidence` representa uma observação estruturada transportável e
auditável.

Uma `GovernanceDecision` representa uma recomendação de governança.

As três estruturas podem se relacionar, mas não devem ser confundidas.

---

## 2. Problema, evidências e impacto

### Problema

O `DeterministicGovernanceValidator` ainda converte as mensagens de
`GovernanceIssue` diretamente em strings:

```python
evidence=tuple(issue.message for issue in issues)
```

Consequentemente, o `GovernanceAssessment` ainda mantém:

```python
evidence: tuple[str, ...]
```

Esse formato preserva apenas texto.

Ele não preserva explicitamente, em cada evidência:

- o `material_id`;
- a origem lógica;
- o `IssueType`;
- a observação como contrato de domínio.

Ao mesmo tempo, o Evidence Engine v1 já possui exatamente essa capacidade por
meio de:

```text
GovernanceEvidence
├── material_id
├── source
├── issue_type
└── observation
```

e:

```text
EvidenceCollection
├── material_id
└── evidence[]
```

Existe, portanto, uma descontinuidade arquitetural:

```text
mecanismo de detecção
      ↓
GovernanceIssue
      ↓
texto livre
```

enquanto o contrato estruturado permanece lateral:

```text
GovernanceEvidence
      ↓
EvidenceCollection
```

A Issue #24 deve conectar essas duas partes.

### Evidências

Fatos observáveis no estado atual do repositório:

1. `MaterialRecord` possui `material_id`.
2. `GovernanceIssue` possui `issue_type`, `field_name`, `message` e `severity`.
3. `GovernanceAssessment` possui `evidence: tuple[str, ...]`.
4. `DeterministicGovernanceValidator.analyze()` executa `run_rules(record)`.
5. O validator também adiciona uma `GovernanceIssue` de
   `POSSIBLE_DUPLICATE` quando existem candidatos.
6. O validator gera evidência textual por `issue.message`.
7. `EvidenceSource` já possui:
   - `RULE`;
   - `VALIDATION`;
   - `DUPLICATE`;
   - `LLM`.
8. `GovernanceEvidence` já valida:
   - `material_id`;
   - `source`;
   - `issue_type`;
   - `observation`.
9. `EvidenceCollection` já rejeita evidências pertencentes a outro material.
10. `EvidenceCollection` aceita coleção vazia para `material_id` válido.
11. O Evidence Engine já possui suíte própria de testes.
12. O baseline pré-Issue #24 possui `46/46` testes aprovados.
13. O Evidence Engine ainda não é construído pelo
    `DeterministicGovernanceValidator`.
14. Não existe adaptador explícito `GovernanceIssue → GovernanceEvidence`.
15. Não existe uma `EvidenceCollection` associada ao resultado determinístico.

### Impacto

Enquanto a cadeia determinística terminar em `tuple[str, ...]`:

- a proveniência da evidência permanece implícita;
- o `IssueType` precisa ser correlacionado por outra estrutura;
- a identidade do material não acompanha cada evidência individualmente;
- auditoria depende de reconstrução indireta;
- regras e Duplicate Intelligence não possuem uma representação comum de
  evidência;
- futura combinação com evidência LLM exigiria tratamento especial;
- benchmark de qualidade da evidência fica limitado;
- explainability fica acoplada à estrutura de `GovernanceIssue`;
- futuras políticas de interpretação correm risco de consumir texto livre;
- o Evidence Engine continua sendo um contrato isolado, e não parte do sistema.

O impacto arquitetural esperado após a integração é:

```text
regra ou detector
      ↓
GovernanceIssue
      ↓
adaptador explícito
      ↓
GovernanceEvidence
      ↓
EvidenceCollection
      ↓
futura interpretação
      ↓
futura decisão
      ↓
revisão humana
```

A mudança aumenta rastreabilidade.

Ela não garante veracidade da evidência.

---

## 3. Objetivo

Integrar o Evidence Engine v1 ao baseline determinístico sem alterar a lógica
existente de decisão e sem quebrar o contrato legado de evidência textual nesta
Issue.

Ao final do incremento, cada `GovernanceAssessment` produzido pelo
`DeterministicGovernanceValidator` deverá possuir uma coleção estruturada de
evidências derivada das `GovernanceIssue` detectadas durante a análise.

A transformação deverá preservar:

```text
material_id
issue_type
observation
source
ordem
```

O fluxo desejado é:

```text
MaterialRecord
      ↓
GovernanceIssue[]
      ↓
GovernanceEvidence[]
      ↓
EvidenceCollection
      ↓
GovernanceAssessment
      ├── evidence legado
      └── evidence_collection estruturado
```

O contrato legado:

```text
evidence: tuple[str, ...]
```

será preservado temporariamente por compatibilidade.

A nova integração será aditiva.

Uma futura Issue poderá decidir se o campo legado deverá ser removido,
substituído ou depreciado.

Resultado mensurável:

- toda Issue produzida pelo baseline gera uma evidência estruturada;
- um material sem Issues produz uma `EvidenceCollection` vazia;
- a coleção pertence ao mesmo `material_id` do assessment;
- a ordem das Issues é preservada;
- a lógica `APPROVE / REVIEW / REJECT` permanece inalterada;
- os 46 testes anteriores continuam aprovados.

---

## 4. Escopo

### Incluído

- criar um adaptador explícito de `GovernanceIssue` para
  `GovernanceEvidence`;
- criar uma função determinística para formar `EvidenceCollection` a partir de
  Issues;
- preservar `material_id`;
- preservar `IssueType`;
- utilizar `GovernanceIssue.message` como `observation`;
- definir política explícita de `EvidenceSource`;
- preservar ordem das Issues;
- produzir coleção vazia quando nenhuma Issue existir;
- integrar a coleção ao resultado do validator;
- adicionar um campo aditivo de evidência estruturada em
  `GovernanceAssessment`;
- preservar o campo legado `evidence: tuple[str, ...]`;
- manter a decisão atual inalterada;
- manter o cálculo atual de confiança inalterado;
- manter completude e normalização inalteradas;
- manter detecção de duplicidades inalterada;
- criar testes TDD para o adaptador;
- criar testes TDD para a integração no validator;
- criar teste de compatibilidade do campo legado;
- preservar os 46 testes existentes;
- documentar RED, GREEN, regressão, riscos e decisões;
- manter CI obrigatório em Python 3.11.

### Fora do escopo

- remover `GovernanceAssessment.evidence`;
- substituir o contrato legado de evidência textual;
- alterar `GovernanceAgentOutput.evidence`;
- alterar JSON Schema da fronteira LLM;
- integrar evidências estruturadas à LLM;
- alterar `GovernanceDecision`;
- criar Decision Engine;
- criar score de evidência;
- atribuir peso a evidências;
- recalibrar confiança;
- alterar severidade;
- mudar regras PDM/BOM;
- alterar Duplicate Intelligence;
- criar novas regras;
- persistir evidências;
- banco de dados;
- RAG;
- embeddings;
- banco vetorial;
- provider real;
- API key;
- HTTP;
- retry;
- fallback;
- tool calling;
- memória;
- interface gráfica;
- automação de decisão final;
- workflow completo human-in-the-loop.

---

## 5. Responsabilidade humana e limites do agente

O Evidence Engine organiza sinais.

Ele não transforma automaticamente um sinal em verdade de domínio.

Exemplo:

```text
IssueType.SUSPICIOUS_UNIT
```

pode gerar:

```text
GovernanceEvidence(
    source=RULE,
    issue_type=SUSPICIOUS_UNIT,
    observation="Material líquido cadastrado em unidade de peça",
)
```

Isso significa:

```text
a regra observou um sinal
```

Não significa:

```text
o cadastro está definitivamente errado
```

Da mesma forma:

```text
POSSIBLE_DUPLICATE
```

não implica duplicidade confirmada.

Portanto:

```text
evidência estruturada != evidência verdadeira
evidência verdadeira != decisão correta
decisão recomendada != decisão humana final
```

A responsabilidade por aprovar, rejeitar ou alterar registros PDM/BOM continua
humana.

Nenhuma mudança desta Issue deverá permitir gravação automática, aprovação
automática ou rejeição autônoma de cadastro.

---

## 6. Requisitos

### Requisitos funcionais

- `RF-01` — Deve existir transformação explícita de `GovernanceIssue` para
  `GovernanceEvidence`.
- `RF-02` — A transformação deve receber explicitamente o `material_id`.
- `RF-03` — O `material_id` da evidência deve ser igual ao material analisado.
- `RF-04` — O `IssueType` deve ser preservado sem conversão textual.
- `RF-05` — `GovernanceIssue.message` deve originar `observation`.
- `RF-06` — A origem deve ser um `EvidenceSource` válido.
- `RF-07` — Uma Issue de `POSSIBLE_DUPLICATE` deve utilizar
  `EvidenceSource.DUPLICATE`.
- `RF-08` — Issues originadas pelas regras determinísticas atuais devem utilizar
  `EvidenceSource.RULE`.
- `RF-09` — Múltiplas Issues devem produzir múltiplas evidências.
- `RF-10` — A ordem das evidências deve corresponder à ordem das Issues.
- `RF-11` — Ausência de Issues deve produzir `EvidenceCollection` vazia.
- `RF-12` — O `material_id` da coleção deve ser o mesmo do material analisado.
- `RF-13` — O validator deve produzir a coleção estruturada durante `analyze()`.
- `RF-14` — `GovernanceAssessment` deve transportar a coleção estruturada.
- `RF-15` — O campo legado `evidence` deve continuar sendo preenchido como
  antes.
- `RF-16` — A decisão determinística deve permanecer idêntica ao comportamento
  anterior.
- `RF-17` — O cálculo de confiança deve permanecer idêntico.
- `RF-18` — A integração não deve produzir decisão a partir das evidências.
- `RF-19` — O adapter não deve executar chamadas de rede.
- `RF-20` — A coleção não deve aceitar evidência pertencente a outro material,
  reutilizando a invariância já existente no Evidence Engine.

### Requisitos de qualidade

- `RQ-01` — A solução deve ser determinística.
- `RQ-02` — A integração deve ser independente de LLM.
- `RQ-03` — Nenhum SDK externo deve ser adicionado.
- `RQ-04` — Nenhuma credencial deve ser necessária.
- `RQ-05` — Nenhum dado empresarial real deve ser usado em testes.
- `RQ-06` — Os 46 testes anteriores devem permanecer aprovados.
- `RQ-07` — O adaptador deve ser uma função pequena e testável isoladamente.
- `RQ-08` — O incremento não deve duplicar a taxonomia `IssueType`.
- `RQ-09` — O incremento deve reutilizar `EvidenceSource`.
- `RQ-10` — O contrato legado deve permanecer compatível nesta Issue.
- `RQ-11` — A mudança em `GovernanceAssessment` deve ser aditiva.
- `RQ-12` — A nova propriedade deve possuir valor default para evitar quebra de
  construções existentes fora do validator.
- `RQ-13` — Nenhuma regra PDM/BOM deve ser alterada.
- `RQ-14` — O diff deve permanecer limitado aos arquivos previstos.
- `RQ-15` — A decisão final deve permanecer humana.

---

## 7. Proposta técnica

### 7.1 Visão geral

A implementação será dividida em três responsabilidades:

```text
A. geração de Issues
B. transformação Issue → Evidence
C. transporte da EvidenceCollection
```

As regras continuam responsáveis apenas por gerar `GovernanceIssue`.

O novo adaptador será responsável apenas por transformar essas Issues em
evidências estruturadas.

O validator continuará responsável pela orquestração.

### 7.2 Fluxo atual

```text
MaterialRecord
      ↓
run_rules()
      ↓
GovernanceIssue[]
      ↓
duplicate detection
      ↓
GovernanceIssue[]
      ↓
decision
      ↓
GovernanceAssessment
      └── evidence: tuple[str]
```

### 7.3 Fluxo proposto

```text
MaterialRecord
      ↓
run_rules()
      ↓
GovernanceIssue[]
      ↓
duplicate detection
      ↓
GovernanceIssue[] consolidado
      ├─────────────────────┐
      ↓                     ↓
decision              build_evidence_collection()
      ↓                     ↓
confidence            GovernanceEvidence[]
      ↓                     ↓
      └────────────── EvidenceCollection
                            ↓
                  GovernanceAssessment
                  ├── issues
                  ├── evidence legado
                  └── evidence_collection
                            ↓
                     revisão humana
```

### 7.4 Adaptador proposto

Criar em:

```text
src/agent_lab/evidence.py
```

uma função pública com responsabilidade clara.

Nome proposto:

```python
build_evidence_collection(
    material_id: str,
    issues: tuple[GovernanceIssue, ...] | list[GovernanceIssue],
) -> EvidenceCollection
```

A função:

1. recebe o identificador do material;
2. percorre as Issues na ordem recebida;
3. determina a origem da evidência;
4. cria `GovernanceEvidence`;
5. cria `EvidenceCollection`;
6. retorna a coleção.

A função não:

- calcula decisão;
- altera severity;
- modifica Issue;
- normaliza texto;
- consulta rede;
- busca dados adicionais;
- corrige IDs;
- deduplica evidências.

### 7.5 Política de origem

A Issue #21 criou quatro fontes:

```text
RULE
VALIDATION
DUPLICATE
LLM
```

Nesta integração será utilizada a seguinte política mínima:

```text
IssueType.POSSIBLE_DUPLICATE
        ↓
EvidenceSource.DUPLICATE
```

Para as demais `GovernanceIssue` atualmente produzidas por `run_rules()`:

```text
GovernanceIssue
        ↓
EvidenceSource.RULE
```

A fonte `VALIDATION` não será utilizada neste incremento.

Motivo:

o contrato atual de `GovernanceIssue` não preserva explicitamente qual função
de validação originou a Issue depois que todas as listas são consolidadas.

Atribuir `VALIDATION` com granularidade maior agora exigiria inferência ou
ampliação do contrato de proveniência, o que está fora do escopo.

A fonte `LLM` permanece fora desta Issue.

Essa decisão evita inventar proveniência que o sistema ainda não registra.

### 7.6 Transformação de campos

Regra de transformação:

```text
GovernanceIssue.issue_type
        ↓
GovernanceEvidence.issue_type
```

```text
GovernanceIssue.message
        ↓
GovernanceEvidence.observation
```

```text
MaterialRecord.material_id
        ↓
GovernanceEvidence.material_id
        ↓
EvidenceCollection.material_id
```

A `severity` não será copiada.

Motivo:

`GovernanceEvidence` v1 não possui severity e a Issue #24 não deve modificar o
contrato do Evidence Engine v1.

Uma futura evolução poderá avaliar se severidade pertence à evidência, à
interpretação ou à política de decisão.

### 7.7 Integração com GovernanceAssessment

A integração deve ser aditiva.

O contrato legado permanece:

```python
evidence: tuple[str, ...]
```

Adicionar um novo campo conceitual:

```python
evidence_collection: EvidenceCollection | None = None
```

A implementação deverá evitar dependência circular entre:

```text
domain.py
evidence.py
```

porque `evidence.py` já depende de `IssueType` definido em `domain.py`.

Estratégia proposta:

- utilizar anotação adiada / forward reference;
- utilizar `TYPE_CHECKING` quando necessário;
- não importar `evidence.py` em runtime a partir de `domain.py`.

Exemplo conceitual:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .evidence import EvidenceCollection
```

e:

```python
evidence_collection: "EvidenceCollection | None" = None
```

O validator, que já é a camada de orquestração, poderá importar normalmente o
Evidence Engine e construir a coleção.

### 7.8 Compatibilidade

Durante esta Issue, o validator deverá continuar preenchendo:

```python
evidence=tuple(issue.message for issue in issues)
```

e também preencher:

```python
evidence_collection=...
```

Essa duplicação é temporária e deliberada.

Ela cria uma ponte de migração:

```text
legado textual
      +
novo contrato estruturado
```

Uma Issue posterior poderá tratar:

- depreciação do campo legado;
- remoção do campo legado;
- migração de consumidores;
- integração estruturada com a LLM.

### 7.9 Arquivos previstos

#### Alterados

```text
src/agent_lab/evidence.py
```

Finalidade:

- adicionar adaptador Issue → Evidence;
- adicionar construção de `EvidenceCollection`;
- encapsular política de origem.

```text
src/agent_lab/domain.py
```

Finalidade:

- adicionar campo aditivo `evidence_collection` em `GovernanceAssessment`;
- preservar compatibilidade do campo legado.

```text
src/agent_lab/validator.py
```

Finalidade:

- construir coleção estruturada;
- associá-la ao assessment;
- preservar decisão e comportamento existente.

#### Testes

Preferência:

```text
tests/test_evidence.py
```

para testes unitários do adaptador.

E:

```text
tests/test_validator.py
```

para testes de integração do Evidence Engine ao baseline.

Não será criado novo arquivo de testes se os arquivos existentes acomodarem os
cenários com clareza.

#### Documentação

```text
docs/specs/0024_evidence_baseline_integration.md
```

Esta SPEC.

### 7.10 Arquivos que não devem ser alterados

Não são previstas mudanças em:

```text
src/agent_lab/rules.py
src/agent_lab/duplicates.py
src/agent_lab/llm_schema.py
src/agent_lab/llm_service.py
src/agent_lab/llm_provider.py
src/agent_lab/baseline.py
src/agent_lab/metrics.py
.github/workflows/tests.yml
```

Se durante a implementação surgir necessidade real de alterar um desses
arquivos, a razão deverá ser registrada antes do commit.

---

## 8. Estratégia de testes e TDD

### 8.1 Baseline

Evidência registrada antes da implementação:

```text
Ran 46 tests
OK
```

Esse é o piso de regressão da Issue #24.

### 8.2 RED 1 — adaptador inexistente

Primeiro teste proposto:

```text
GovernanceIssue
      ↓
build_evidence_collection()
      ↓
GovernanceEvidence
```

Antes da implementação, o teste deve falhar porque a função ainda não existe.

RED aceitável:

```text
ImportError
```

ou:

```text
cannot import name 'build_evidence_collection'
```

Esse RED demonstra ausência real da capacidade.

### 8.3 GREEN 1 — uma Issue de regra

Implementar somente o necessário para transformar uma Issue comum.

Verificar:

```text
material_id preservado
source == RULE
issue_type preservado
observation == issue.message
```

### 8.4 RED/GREEN 2 — duplicidade

Adicionar cenário:

```text
IssueType.POSSIBLE_DUPLICATE
```

Esperado:

```text
source == EvidenceSource.DUPLICATE
```

O teste impede que Duplicate Intelligence perca sua proveniência lógica.

### 8.5 RED/GREEN 3 — múltiplas Issues

Criar duas ou mais Issues.

Verificar:

- quantidade;
- ordem;
- identidade;
- tipos;
- observações.

A ordem deve permanecer estável.

### 8.6 RED/GREEN 4 — ausência de Issues

Criar:

```text
issues = []
```

Esperado:

```text
EvidenceCollection(
    material_id=<material>,
    evidence=(),
)
```

A ausência de evidência não deve ser representada por `None` dentro do
Evidence Engine.

### 8.7 RED/GREEN 5 — integração no validator

Executar `DeterministicGovernanceValidator.analyze()` para um material que
produza Issue.

Verificar:

```text
assessment.evidence_collection is not None
assessment.evidence_collection.material_id == assessment.material_id
len(assessment.evidence_collection.evidence) > 0
```

### 8.8 GREEN — compatibilidade legada

No mesmo cenário, confirmar:

```text
assessment.evidence
```

continua contendo as mensagens textuais como antes.

Isso prova que a mudança é aditiva.

### 8.9 GREEN — material válido

Para material sem Issues:

```text
decision == APPROVE
issues == ()
evidence == ()
evidence_collection.evidence == ()
```

### 8.10 Regressão

Executar:

```powershell
python -m unittest discover -s tests -p "test_evidence.py" -v
python -m unittest discover -s tests -p "test_validator.py" -v
python -m unittest discover -s tests -p "test_*.py" -v
```

O primeiro critério é:

```text
46 testes anteriores continuam aprovados
```

O número final de testes será registrado após a implementação.

Não antecipar artificialmente a contagem final.

### 8.11 Testes previstos

- `T-01` — uma Issue produz uma evidência estruturada;
- `T-02` — `material_id` é preservado;
- `T-03` — `IssueType` é preservado;
- `T-04` — `message` torna-se `observation`;
- `T-05` — Issue de regra usa `EvidenceSource.RULE`;
- `T-06` — `POSSIBLE_DUPLICATE` usa `EvidenceSource.DUPLICATE`;
- `T-07` — múltiplas Issues preservam ordem;
- `T-08` — ausência de Issues produz coleção vazia;
- `T-09` — validator inclui `EvidenceCollection`;
- `T-10` — material válido recebe coleção vazia;
- `T-11` — campo legado `evidence` permanece compatível;
- `T-12` — decisão permanece igual ao comportamento anterior;
- `T-13` — regressão completa preserva os 46 testes anteriores.

---

## 9. Gates de qualidade

### Antes de implementar

```powershell
git status -sb
python -m unittest discover -s tests -p "test_*.py" -v
```

Baseline esperado:

```text
Ran 46 tests
OK
```

### Durante TDD

Executar testes específicos:

```powershell
python -m unittest discover -s tests -p "test_evidence.py" -v
python -m unittest discover -s tests -p "test_validator.py" -v
```

### Antes do commit

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
git diff --check
git status -sb
git diff --stat
```

### Antes do commit staged

```powershell
git add <arquivos previstos>
git diff --cached --check
git diff --cached --stat
git diff --cached
```

### No Pull Request

Obrigatório:

```text
Testes / Python 3.11
```

deve estar aprovado.

### Critérios mínimos

- TDD RED registrado;
- testes específicos aprovados;
- regressão completa aprovada;
- nenhum erro em `git diff --check`;
- nenhum SDK novo;
- nenhuma chamada de rede;
- nenhuma credencial;
- nenhum dado empresarial real;
- nenhuma regra PDM/BOM alterada;
- compatibilidade do campo legado comprovada;
- Evidence continua separado de Decision;
- limitações registradas;
- revisão humana preservada.

---

## 10. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Transformar integração em refatoração ampla | Média | Alto | Limitar diff aos arquivos previstos |
| Quebrar consumidores do campo legado | Média | Alto | Integração aditiva e teste de compatibilidade |
| Criar dependência circular `domain ↔ evidence` | Média | Alto | Forward reference / `TYPE_CHECKING` |
| Atribuir proveniência inexistente | Média | Médio | Política explícita e mínima de source |
| Confundir Issue com Evidence | Média | Médio | Adaptador explícito e documentação |
| Confundir Evidence com Decision | Média | Alto | Nenhuma lógica de decisão no adapter |
| Duplicar duas representações de evidência | Alta | Baixo | Tratar como ponte temporária de migração |
| Usar `VALIDATION` sem rastreabilidade real | Média | Médio | Não utilizar nesta Issue |
| Perder ordem das Issues | Baixa | Médio | Tuple ordenada + teste |
| Alterar decisão sem intenção | Baixa | Alto | Testes de regressão do validator |
| Tratar evidência estruturada como verdade | Alta | Alto | Documentar limite epistemológico |

### Limitações conhecidas após o incremento

Mesmo após a Issue #24:

- `GovernanceAssessment.evidence` ainda existirá como campo legado;
- `GovernanceAgentOutput.evidence` continuará como `tuple[str, ...]`;
- LLM ainda não produzirá `GovernanceEvidence`;
- `VALIDATION` continuará sem uso específico no baseline;
- não haverá score de evidência;
- não haverá peso;
- não haverá ranking;
- não haverá resolução de conflitos;
- não haverá ground truth de evidência;
- não haverá persistência;
- não haverá Decision Engine;
- não haverá decisão autônoma.

O sistema ganhará estrutura e rastreabilidade.

Não ganhará certeza epistemológica.

---

## 11. Plano de reversão

Caso a integração cause regressão antes do merge:

1. não integrar o Pull Request;
2. corrigir na branch;
3. manter `main` intacta;
4. executar novamente os 46 testes de baseline.

Caso uma regressão seja descoberta depois do merge:

1. reverter o Pull Request;
2. remover o campo aditivo de `GovernanceAssessment`;
3. remover a construção de `EvidenceCollection` no validator;
4. remover o adaptador novo do Evidence Engine;
5. remover os testes associados junto com o revert;
6. executar a suíte completa;
7. confirmar que o comportamento textual legado voltou ao estado anterior.

Não existe migração de banco ou alteração de dado persistido nesta Issue.

A reversão é, portanto, puramente de código.

---

## 12. Versionamento e release

### Impacto SemVer

`MINOR`

Justificativa:

a Issue adiciona uma nova capacidade observável e um novo contrato aditivo ao
resultado determinístico, sem remover o contrato legado.

Não é apenas uma correção interna.

É uma evolução funcional compatível.

### Publicação prevista

- versão planejada: `Unreleased`;
- criação de tag: não;
- criação de GitHub Release: não;
- atualização do `CHANGELOG.md`: avaliar no fechamento conforme política
  vigente.

---

## 13. Critérios de aceite

### Arquitetura

- [ ] existe adaptador explícito `GovernanceIssue → GovernanceEvidence`;
- [ ] `Issue` permanece conceitualmente separado de `Evidence`;
- [ ] `Evidence` permanece separado de `GovernanceDecision`;
- [ ] o Evidence Engine participa do fluxo determinístico real;
- [ ] `EvidenceCollection` é produzida pelo fluxo do validator;
- [ ] a integração é aditiva.

### Identidade e contrato

- [ ] `material_id` é preservado em cada evidência;
- [ ] `material_id` da coleção corresponde ao material analisado;
- [ ] `IssueType` é preservado;
- [ ] `message` origina `observation`;
- [ ] nenhuma correção silenciosa de identidade é criada.

### Proveniência

- [ ] Issues de regra usam `EvidenceSource.RULE`;
- [ ] `POSSIBLE_DUPLICATE` usa `EvidenceSource.DUPLICATE`;
- [ ] `VALIDATION` não é inventado sem proveniência explícita;
- [ ] `LLM` permanece fora deste incremento.

### Comportamento

- [ ] uma Issue produz uma evidência;
- [ ] múltiplas Issues produzem múltiplas evidências;
- [ ] a ordem é preservada;
- [ ] ausência de Issues produz coleção vazia;
- [ ] material válido continua `APPROVE`;
- [ ] material com Issue continua recebendo a mesma decisão anterior;
- [ ] confiança não é recalibrada;
- [ ] regras PDM/BOM não são alteradas;
- [ ] Duplicate Intelligence não é alterada.

### Compatibilidade

- [ ] `GovernanceAssessment.evidence` continua funcionando;
- [ ] existe teste explícito de compatibilidade do campo legado;
- [ ] o novo campo possui default compatível;
- [ ] consumidores existentes não precisam migrar nesta Issue.

### TDD e qualidade

- [x] baseline `46/46` foi registrado;
- [ ] existe RED comprovando ausência do adaptador;
- [ ] existem testes específicos do adaptador;
- [ ] existem testes de integração no validator;
- [ ] os 46 testes anteriores permanecem aprovados;
- [ ] todos os novos testes estão aprovados;
- [ ] `git diff --check` não apresenta erros;
- [ ] GitHub Actions / Python 3.11 está aprovado.

### Governança

- [x] nenhum SDK externo foi adicionado até o baseline;
- [x] nenhuma chamada de rede foi adicionada até o baseline;
- [x] nenhuma credencial foi adicionada até o baseline;
- [x] nenhum dado empresarial real foi utilizado no baseline;
- [ ] riscos e limitações finais estão registrados;
- [x] decisão final permanece humana;
- [ ] Pull Request referencia Issue #24;
- [ ] Pull Request referencia `SPEC-0024`.

---

## 14. Questões em aberto

### 1. Nome final do campo estruturado

Proposta:

```text
evidence_collection
```

Alternativa:

```text
structured_evidence
```

Preferência inicial:

```text
evidence_collection
```

porque o tipo transportado é explicitamente `EvidenceCollection`.

### 2. Local do adaptador

Proposta:

```text
src/agent_lab/evidence.py
```

Motivo:

a transformação produz tipos do Evidence Engine e não deve contaminar
`rules.py`.

### 3. Uso de EvidenceSource.VALIDATION

Decisão inicial:

```text
não utilizar nesta Issue
```

A arquitetura atual não preserva proveniência suficiente para separar de forma
segura `RULE` e `VALIDATION` depois que as Issues são consolidadas.

Uma futura Issue poderá modelar proveniência detalhada.

### 4. Campo legado de strings

Decisão inicial:

```text
preservar nesta Issue
```

A remoção deve ocorrer somente após existir uma estratégia explícita de
migração.

### 5. Integração com GovernanceAgentOutput

Decisão:

```text
fora do escopo
```

A fronteira LLM possui contrato Pydantic e JSON Schema próprios e merece uma
Issue independente.

---

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `2026-08-12` | Criar `SPEC-0024` | Evidence Engine v1 existe, mas permanece lateral ao baseline | Jakson Pascoal |
| `2026-08-12` | Preservar o contrato legado de strings | Evitar mudança incompatível prematura | Jakson Pascoal |
| `2026-08-12` | Fazer integração aditiva | Permitir migração incremental | Jakson Pascoal |
| `2026-08-12` | Usar `RULE` para Issues das regras atuais | Proveniência conhecida e determinística | Jakson Pascoal |
| `2026-08-12` | Usar `DUPLICATE` para `POSSIBLE_DUPLICATE` | Preservar origem lógica do detector | Jakson Pascoal |
| `2026-08-12` | Não usar `VALIDATION` por inferência | Evitar inventar proveniência não registrada | Jakson Pascoal |
| `2026-08-12` | Manter LLM fora do incremento | Fronteira LLM requer evolução contratual separada | Jakson Pascoal |
| `2026-08-12` | Não alterar decisão ou confiança | Evidence Engine deve transportar observações, não decidir | Jakson Pascoal |
| `2026-08-12` | Baseline inicial `46/46` | Evidência de estabilidade pré-implementação | Jakson Pascoal |

---

## 16. Rastreabilidade

### Issue

```text
#24
[FEATURE] Integrar Evidence Engine ao baseline determinístico
```

### SPEC predecessora

```text
SPEC-0021
Evidence Engine v1
```

A `SPEC-0021` criou os contratos.

A `SPEC-0024` conecta esses contratos ao baseline determinístico.

### Dependência conceitual

```text
SPEC-0021
Evidence Engine v1
      ↓
SPEC-0024
Integração com baseline
      ↓
futura integração com LLM
      ↓
futura camada de interpretação
      ↓
futuro Decision Engine
```

### Fluxo de engenharia previsto

```text
Issue #24
   ↓
SPEC-0024
   ↓
branch
   ↓
TDD RED
   ↓
adapter mínimo
   ↓
GREEN específico
   ↓
integração no validator
   ↓
GREEN
   ↓
regressão completa
   ↓
review
   ↓
atualização da SPEC
   ↓
commit
   ↓
push
   ↓
Pull Request
   ↓
GitHub Actions
   ↓
code review
   ↓
merge
   ↓
validação pós-merge
   ↓
RD 2026-08-12
```
