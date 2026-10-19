# PoC — Matriz de aceite por entregável e caminho crítico (19/10/2026)

**Status:** PROPOSTA DOCUMENTAL PARA REVISÃO HUMANA; NO REBASELINE / NO PRODUCTION CHANGE.  
**Base:** ROADMAP exportado 19/10 (snapshot 18/10), `docs/PROJECT_COMPASS.md`, PR #195 (auditoria integrada) e histórico das Issues citadas.  
**Regra:** evidência de componente implementado não é prova de macrofrente concluída. A matriz não altera percentuais, datas, pesos ou status. Evidência de PR identifica entrega histórica; cobertura/qualidade atual requer inspeção e teste próprios.

## Taxonomia de aceite
- **I = implementado:** código ou contrato existente com referência rastreável.
- **V = validado:** critérios e testes aplicáveis evidenciados, dentro do limite avaliado.
- **G = integrado:** entrega presente em `main`.
- **D = demonstrado:** execução ponta a ponta reproduzível com entradas, saídas e evidências.
- **P = pendente/não comprovado:** não confundir com inexistência absoluta; lacuna de aceite documental.
- Somente declarar macrofrente **DONE** mediante critérios explícitos de aceite. Não derivar % do número de PRs nem preencher % com estimativas.

## Matriz de escopo, aceites e lacunas

| Macro / prazo original | Entregável verificável | Evidência histórica / estado | Lacuna e próximo critério de aceite |
| --- | --- | --- | --- |
| HITL `hitlops` / 25-09 (vencido) | Fila pending, claims, eligibility/runtime, release-aware read path | Issues #77–#145: componentes implementados/integrados conforme Roadmap (I/G históricos) | Contrastar escopo operacional requerido com Active Claim Projection/Policy, ownership/assignment, TTL/SLA; aprovar **escopo mínimo da PoC** versus itens fora de escopo. Fazer demo e regressão E2E da jornada escolhida (D pendente). |
| GT `groundtruth` / 10-10 (vencido) | Contratos/datasets/evaluators/serialização atômica e runner de DecisionRecommendation | #115, #119, #124, #129, #133, #137, #141 (I/G históricos) | Runners Material Rules e Duplicate Pair, persistência/loaders físicos, benchmark com dataset definido: **separar essencial para demo de expansão**; apresentar caso reproduzível, ground truth custodiado e saída medida (D pendente). |
| Import `import` / 15-10 (vencido) | CSV operacional de catálogo | #154: adapter CSV v1 (I/G histórico) | Excel e SQL **não demonstrados**; decisão: CSV satisfaz entrada mínima da PoC? Se sim, reespecificar macro composta sem falsificar entrega Excel/SQL. Testar arquivo inválido, determinismo, lineage/erros e fluxo CSV → diagnóstico (V/D a evidenciar). |
| Diagnóstico / núcleo transversal | Pipeline de diagnóstico e saída estruturada de domínio | #149 e #154 como base operacional (I/G históricos) | Comprovar execução com dataset sintético, entradas versionadas, resultados auditáveis; não chamar isso de relatório executivo pronto. |
| Report `report` / 25-10 (a vencer) | Relatório executivo auditável de problemas/duplicidades/evidências/recomendações | Núcleo #149 fornece insumos, **não comprova artefato final** (P) | Definir schema, campos obrigatórios, proveniência por material, interpretação de incerteza e exportação; teste de geração e replay, exemplo revisado por humano (D). |
| Demo `pocdemo` / 20-11 (meta não revalidada) | Cenário PDM/BOM sintético, ingestão, diagnóstico, avaliação, revisão humana, auditoria e relatório | Componentes parciais presentes; demo vendável E2E não comprovada (P) | Critérios de aceite: fixture sintético congelado, passos reproduzíveis, antes/depois, rastreabilidade de decisão e prova de falha segura; não confundir demo de PoC com SaaS/ERP. |
| SR-001 `sr001scalereconnaissance158` / 27-09 (vencido) | Exploração P-07, B0/B1/B2 pós-hoc, controles experimentais | Issue #158 OPEN, PRs #188/#189/#194; B2 não validada independentemente | Trilha **separada**, weight 0 e KPI 0. G6/G4 e demais gates exigem decisões, amostra nova depende de HUMAN GO. Não é pré-condição automática para demo sintética; 100k SKUs não validado. |

## Caminho crítico *proposto*, não aprovado

1. **Definir MVP da PoC vendável**: CSV mínimo? Human review sem assignment/locking? benchmark obrigatório em qual domínio? Formalizar IN/OUT com aceite humano.
2. **Congelar fixture e caso de uso sintéticos**: registros, rótulos, erros intencionais e evidências; estabelecer hashing, não reutilizar T02.
3. **Exercitar CSV → diagnóstico #149 → avaliação GT #141 onde aplicável → decisão/revisão humana existente**, capturando logs e limites; identificar interfaces de orquestração ausentes sem supor implementação.
4. **Entregar reporting mínimo auditável**: artefato com source row/material_id, observações, regras, evidências, recomendação, decisão humana, limites e métricas sem falsos claims.
5. **Demonstração E2E com checklist de aceite**: reproduzível, falhas documentadas, screenshot/log/output, revisão humana e sign-off. Evitar chamar de prontidão industrial.

**Dependências:** (1) precede mudança formal do Crono; (2) precede demonstração; (3) estabelece dados para (4); (4) precede (5). HITL e GT não precisam expandir indefinidamente se o escopo mínimo for aprovado. SaaS/Industrial e P-07/100k seguem trilhas distintas.

## Decisões exigidas e controle de mudanças

- **D-01 Escopo mínimo:** aprovar ou rejeitar CSV-only para PoC, módulos GT necessários e HITL sem assignment/lock/SLA.
- **D-02 Aceite por entregável:** confrontar testes/CI/PR com requisitos V/G/D e assinar lacunas reais.
- **D-03 Progresso:** escolher pesos **internos** de subentregáveis e fórmula auditável (com denominadores fixados antes do cálculo); só depois atualizar campo progress. Preservar pesos de macrofrentes.
- **D-04 Prazo:** reter `end` como linha-base histórica e criar previsão revisada em campo distinto, com dependências/justificativa; exibir **atraso** e **previsão** simultaneamente, sem apagar alertas.
- **D-05 Closeout PoC:** distinguir prova de conceito demonstrável de v0.1.0 histórica, evolução SaaS/Industrial e SR-001 experimental.

## Próxima sessão operativa
Propor SPEC mínima para o **relatório auditável de diagnóstico**, vinculando sua saída à PoC #149 e entrada CSV #154. Antes de codificar, validar D-01 e um exemplo de output; não alterar a PR #191 nem dados T02.

**Invariantes:** produto 1194/1194 e instrumental legado 40/40 são baselines históricos; não houve reexecução local associada a este documento. Nenhuma alteração em `src/agent_lab/`, `tests/`, GT, T02 FROZEN, métricas, KPI ou cronograma. Não há inferência de readiness para 100 mil SKUs.
