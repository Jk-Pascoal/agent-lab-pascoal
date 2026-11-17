# Auditoria das Issues — Agent Lab Pascoal — 2026-11-17

## Escopo e evidências
Reconciliação das 13 Issues abertas, PRs abertas #191/#214/#232, PRs históricas #205/#218/#227/#228/#229/#230/#231, `AGENTS.md`, `docs/PROJECT_COMPASS.md`, `docs/operations/SESSION_HANDOFF.json`, e módulo `src/agent_lab/dimension_candidate_audit.py`. Avaliação de status baseada no estado GitHub lido em 17/11; não equivale a revisão independente, CI nova ou testes locais. O handoff é checkpoint de 15/11, não prova de HEAD em 17/11.

## Taxonomia
- **PARCIAL / GATE**: implementação em PR ainda não integrada; manter Issue aberta, não confundir CI de branch com `main`.
- **PENDENTE**: trabalho técnico ou validação genuinamente ainda não entregue.
- **PLANEJADO / DEPENDÊNCIA**: preservar registro e impedir claim de completude.
- **EXPERIMENTAL**: pesquisa segregada da PoC operacional.

| Issue | Diagnóstico 17/11 | Dependência / próximo critério |
|---|---|---|
| #158 SR-001 | EXPERIMENTAL, aberto | B2 não é prova independente; #191 DRAFT exige GO metodológico. Não alterar T02/GT congelados nem inferir escala 100k. |
| #204 PoC CSV structural | PARCIAL integrado na `main` via #205; closeout aberto | Custódia física R4, durabilidade power-loss R7, aceite/revisão, D-03/D-04, planejamento; sem HITL E2E. |
| #206 contribution verification | PENDENTE DE VERIFICAÇÃO | Distinguir evento elegível de exibição efetiva do calendário; sem retrodatação e sem merges artificiais. |
| #210 jornada CSV UI | PARCIAL / GATE | Implementação em #214 DRAFT, ainda não `main`; aceite #215. |
| #215 revisão UI e segurança | BLOQUEADOR P1 | Teste manual/adversarial real de navegador e sockets, revisão humana e GO documentados; browser smoke automatizado não substitui. |
| #216 descarte de sessões | PENDENTE / PÓS-GATE | Endpoint autenticado, publicação/descarte atômico lógico, 404 e recuperação de capacidade; após #214. |
| #217 timeout de upload | PARCIAL / GATE | Código/teste no #214, CI de branch histórica verde; aguarda #215/merge. |
| #219 mapping CSV multi-ERP | PLANEJADO, NÃO AUTORIZADO | Validar hipótese de redução de fricção com fixture sintética; após fechar jornada local; zero conector ERP real. |
| #220 framing HTTP | PARCIAL / GATE | Regressões em #214; aceite #215 e integração antes de encerrar. |
| #221 CSP nonce | PARCIAL / GATE | Conferir implementação/testes e aceite #215 em #214; não fechar por presunção. |
| #222 builder raw socket | PENDENTE | Helper de teste isolado para CRLF correto, regressão, CI nova; não é falha de produto. |
| #223 browser E2E | PARCIAL / VERIFICAR | Workflow `poc-210-browser-smoke.yml` e script presentes em #214; exigir evidência de execução, screenshots/logs; revisão manual #215 continua. |
| #225 dimensões e duplicidades | PARCIAL / RISCO P1 | Auditoria read-only #230 integrada; #232 DRAFT identifica origem; scorer/ranking ainda podem gerar candidatos de dimensão invertida; política de consumo e recall necessitam HUMAN GO. |

## PRs em aberto
1. #214 DRAFT — jornada local CSV; prioridade comercial de demonstração, bloqueada por #215, não usar merge para calendário.
2. #232 DRAFT — enriquecimento da auditoria dimensional: `EXACT_PART_MANUFACTURER` vs `DESCRIPTION_HEURISTIC`; CI 1267/1267 declarada em 16/11; revisão do diff/JSON consumidor e GO.
3. #191 DRAFT — protocolo experimental de validação B2; não promover sem revisão independente/metodológica humana.

## Histórico e coerência de SPECs
- SNAPSHOTS ANTIGOS NÃO SÃO ESTADO CORRENTE: Compass registra explicitamente divergências históricas de SPEC 0008 proposta e 0010 implementação, bem como o antigo baseline 1194, superado em checkpoints posteriores. Não reescrever histórico.
- `docs/specs/0154_catalog_csv_ingestion_adapter_v1.md` consta como SPEC integrada no Compass; #205 entregou o MVP CSV estrutural.
- #228 tornou o parser dimensional fail-closed para fragmentos malformados; #230 provou risco observável end-to-end por auditoria read-only. Nenhuma das duas equivale a correção de scorer.
- Contrato dominante: `ADAPTER PRESERVA; DOMÍNIO JULGA`, `UNKNOWN != MATCH`, `MATCH != identidade física validada`; FROZEN T02/GT/SR-001/B2 intocados.

## Ordem de execução recomendada após a auditoria
1. **P1 #215/#214**: executar navegador real e casos adversariais documentando resultado efetivo. Inspecionar proteção CSRF, Origin/Host, CSP, downloads, sessão, concorrência e HTTP inválido. Corrigir somente falhas reproduzidas, com testes. Sem humano presente, registrar bloqueio de aceite e não fazer merge.
2. **#232/#225**: revisar compatibilidade JSON e diff da PR #232 e manter separação entre auditoria e veto. Só desenhar integração com política explícita aprovada, cobrindo precisão/recall e falso negativo.
3. **#222**: melhoria de testes CRLF em branch isolada caso o gate de UI esteja dependente de revisão humana.
4. **#216/#219**: sequenciar pós-aceite, privilegiando experiência de especialista e fricção de importação antes de ampliar IA/ERP.
5. **#191/#158**: caminho de pesquisa separado; dados independentes e aprovação metodológica.
6. **D-03/D-04**: preservar `planned_end=2026-10-25` vencido e alvo 20/11 não revalidado; não atribuir novo prazo/percentual sem decisão humana.

## Contadores e verificação de contribuição
- Última CI de `main` *documentada* e lida no handoff: **1265/1265** (15/11), workflow 43739751150. Não afirmar que foi reexecutada hoje.
- CI da PR #232 declarada na PR: **1267/1267** na branch, workflows 43870151664 e 43870151526 (16/11).
- O número **1194** é baseline histórico, não estado de 17/11.
- A criação de branch/PR/commit desta auditoria documenta trabalho de governança real, mas só se deve afirmar “quadradinho verde” após verificar elegibilidade e a exibição no perfil. Não usar merge de PR bloqueada para isso.

## Resultado
Auditoria executada, nenhuma Issue encerrada sem prova de DoD, nenhum benchmark/promessa industrial alterado, nenhuma revisão humana fingida. Próxima sessão: priorizar entrega operacional e aceitação do produto, não nova série de documentos.
