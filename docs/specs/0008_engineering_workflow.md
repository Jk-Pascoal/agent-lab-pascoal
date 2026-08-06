# SPEC-0008 — Workflow de engenharia e versionamento

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0008` |
| Status | `Proposta` |
| Issue relacionada | [#8 — Institucionalizar workflow de engenharia e versionamento](https://github.com/Jk-Pascoal/agent-lab-pascoal/issues/8) |
| Responsável | Jk-Pascoal |
| Data de criação | `2026-08-05` |
| Última atualização | `2026-08-05` |

## 1. Contexto

O Agent Lab Pascoal já utiliza branches, commits, testes automatizados e Pull
Requests para desenvolver o baseline determinístico e o contrato estruturado do
Módulo 2. O projeto, porém, ainda não possui um processo de engenharia formal e
versionado que oriente os próximos incrementos.

Esta SPEC transforma as práticas já experimentadas no laboratório em um
workflow explícito, rastreável e reutilizável.

## 2. Problema, evidências e impacto

### Problema

Não existem no repositório templates de Issue, SPEC e Pull Request, política de
versionamento, CHANGELOG inicial nem critérios uniformes para contribuição,
revisão e merge.

Sem essa estrutura, decisões podem ficar somente na conversa ou na memória de
quem implementou a mudança, reduzindo rastreabilidade, repetibilidade e
capacidade de auditoria.

### Evidências

- os incrementos anteriores usaram testes, branches e Pull Requests;
- não há formulário padronizado para descrever features e bugs;
- não há modelo reutilizável de SPEC;
- não há template de Pull Request com validações, riscos e limitações;
- não há política documentada de SemVer e releases;
- não há `CHANGELOG.md` no repositório.

### Impacto

A ausência de um workflow uniforme aumenta o risco de:

- implementação sem problema e critérios de aceite claramente definidos;
- mudanças funcionais sem testes ou sem avaliação de regressão;
- perda do vínculo entre necessidade, decisão técnica e código;
- confusão entre commit, tag, versão e GitHub Release;
- automação de decisões de domínio sem explicitar a responsabilidade humana.

## 3. Objetivo

Institucionalizar um fluxo de engenharia rastreável para que os próximos
incrementos sigam o ciclo:

```text
Issue → análise → SPEC → TDD → implementação → Pull Request
      → CI → revisão → merge → release
