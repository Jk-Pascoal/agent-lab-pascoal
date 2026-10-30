# AGENTS.md — Agent Lab Pascoal (ponto de entrada persistente)

Este arquivo é o protocolo de reentrada para assistentes de código, incluindo Codex, Copilot e sessões ChatGPT com acesso ao repositório. **Não é prova de que um novo chat o lerá automaticamente.** No início de um novo chat Agent Lab, o assistente DEVE buscá-lo no GitHub, não inventar a sessão anterior.

## Primeira operação obrigatória em toda nova sessão

1. Ler este arquivo, `docs/operations/SESSION_HANDOFF.json` e `docs/PROJECT_COMPASS.md` **antes** de escolher a atividade. O handoff é snapshot histórico e pode estar desatualizado.
2. Conferir branch `main`, HEAD e GitHub Actions mais recentes (CI), Issue funcional, PRs e deliberações humanas; prevalecem **código/testes atuais em `main` > SPEC implementada > Compass > handoff**. Se houver conflito, não presumir que o snapshot venceu; explicitar e corrigir.
3. Executar ou verificar na CI o comando canônico `python -m unittest discover -s tests -v` (não substituir por pytest).
4. Abrir a Issue funcional prioritária indicada no handoff; **a próxima atividade deve entregar código executável e testes**, ou registrar um bloqueio específico se inviável. Não deixar a sessão se transformar novamente em uma sucessão de atualizações documentais.
5. Trabalhar em branch isolada e PR com escopo; nunca fazer merge com revisão exigida pendente, nem por motivo de calendário de contribuições. Não inventar review independente.
6. Antes de encerrar, atualizar o handoff com o estado **verificado** (sha de `main`, CI, números e links), RD/PMP/Crono e status de contribuição GitHub. Um commit em branch não necessariamente preenche o calendário do perfil.

## Estado no checkpoint 30/10/2026 — confira live amanhã

- `main`: `3aef3d10febc61855186fe31caa26c911948424b`; CI [41126119760](https://github.com/Jk-Pascoal/agent-lab-pascoal/actions/runs/41126119760): **1233/1233 GREEN**.
- PR funcional #205: **MERGED**; MVP CSV sintético estrutural (ingestão → diagnóstico → relatório JSON + manifesto SHA-256 → verificação → triagem CSV). Não é produto industrial.
- Issue #204 segue OPEN para lacunas residuais. R4 prova fallback `UNAVAILABLE`, **não** custódia original; R7 prova recusa de par incompleto e SIGKILL, **não** durabilidade em queda de energia. Nenhuma decisão humana real no MVP: `NOT_RECORDED`. Sem HITL E2E.
- A PR #205 foi integrada sem revisão externa independente; essa exceção está registrada e não pode ser apagada ou simulada.
- D-01/D-02 aprovadas em 27/10; D-03/D-04 pendentes; histórico `report=2026-10-25` vencido e PoC 20/11 sem previsão revalidada.
- Ground Truth/T02 FROZEN, SR-001 e demais testes experimentais são guardrails; não reutilizar indevidamente e não alterar.
- Release `v0.1.0` é baseline histórico, **não** versão comercial certificada.

## Prioridade funcional da próxima sessão — 31/10/2026

Issue [#210](https://github.com/Jk-Pascoal/agent-lab-pascoal/issues/210): **P1, primeira jornada operacional local para especialista de materiais**. Construir o menor fluxo de interação executável com CSV sintético/autorizado → diagnóstico real → inspeção e filtro de problemas → download de relatório validado/manifesto/triagem. A UI pode ser Streamlit se a escolha for justificada, mas evitar dependências desnecessárias. Testar o caminho feliz e falhas. Não abrir provider LLM, RAG, ERP, SSO, banco ou revisão humana persistida neste incremento sem nova deliberação.

**Resultado mínimo exigido:** commit com mudança funcional, testes, evidência CLI/CI e PR vinculada à Issue #210; se não for possível, declarar bloqueio concreto e evidência, não declarar avanço.

## Verificação local automática

```powershell
python scripts/verify_session_handoff.py
python -m unittest discover -s tests -v
```

O teste `tests/test_session_handoff.py` faz parte do runner canônico e rejeita a perda de invariantes críticos no arquivo de passagem de sessão. **O teste valida o contrato, não garante que o estado de amanhã seja idêntico ao snapshot, nem que o ChatGPT lerá automaticamente este repositório.**

Para iniciar outro chat, a frase suficiente é: **“Agent Lab: executar atividade de hoje seguindo AGENTS.md e SESSION_HANDOFF.json no GitHub”**. O assistente deve buscar os documentos e a `main` em vez de pedir para repetir todo o contexto.
