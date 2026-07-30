# Módulo 0 — Definição do problema

## 1. Problema de negócio

Cadastros de materiais podem conter descrições incompletas, abreviações inconsistentes, unidades inadequadas, classificações incorretas e registros duplicados. Esses defeitos afetam compras, estoque, planejamento, manutenção, custos e estruturas BOM.

O sistema proposto deve apoiar o especialista identificando problemas, reunindo evidências e recomendando uma ação. Nesta fase, ele não aprova nem altera cadastros automaticamente.

## 2. Primeira fronteira do projeto

Começaremos pelo cadastro mestre de materiais. A análise de estruturas BOM será acrescentada depois que o pipeline de governança de materiais estiver estável e mensurável.

### Incluído inicialmente

- verificação de completude;
- padronização de descrições;
- identificação de atributos ausentes;
- validação de unidade de medida;
- sugestão de família de materiais;
- busca por possíveis duplicidades;
- cálculo de confiança;
- recomendação de aprovação, revisão ou rejeição.

### Fora do escopo inicial

- alteração direta no ERP ou PLM;
- decisão fiscal automática;
- classificação NCM sem evidência normativa;
- exclusão automática de materiais;
- geração automática de ordens de compra;
- uso de dados empresariais confidenciais.

## 3. Usuários e responsabilidades

| Papel | Responsabilidade |
|---|---|
| Solicitante | Informa os dados do material |
| Agente | Analisa, busca evidências e recomenda |
| Especialista PDM | Revisa casos incertos e toma a decisão |
| Gestor de dados | Define regras, indicadores e limites |

## 4. Contrato de entrada

Um registro poderá conter:

| Campo | Tipo | Obrigatório no MVP |
|---|---|---|
| `material_id` | texto | sim |
| `description_short` | texto | sim |
| `long_description` | texto | não |
| `unit` | texto | sim |
| `manufacturer` | texto | não |
| `manufacturer_part_number` | texto | não |
| `material_group` | texto | não |
| `status` | texto | sim |

O sistema deve aceitar registros imperfeitos: os defeitos do dado são justamente o objeto da análise.

## 5. Contrato de saída

Cada avaliação deverá produzir:

- identificador do material;
- descrição padronizada sugerida;
- família sugerida;
- lista estruturada de problemas;
- candidatos a duplicidade;
- evidências utilizadas;
- completude entre 0 e 1;
- confiança entre 0 e 1;
- decisão recomendada: `APPROVE`, `REVIEW` ou `REJECT`.

## 6. Fronteiras de decisão

| Situação | Ação permitida |
|---|---|
| Registro completo e sem alerta | Recomendar aprovação |
| Baixa confiança ou possível duplicidade | Encaminhar para revisão |
| Campo crítico ausente ou regra impeditiva | Recomendar rejeição |
| Classificação fiscal, impacto financeiro ou conflito normativo | Exigir especialista |

Nenhuma recomendação constitui decisão final no MVP.

## 7. Métricas iniciais

### Qualidade do cadastro

- **Completude:** proporção de campos obrigatórios preenchidos.
- **Taxa de duplicidade detectada:** duplicidades conhecidas encontradas pelo sistema.
- **Precisão de duplicidade:** candidatos sugeridos que são duplicidades reais.
- **Cobertura de anomalias:** defeitos conhecidos identificados.

### Qualidade da recomendação

- **Acurácia da decisão:** concordância com o especialista.
- **Taxa de revisão humana:** proporção encaminhada para revisão.
- **Falso aceite:** registro defeituoso recomendado para aprovação.
- **Falsa rejeição:** registro válido recomendado para rejeição.

### Operação

- latência por material;
- custo por análise;
- quantidade de ferramentas chamadas;
- falhas e repetições do fluxo.

O falso aceite terá peso maior que a falsa rejeição, pois um defeito aprovado pode se propagar para processos posteriores.

## 8. Hipótese inicial

Uma arquitetura híbrida — regras determinísticas, busca semântica e LLM — deverá superar cada componente isolado, especialmente em descrições abreviadas e duplicidades sem correspondência textual exata.

Essa hipótese deverá ser testada, não presumida.