```

Ao final, o repositório deve oferecer modelos e documentos suficientes para que
uma nova mudança seja especificada, testada, revisada, incorporada e preparada
para versionamento de maneira consistente.

## 4. Escopo

### Incluído

- formulário de Issue para feature;
- formulário de Issue para bug;
- template de Pull Request;
- template reutilizável e versionado de SPEC;
- documentação do workflow de engenharia;
- critérios de contribuição, revisão e merge;
- política de versionamento semântico e releases;
- `CHANGELOG.md` inicial;
- registro explícito da responsabilidade humana nas decisões de domínio.

### Fora do escopo

- criar workflow de GitHub Actions, que será tratado em Issue própria;
- configurar proteção da branch `main`;
- criar tags ou GitHub Releases neste incremento;
- integrar uma LLM real;
- alterar regras de governança PDM/BOM;
- alterar comportamento funcional do baseline ou do Módulo 2.

## 5. Responsabilidade humana e limites do agente

O Agent Lab Pascoal pode validar dados, apontar problemas, apresentar evidências
e recomendar `APPROVE`, `REVIEW` ou `REJECT`. Essas saídas permanecem
recomendações auditáveis.

A decisão final sobre aprovação, rejeição, alteração de cadastro, exceções de
governança ou impacto em PDM/BOM pertence ao especialista humano responsável.
Nenhum template ou fluxo criado nesta Issue autoriza a promoção automática de
uma recomendação do agente para decisão final de negócio.

## 6. Requisitos

### Requisitos funcionais

- `RF-01` — novas Issues de feature devem solicitar problema, evidências,
  impacto, escopo e critérios de aceite;
- `RF-02` — novas Issues de bug devem solicitar comportamento observado,
  comportamento esperado, evidências, impacto, reprodução, escopo e critérios
  de aceite;
- `RF-03` — Pull Requests devem solicitar vínculos com Issue e SPEC, resumo das
  mudanças, validações executadas, riscos e limitações;
- `RF-04` — deve existir um template reutilizável para futuras SPECs;
- `RF-05` — o workflow deve documentar análise, SPEC, TDD, implementação,
  revisão, merge e preparação de release;
- `RF-06` — os critérios de contribuição e merge devem ser explícitos;
- `RF-07` — a política deve distinguir commit, tag e GitHub Release;
- `RF-08` — o versionamento deve seguir `MAJOR.MINOR.PATCH`;
- `RF-09` — deve existir um `CHANGELOG.md` inicial com seção `Unreleased`.

### Requisitos de qualidade

- `RQ-01` — todos os documentos devem ser legíveis em Markdown no GitHub;
- `RQ-02` — os templates devem ser objetivos e reutilizáveis;
- `RQ-03` — o processo deve manter rastreabilidade entre Issue, SPEC, branch,
  commit e Pull Request;
- `RQ-04` — nenhum arquivo de código funcional deve ser alterado;
- `RQ-05` — os 24 testes existentes devem permanecer aprovados;
- `RQ-06` — nenhuma credencial, chave de API ou dado real deve ser incluído;
- `RQ-07` — responsabilidade humana, riscos e limitações devem permanecer
  visíveis no processo.

## 7. Proposta técnica

### Fluxo de trabalho

1. **Issue:** registra problema, evidências, impacto, escopo e aceite.
2. **Análise:** confirma a necessidade, os limites e as dependências.
3. **SPEC:** documenta decisão técnica, testes, riscos e versionamento.
4. **Branch:** isola o incremento a partir da `main` atualizada.
5. **TDD:** começa pelo teste ou verificação que representa o comportamento.
6. **Implementação:** realiza a menor mudança necessária para atender à SPEC.
7. **Pull Request:** reúne vínculos, diff, validações, riscos e limitações.
8. **CI:** executa automaticamente os gates quando o workflow existir.
9. **Revisão:** verifica escopo, qualidade, segurança e responsabilidade humana.
10. **Merge:** incorpora a mudança somente após os critérios serem atendidos.
11. **Release:** agrupa mudanças aprovadas em uma versão comunicável.

### Rastreabilidade mínima

```text
Issue #N
  └── docs/specs/NNNN_nome.md
        └── branch de trabalho
              └── commits pequenos e intencionais
                    └── Pull Request
                          └── merge na main
                                └── changelog/tag/release quando aplicável
