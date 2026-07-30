# Roteiro de aprendizagem

Cada módulo acrescenta uma capacidade ao produto e um conceito ao aprendizado.

| Módulo | Produto construído | Conceitos estudados |
|---|---|---|
| 0. Fundação | Problema, dados, contratos e métricas | Modelagem de domínio, desenho experimental |
| 1. Baseline | Validador determinístico | Python, regras, testes, métricas |
| 2. LLM estruturado | Extração e normalização | Tokens, prompts, temperatura, JSON Schema, Pydantic |
| 3. Ferramentas | Agente seleciona validadores | Tool calling, estado, loop, critérios de parada |
| 4. Duplicidades | Busca semântica de materiais | Embeddings, similaridade, thresholds, avaliação |
| 5. Conhecimento | Consulta normas e procedimentos | RAG, chunking, reranking, groundedness |
| 6. Orquestração | Fluxo com aprovação humana | LangGraph, checkpoints, human-in-the-loop |
| 7. Memória | Reutilização de correções | Memória episódica, semântica e feedback |
| 8. BOM | Governança de estruturas | Grafos, ciclos, impacto e relações pai–filho |
| 9. Produção | Serviço utilizável | FastAPI, Docker, segurança, logs e observabilidade |
| 10. Avançado | Integrações e especialização | MCP, multimodalidade, fine-tuning, multiagentes |

## Método aplicado em todos os módulos

1. Formular uma hipótese.
2. Construir a solução mínima.
3. Criar casos de teste.
4. Medir o resultado.
5. Comparar com o baseline.
6. Registrar limitações.
7. Somente então aumentar a complexidade.

## Critério para adotar uma nova tecnologia

Uma tecnologia entra no projeto quando melhora pelo menos uma dimensão relevante:

- qualidade;
- rastreabilidade;
- velocidade;
- custo;
- segurança;
- manutenção;
- experiência do especialista.

Complexidade sem ganho demonstrado será tratada como dívida técnica, não como evolução.

