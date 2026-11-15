# Proposta estratégica — Agent Lab Industrial Intelligence / ERP Diagnostic Agent
**Data da decisão de planejamento:** 2026-11-04  
**Estado:** STRATEGIC ROADMAP / PLANNED / NOT IMPLEMENTED  
**Natureza:** inclusão de direção de produto, sem autorização automática de código, Issue, SPEC, merge, release ou alteração de prazo/KPI.

## 1. Objetivo
Expandir gradualmente o Agent Lab Pascoal, hoje centrado em governança de materiais PDM/BOM, para uma **camada de inteligência diagnóstica sobre processos industriais e ERPs de diferentes fornecedores**. A tese não é criar outro ERP, mas correlacionar dados, hipóteses causais e evidências auditáveis de processos transversais, sugerindo ações sujeitas a validação humana.

A identidade do produto atual, o `docs/PROJECT_COMPASS.md`, as delimitações Domain/Application/Infrastructure, as políticas fail-closed e os dados experimentais congelados permanecem válidos.

## 2. Cinco marcos estratégicos
Os cinco marcos constam na atualização portátil do CRONO em 04/11/2026. Todos: **status=plan, progress=0, weight=0, start/end não aprovados**.

| Marco | Entrega futura pretendida | Condição de entrada |
| --- | --- | --- |
| Industrial Intelligence (visão) | Problemas industriais entre cadastros, estoques, compras, MRP, ativos e manutenção | Direção estratégica aprovada, sem execução |
| Modelo semântico e catálogo de falhas | Entidades, relações, tipos de falha, fontes, proveniência, hipóteses e evidências | Casos priorizados e contrato arquitetural |
| ERP Diagnostic Agent V0 (somente leitura) | PoV sobre CSV sintético/anonimizado: diagnóstico, hipóteses refutáveis, explicações e revisão humana | Núcleo CSV demonstrável, SPEC e HUMAN GO |
| Conectores ERP graduais (somente leitura) | Adapters versionados por export/API autorizadas (p.ex. SAP, Oracle, TOTVS, Dynamics, conforme viabilidade) | PoV e controles de segurança aprovados |
| Piloto e valor econômico | Métricas por tipo de falha, tempo de diagnóstico, erros, perdas evitáveis e ROI com baseline mensurável | Cliente, dados e Ground Truth autorizados; go/no-go |

A tarefa histórica do CRONO `erp` (“Integrações ERP piloto”) permanece inalterada em peso, datas e percentual; os marcos acima não a substituem e não reprogramam a trilha industrial.

## 3. Dependências e prioridades
1. **Prioridade corrente:** produto demonstrável da PoC CSV e gates do incremento da PR #214 (DRAFT/UNMERGED no checkpoint de 04/11); revisão adversarial e aceite independente, sem misturar resultados de branch com a `main`.
2. **Gate arquitetural:** explicitar contratos de dados, escopo, falhas-alvo, proveniência, métricas, fronteiras de domínio e riscos; nenhuma abertura automática de Issue/SPEC.
3. **Primeiro experimento:** caso industrial estreito, somente leitura, dados sintéticos e expectativas pré-registradas; saídas auditáveis e nenhuma correção automática no ERP.
4. **Escala:** conexão com sistemas somente após avaliação de segurança/privacidade, autorização e gestão de permissões.
5. **Negócio:** validar utilidade e economia real, evitando inferir ROI a partir de demonstrações sintéticas.

## 4. Invariantes de governança
- `GovernanceDecision != HumanDecision`; diagnóstico não é ação executada.
- `Hypothesis != Evidence != Verified Root Cause`; a IA não deve inventar causa, fonte ou grau de certeza.
- Sem conexões ERP autorizadas hoje; SAP/Oracle/TOTVS/Dynamics são **alvos possíveis**, não integrações instaladas.
- Sem execução no ERP, escritas automáticas, autonomia de compras/cadastros ou uso de dados empresariais sem autorização específica.
- Preservar SR-001, Issue #158, T02 FROZEN, Ground Truth, histórico, baselines e os gates da PoC.
- Esta decisão **não** corrige atraso, libera marcos, revalida 20/11/2026, altera D-03/D-04, aumenta pesos, cria métricas de produção, nem converte planos em entregas.
- A prontidão industrial e escala para 100 mil SKUs **não estão demonstradas**.

## 5. Definição de valor para primeira prova
O agente poderá receber uma pergunta operacional (ex.: ruptura apesar de cobertura de estoque), identificar dados faltantes, cruzar cadastro e suprimentos, propor hipóteses verificáveis e apresentar evidências e ações recomendadas para especialista humano. Não deve declarar uma causa raiz sem suporte ou alterar transações.

Critérios a aprovar antes da implementação: cenário-alvo, fonte/dicionário dos dados, definição de erro e Ground Truth, precisão por falha, taxa de afirmações sem fonte, taxa de encaminhamento humano, tempo até diagnóstico e custo de revisão. ROI deve ser medido em piloto real autorizado.

## 6. Situação documental
- **Aprovado para constar no roadmap:** SIM, por decisão do usuário em 04/11/2026.
- **Aprovado para implementação:** NÃO.
- **Cronograma e pesos novos:** NÃO aprovados, nulos/zero.
- **Documentação de planejamento:** este arquivo.
- **Código, testes, CI, dataset, baselines, release:** sem modificações nesta proposta.
- **Próxima deliberação humana:** selecionar caso de uso piloto específico e autorizar formalmente seu desenho técnico somente após os gates correntes.

> Planejar a expansão não deve competir com a entrega efetiva do produto atual.
