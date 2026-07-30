# Agent Lab Pascoal

Laboratório progressivo de engenharia de agentes de IA aplicado à governança de materiais PDM e estruturas BOM.

## Objetivo

Construir, compreender e avaliar um agente capaz de apoiar a governança de materiais sem substituir a decisão do especialista.

O projeto começa com regras determinísticas e evolui gradualmente para:

- saídas estruturadas com LLMs;
- ferramentas e roteamento de decisões;
- detecção semântica de duplicidades;
- RAG sobre normas e procedimentos;
- memória e aprendizado a partir de feedback;
- fluxos controlados com LangGraph;
- avaliação, observabilidade e implantação.

## Princípio de engenharia

> A IA só entra onde demonstrar ganho mensurável sobre uma solução mais simples.

Antes de acrescentar um LLM, construiremos um baseline determinístico. Isso permitirá comparar precisão, custo, latência e risco.

## Módulo atual: 0 — Fundação

Nesta etapa definimos:

1. o problema de negócio;
2. as fronteiras de decisão;
3. o contrato de entrada e saída;
4. as métricas;
5. um conjunto de dados sintético;
6. os primeiros modelos de domínio.

Ainda não existe um agente autônomo neste módulo. Isso é intencional: primeiro construímos a ossatura; depois damos movimento a ela.

## Estrutura inicial

```text
agent-lab-pascoal/
├── data/
│   ├── README.md
│   └── synthetic/
│       └── materials.csv
├── docs/
│   ├── 01_problem_definition.md
│   └── 02_learning_roadmap.md
├── src/
│   └── agent_lab/
│       ├── __init__.py
│       ├── domain.py
│       └── metrics.py
├── tests/
│   └── test_domain.py
├── pyproject.toml
└── README.md
```

## Executando os testes

Requer Python 3.11 ou superior.

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

No PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## Segurança dos dados

Este repositório é público. Não devem ser enviados:

- cadastros reais de empresas;
- códigos internos ou informações comerciais;
- documentos proprietários;
- credenciais e chaves de API.

Os dados iniciais são inteiramente sintéticos. Dados reais somente poderão ser utilizados após anonimização e autorização apropriadas.

## Estado do projeto

🧱 **Módulo 0 em construção:** fundação do domínio e desenho experimental.

