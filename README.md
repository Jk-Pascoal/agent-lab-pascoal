# Agent Lab Pascoal

Laboratório progressivo de engenharia de agentes de IA aplicado à governança de materiais PDM e estruturas BOM.

## Objetivo

Construir, compreender e avaliar agentes capazes de apoiar a governança de materiais sem substituir a decisão do especialista.

O laboratório começa com regras determinísticas e evoluirá gradualmente para:

- saídas estruturadas com LLMs;
- ferramentas, guardrails e roteamento de decisões;
- detecção semântica de duplicidades;
- RAG sobre normas e procedimentos;
- memória e aprendizado a partir de feedback;
- orquestração controlada de agentes;
- avaliação, observabilidade e implantação.

## Princípio de engenharia

> A IA só entra onde demonstrar ganho mensurável sobre uma solução mais simples.

Antes de acrescentar um LLM, construímos um baseline determinístico. Ele servirá como referência para comparar qualidade, custo, latência e risco das próximas abordagens.

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
- métrica ponderada de custo dos erros;
- 17 testes automatizados.

O baseline ainda não utiliza LLM. Ele representa a solução auditável que os próximos módulos deverão superar.

## Resultados do baseline

| Conjunto | Registros | Correspondência exata | Precisão de duplicidade | Recall de duplicidade |
|---|---:|---:|---:|---:|
| Desenvolvimento | 20 | 100% | 100% | 100% |
| Desafio | 10 | 80% | 0% | 0% |

O conjunto de desafio preserva duas limitações conhecidas:

- uma duplicidade semanticamente equivalente não identificada;
- uma revisão desnecessária causada por unidade considerada suspeita.

## Custo ponderado dos erros

A hipótese inicial do laboratório considera:

- falso negativo de duplicidade: peso 5;
- revisão desnecessária: peso 1.

No conjunto de desafio:

```text
Custo = 1 × 5 + 1 × 1 = 6

## Estrutura do Projeto

agent-lab-pascoal/
├── data/
│   ├── README.md
│   └── synthetic/
│       ├── materials.csv
│       └── materials_challenge.csv
├── docs/
│   ├── 01_problem_definition.md
│   ├── 02_learning_roadmap.md
│   └── 03_module_01_baseline.md
├── src/
│   └── agent_lab/
│       ├── __init__.py
│       ├── baseline.py
│       ├── cli.py
│       ├── data_io.py
│       ├── domain.py
│       ├── duplicates.py
│       ├── metrics.py
│       ├── normalization.py
│       ├── rules.py
│       └── validator.py
├── tests/
│   ├── test_baseline.py
│   ├── test_domain.py
│   ├── test_normalization.py
│   └── test_validator.py
├── pyproject.toml
└── README.md