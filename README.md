# Agent Lab Pascoal

Laboratório progressivo de engenharia de agentes de IA aplicado à governança de materiais PDM e estruturas BOM.

## Objetivo

Construir, compreender e avaliar agentes capazes de apoiar a governança de materiais sem substituir a decisão do especialista.

O laboratório evolui de soluções simples e auditáveis para componentes probabilísticos somente quando existe uma hipótese mensurável de ganho. A arquitetura atual combina baseline determinístico, contratos estruturados para LLM, fronteiras explícitas de validação, guardrails e revisão humana.

## Princípio de engenharia

> A IA só entra onde demonstrar ganho mensurável sobre uma solução mais simples.

Antes de acrescentar uma LLM, construímos um baseline determinístico. Ele permanece como referência para comparar qualidade, custo, latência e risco das próximas abordagens.

## Arquitetura atual

```text
MaterialRecord
     │
     ├──────────────► Baseline determinístico
     │                  │
     │                  └──► APPROVE / REVIEW / REJECT
     │
     └──────────────► Fronteira LLM
                        │
                        ├──► prompt determinístico
                        ├──► LLMProvider
                        ├──► JSON bruto
                        ├──► validação Pydantic
                        ├──► JSON Schema
                        ├──► guardrail de identidade
                        └──► GovernanceAgentOutput
                                  │
                                  └──► revisão humana
```

A fronteira LLM está implementada de forma independente de fornecedor. O repositório ainda não realiza chamadas reais para OpenAI, Anthropic, Gemini ou outro provider externo.

## Módulos concluídos

### Módulo 0 — Fundação

O Módulo 0 definiu:

1. o problema de governança;
2. as fronteiras de decisão;
3. os contratos de entrada e saída;
4. as métricas iniciais;
5. um conjunto de dados sintético;
6. os primeiros modelos de domínio.

### Módulo 1 — Baseline determinístico

O Módulo 1 implementou:

- leitura tipada dos materiais;
- normalização de textos e abreviações;
- validação de campos obrigatórios;
- análise de unidades, status e atributos técnicos;
- identificação lexical de possíveis duplicidades;
- recomendações `APPROVE`, `REVIEW` e `REJECT`;
- conjunto de desafio separado;
- avaliação de precisão, recall e correspondência exata;
- métrica ponderada de custo dos erros.

O baseline não utiliza LLM. Ele representa a solução auditável que as abordagens probabilísticas deverão superar de forma mensurável.

### Módulo 2 — Saída estruturada e fronteira LLM

O Módulo 2 já possui uma primeira fronteira segura e testável para futuras integrações com LLMs.

Capacidades implementadas:

- modelo `GovernanceAgentOutput` com Pydantic;
- campos obrigatórios e tipados;
- `GovernanceDecision` e `IssueType` reutilizados do domínio;
- `confidence` restrita ao intervalo entre 0 e 1;
- rejeição de propriedades extras com `extra="forbid"`;
- objetos imutáveis com `frozen=True`;
- parsing e validação de JSON bruto;
- exportação do contrato como JSON Schema;
- contrato `LLMProvider` independente de fornecedor;
- `GovernanceLLMService`/fronteira de execução para análise de materiais;
- construção determinística do prompt;
- Fake Provider para testes sem rede;
- rejeição de JSON malformado ou estruturalmente inválido;
- guardrail semântico de identidade do material;
- erro explícito quando o `material_id` retornado diverge do registro analisado;
- preservação dos identificadores `expected` e `received` para auditoria;
- ausência deliberada de correção silenciosa e retry automático nesse guardrail.

O contrato estruturado garante conformidade sintática e estrutural. Ele não comprova veracidade semântica, ausência de alucinação ou qualidade da recomendação.

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

O desenvolvimento segue um fluxo rastreável:

```text
Issue → análise → SPEC → TDD → implementação → Pull Request
      → CI → revisão → merge → release
```

O projeto atualmente possui:

- templates de Issue e Pull Request;
- SPECs versionadas;
- desenvolvimento orientado por testes;
- GitHub Actions em Python 3.11;
- suíte automatizada com **34 testes**;
- proteção da branch `main`;
- status check de CI obrigatório antes do merge;
- política de Versionamento Semântico;
- `CHANGELOG.md` e guia de contribuição;
- revisão humana preservada como fronteira de decisão.

Um PR experimental com falha deliberada também foi utilizado para comprovar que uma CI reprovada bloqueia a integração na `main`.

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
│   └── 04_engineering_workflow.md
├── src/
│   └── agent_lab/
│       ├── baseline.py
│       ├── cli.py
│       ├── data_io.py
│       ├── domain.py
│       ├── duplicates.py
│       ├── llm_provider.py
│       ├── llm_schema.py
│       ├── llm_service.py
│       ├── metrics.py
│       ├── normalization.py
│       ├── rules.py
│       └── validator.py
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

- integração com provider real de LLM;
- benchmark de qualidade entre modelos reais;
- detecção semântica de duplicidades por embeddings ou similaridade vetorial;
- RAG sobre normas, catálogos ou procedimentos;
- Evidence Engine completo;
- tool calling;
- memória persistente;
- orquestração multiagente;
- retry, fallback ou roteamento entre providers;
- observabilidade de produção;
- implantação para clientes;
- aprendizado automático a partir de feedback humano.

Essas capacidades pertencem à esteira evolutiva e devem ser introduzidas em incrementos pequenos, testáveis e mensuráveis.

## Próximas frentes

A evolução planejada inclui:

1. integrar um provider real sem quebrar a abstração `LLMProvider`;
2. medir a LLM contra o baseline determinístico;
3. introduzir detecção semântica de duplicidades;
4. expandir evidências e justificativas auditáveis;
5. testar arquitetura híbrida de regras + similaridade + RAG + LLM;
6. fortalecer decisões `APPROVE`, `REVIEW` e `REJECT` com human-in-the-loop;
7. construir benchmark com ground truth;
8. acompanhar precision, recall, falsos negativos, revisões desnecessárias, custo, latência e risco;
9. evoluir para uma PoC de diagnóstico de qualidade cadastral antes de qualquer promessa de produto industrial.

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

✅ **Módulo 0 concluído:** fundação do domínio e contratos iniciais.

✅ **Módulo 1 concluído:** baseline determinístico, conjunto de desafio e custo ponderado de erros.

✅ **Módulo 2 em estágio funcional inicial:** saída estruturada, JSON Schema, fronteira LLM independente de fornecedor e guardrail de identidade implementados e testados.

🧪 **34 testes automatizados** protegem o comportamento atual.

➡️ **Próxima etapa:** conectar uma LLM real de forma controlada e iniciar comparação mensurável contra o baseline, sem remover a revisão humana.