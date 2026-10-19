# Agent Lab — Auditoria factual do cronograma e macrofrentes (19/10/2026)

**Classificação:** AUDIT / READ-ONLY OF PRODUCT / NO REBASELINE / HUMAN DECISION PENDING.  
**Entrada local consultada:** `agent-lab-pascoal-roadmap(20261019-111314).json` (snapshot 18/10) e painel-mestre exportado em 19/10.  
**Estado remoto verificado:** `main` @ `f602bb94a24c30c97bc2397b9d3a830fcc4163f4`, PR #194 MERGED; PR #191 OPEN/DRAFT.  
**Fonte canônica do projeto:** `docs/PROJECT_COMPASS.md`, mais matriz de oito gates de 18/10.  
**Natureza deste registro:** auditoria observacional de inconsistências do cronograma, não autorização de mudança de pesos, datas, percentuais, estados ou baseline.

## Conflitos auditados (snapshot de 18/10)

| Macrofrente / ID | Estado e progresso mostrados | Prazo registrado | Evidência de divergência / ação de reconciliação |
| --- | --- | --- | --- |
| `hitlops` — operacionalização HITL | doing / 0% | 25/09/2026 | Pipeline HITL, identidade, audit trail e persistência já têm entregas históricas; verificar o escopo remanescente da macrofrente antes de recalcular percentuais. |
| `groundtruth` | doing / 0% | 10/10/2026 | Contratos, dataset e evaluator GT já possuem entregas; discriminar entregas parciais e critério formal de conclusão. |
| `import` | plan / 0% | 15/10/2026 | Adapter de entrada CSV v1 já entregue na Issue #154; distinguir ingestão de catálogo CSV do escopo de importação operacional completa. |
| `report` | plan / 0% | 25/10/2026 | Prazo futuro; confirmar fronteira de reporting e suas dependências. |
| `pocdemo` | plan / 0% | 20/11/2026 | Confirmar critérios de aceite, demo E2E, evidência de domínio e dependências anteriores. |
| `sr001scalereconnaissance158` | doing / 0%, weight 0 | 27/09/2026 | Experimental/non-functional, Issue #158 aberta; conservar peso zero e tratar prazo vencido em trilha própria, não no KPI da PoC. |

**Atrasos cronológicos verificáveis:** `hitlops`, `groundtruth`, `import` e `sr001scalereconnaissance158` têm prazo anterior a 19/10 e estado não concluído. Isso NÃO demonstra que nenhum subitem foi entregue. `report` e `pocdemo` ainda não venceram em 19/10. As etapas SaaS/Industrial estão planejadas para dezembro/2026 a abril/2027 e não devem ser falsamente classificadas como vencidas por agregação.

## Governança de conclusão da PoC

1. Congelar a leitura histórica: 1194/1194 produto e 40/40 instrumental legado são referências, não reexecução local de hoje; nenhuma alteração de `src/agent_lab/`, `tests/`, T02 FROZEN, Ground Truth ou KPI.
2. Produzir uma matriz de reconciliação **por entregável e evidência de aceite**, separando `implementado`, `validado`, `integrado`, `demonstrado` e `pendente` antes de atualizar `progress`.
3. Cada macrofrente deve ter definição de pronto, artefato/PR/CI como evidência, escopo residual e dependências; somente após aceite humano recalcular `progress`, `status` e datas sem alterar silenciosamente `weight`.
4. Definir trilha crítica provável para PoC: importação/integração operacional → GT/evaluation → workflow operacional → reporting → demonstração E2E; **trilha proposta, não cronograma aprovado**.
5. Preservar `SR-001` como experimento segregado; G6 contrato físico tipado e G4 UNKNOWN são decisões prévias; G1/G2/G3/G5/G7 restantes e G8 escala independente continuam pendentes. PR #191 permanece DRAFT; nenhuma amostra cega autorizada.
6. P-07 migração/carga 100 mil SKUs exige protocolo próprio de integridade, desempenho e migração, sem inferência a partir da T02 de 40 pares.

## Itens de decisão humana antes de publicar nova versão do Crono

- Aceitar o desdobramento de cada macrofrente em entregas concluídas versus escopo ainda não demonstrado.
- Aceitar critérios de ponderação por entregável, percentuais recalculados apenas por evidências e novos prazos por dependência.
- Decidir se datas vencidas serão tratadas como **baseline histórico** mais previsão revisada separada; nunca apagar desvio para deixar a UI verde.
- Confirmar definição formal de encerramento da **PoC vendável** versus expansão SaaS/industrial e experimentos.

**STOP:** nada nesta auditoria aprova PR #191, autoriza execução B2 fora da T02, modifica a main por push direto ou comprova prontidão industrial.  
**Próxima âncora:** elaborar a matriz detalhada de aceite por macrofrente e subentregável, submeter a decisão humana e, somente então, atualizar o JSON/HTML do cronograma com trilha de alterações auditável.