```

### Arquivos previstos

- `.github/ISSUE_TEMPLATE/feature.yml` — formulário para novas funcionalidades;
- `.github/ISSUE_TEMPLATE/bug.yml` — formulário para defeitos;
- `.github/PULL_REQUEST_TEMPLATE.md` — checklist obrigatório do Pull Request;
- `docs/specs/SPEC_TEMPLATE.md` — modelo reutilizável de especificação;
- `docs/specs/0008_engineering_workflow.md` — esta decisão específica;
- `docs/04_engineering_workflow.md` — explicação operacional do fluxo;
- `CONTRIBUTING.md` — contribuição, revisão e critérios de merge;
- `VERSIONING.md` — SemVer, tags e releases;
- `CHANGELOG.md` — histórico inicial de mudanças relevantes.

## 8. Estratégia de testes e TDD

Esta Issue altera governança e documentação, não o comportamento do agente. O
ciclo TDD é preservado da seguinte forma:

### Vermelho

O estado inicial não satisfaz os critérios da Issue: os templates e documentos
não existem. A lista de aceite funciona como verificação inicialmente
reprovada.

### Verde

Criar somente os templates e documentos previstos, preenchendo cada requisito
da Issue sem alterar código funcional.

### Regressão

Executar a suíte completa para demonstrar que a institucionalização do processo
não modificou o baseline nem o Módulo 2.

```powershell
python -m unittest discover -s tests -v
```

Resultado esperado: `Ran 24 tests` e `OK`.

## 9. Gates de qualidade

Antes do Pull Request:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

O incremento somente poderá ser incorporado quando:

- os 24 testes estiverem aprovados;
- `git diff --check` não apresentar erros;
- o diff estiver restrito a governança e documentação;
- todos os critérios de aceite estiverem verificáveis;
- o Pull Request referenciar a Issue #8 e esta SPEC;
- riscos, limitações e ausência de mudança funcional estiverem declarados;
- não houver dados reais nem credenciais no conteúdo.

O futuro workflow de GitHub Actions automatizará parte desses gates em uma Issue
separada. Nesta Issue, a validação continua sendo executada localmente e
registrada no Pull Request.

## 10. Versionamento, commits e releases

### SemVer

O projeto adotará o formato `MAJOR.MINOR.PATCH`:

- `MAJOR`: mudança incompatível com contratos públicos anteriores;
- `MINOR`: nova funcionalidade compatível;
- `PATCH`: correção compatível.

### Distinções

| Elemento | Finalidade |
| --- | --- |
| Commit | Registra uma alteração específica no histórico Git. |
| Tag | Dá um nome imutável a um commit, normalmente uma versão como `v0.2.0`. |
| GitHub Release | Publica uma tag com notas, contexto e artefatos para usuários. |

Um commit não cria automaticamente uma versão. Uma tag identifica um ponto do
histórico, enquanto a GitHub Release comunica formalmente essa versão.

### Impacto deste incremento

- versão atual do projeto: `0.1.0`;
- impacto imediato: `SEM ALTERAÇÃO`;
- registro: seção `Unreleased` do `CHANGELOG.md`;
- criação de tag: não;
- criação de GitHub Release: não.

A Issue #8 estabelece a política, mas não publica uma nova versão.

## 11. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Templates extensos não serem preenchidos com atenção | Média | Médio | Campos objetivos e checklist de revisão |
| Documentação ficar desatualizada | Média | Alto | Exigir atualização no Pull Request quando o processo mudar |
| Processo gerar burocracia desnecessária | Baixa | Médio | Aplicar SPEC completa apenas a mudanças relevantes |
| Confundir aprovação técnica com decisão de domínio | Baixa | Alto | Manter a responsabilidade humana explícita nos templates |
| Gates permanecerem manuais nesta etapa | Alta | Médio | Criar Issue separada para GitHub Actions |

Limitação conhecida: esta Issue documenta e padroniza o processo, mas não o
automatiza nem impede tecnicamente um merge fora do padrão.

## 12. Plano de reversão

Como o incremento contém apenas documentos e templates, a reversão pode ser
feita revertendo o commit ou Pull Request correspondente. Nenhum dado de
negócio, contrato funcional ou estado de execução precisa ser migrado.

Antes da reversão, deve-se registrar o motivo e avaliar se outros Pull Requests
já dependem dos templates ou políticas introduzidos.

## 13. Critérios de aceite

- [ ] novas Issues solicitam problema, evidências, impacto, escopo e critérios
  de aceite;
- [ ] Pull Requests exigem vínculo com Issue/SPEC, validações, riscos e
  limitações;
- [ ] existe uma SPEC reutilizável e versionada;
- [ ] TDD e gates de qualidade estão documentados;
- [ ] o processo distingue commit, tag e GitHub Release;
- [ ] existe política SemVer para versões `MAJOR.MINOR.PATCH`;
- [ ] existe um `CHANGELOG.md` inicial;
- [ ] a responsabilidade humana pelas decisões de domínio está documentada;
- [ ] nenhuma regra funcional do baseline ou do Módulo 2 foi alterada;
- [ ] os 24 testes existentes continuam aprovados.

## 14. Questões em aberto

- definir, em Issue própria, quando e como os gates serão automatizados pelo
  GitHub Actions;
- avaliar futuramente a proteção da branch `main` após o workflow estar maduro.

Essas questões não bloqueiam a conclusão da Issue #8.

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `2026-08-05` | Adotar Issue → SPEC → TDD → PR → revisão → merge → release | Criar rastreabilidade e repetibilidade | Jk-Pascoal |
| `2026-08-05` | Manter GitHub Actions fora do escopo | Automação será tratada em Issue própria | Jk-Pascoal |
| `2026-08-05` | Não alterar a versão `0.1.0` nesta Issue | O incremento formaliza o processo sem publicar funcionalidade | Jk-Pascoal |
| `2026-08-05` | Preservar decisão final humana em PDM/BOM | Recomendações do agente não substituem o especialista | Jk-Pascoal |
