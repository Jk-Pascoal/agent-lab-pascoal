# SPEC 0012 — Proteção da branch `main` e CI obrigatória

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0012` |
| Status | `Implementada` |
| Issue relacionada | `#12` — `[QUALITY] Proteger a branch main e exigir CI aprovada` |
| Responsável | Jakson Pascoal (`Jk-Pascoal`) |
| Data de criação | `2026-08-07` |
| Última atualização | `2026-08-08` |
| Área | Testes, qualidade e governança do repositório |

## 1. Contexto

O Agent Lab Pascoal já possui um workflow de integração contínua em
`.github/workflows/tests.yml`.

A CI é executada automaticamente em Pull Requests e pushes direcionados à
branch `main`, utilizando Python 3.11 em ambiente Linux e executando a suíte
automatizada do projeto.

O repositório possui atualmente 24 testes automatizados aprovados localmente.
A implementação da CI foi concluída na Issue #10 e incorporada pelo Pull
Request #11.

A Issue #10 deixou deliberadamente a proteção obrigatória da branch `main`
fora de seu escopo. Dessa forma, a CI já produz evidência automatizada de
qualidade, mas essa evidência ainda precisa ser promovida a um gate obrigatório
de integração.

Este incremento trata exclusivamente dessa camada de governança.

## 2. Problema, evidências e impacto

### Problema

A existência de um check de CI não garante, por si só, que a branch `main`
esteja protegida contra integrações realizadas sem a aprovação desse check.

Sem uma regra explícita de proteção, a CI pode funcionar apenas como mecanismo
informativo: ela mostra se os testes passaram ou falharam, mas não
necessariamente impede o fluxo normal de merge de uma alteração reprovada.

### Evidências

O estado atual do projeto apresenta:

- 24 testes automatizados com `unittest`;
- workflow versionado em `.github/workflows/tests.yml`;
- execução automática em Pull Requests para `main`;
- execução automática em pushes para `main`;
- Python 3.11 configurado na CI;
- Pull Request #11 incorporado com a implementação do GitHub Actions;
- ausência, até a Issue #12, de uma política formal que torne o check da CI
  obrigatório antes do merge.

A própria SPEC 0010 registrou a proteção obrigatória da `main` como item fora
do escopo daquele incremento.

### Impacto

Caso a proteção não seja implementada:

- uma regressão poderá chegar à `main` se o check falhar e o merge ainda puder
  ser realizado;
- o workflow documentado e o comportamento efetivo do repositório poderão
  divergir;
- a confiabilidade da `main` continuará dependendo parcialmente de disciplina
  manual;
- a CI terá menor valor como evidência pública de maturidade de engenharia.

Com a proteção ativa, a expectativa é que:

```text
alteração
    ↓
Pull Request
    ↓
CI obrigatória
    ↓
check aprovado?
 ┌───────┴───────┐
 não             sim
  ↓               ↓
merge bloqueado   revisão
                  ↓
                 merge
                  ↓
                 main
```

## 3. Objetivo

Transformar a CI existente em um gate efetivo de qualidade para a branch
`main`.

Ao final do incremento, o fluxo normal de integração deverá satisfazer a
seguinte propriedade:

```text
main = alteração rastreável + Pull Request + CI aprovada + decisão humana de merge
```

O resultado deverá ser demonstrado por evidência observável no GitHub, e não
apenas por documentação.

## 4. Escopo

### Incluído

- aplicar regra de proteção ou ruleset à branch `main`;
- exigir Pull Request no fluxo normal de integração;
- tornar obrigatório o status check da CI existente;
- verificar o nome exato do check exibido pelo GitHub antes de torná-lo
  obrigatório;
- impedir o merge normal enquanto o check obrigatório estiver falhando ou
  pendente;
- validar um cenário controlado de CI reprovada;
- validar posteriormente um cenário de CI aprovada;
- preservar uma via segura de administração/recuperação do repositório sem
  transformar bypass em prática normal;
- documentar a política de proteção no workflow de engenharia;
- manter os 24 testes atuais aprovados no estado final;
- registrar no Pull Request as evidências da configuração e da validação.

### Fora do escopo

- integração com provedores reais de LLM;
- alteração de regras funcionais PDM/BOM;
- novos comportamentos do agente;
- criação de novos testes de negócio permanentes;
- cobertura de testes;
- linting ou formatação automática;
- matriz de múltiplas versões do Python;
- matriz de múltiplos sistemas operacionais;
- deploy;
- ambientes de staging ou produção;
- criação de tag;
- publicação de GitHub Release;
- exigência de assinatura de commits;
- exigência de code scanning;
- exigência de deployments;
- exigência de aprovação obrigatória por outro reviewer nesta fase;
- adoção de regras adicionais sem relação direta com a Issue #12.

## 5. Responsabilidade humana e limites do agente

Este incremento protege o processo de integração do repositório; ele não
transfere a decisão final de engenharia para a automação.

O GitHub Actions poderá afirmar que os testes automatizados foram aprovados ou
reprovados. Essa evidência não representa prova absoluta de correção do
software.

Continuam sob responsabilidade humana:

- interpretar os resultados da CI;
- analisar o diff;
- verificar se a implementação satisfaz a Issue e a SPEC;
- decidir se riscos e limitações são aceitáveis;
- decidir quando o Pull Request está pronto para merge;
- autorizar qualquer exceção administrativa;
- tomar decisões de domínio PDM/BOM.

Como o projeto possui atualmente um mantenedor principal, não será exigida,
nesta fase, aprovação obrigatória de um segundo reviewer. O code review
continua sendo parte do processo, mas não será configurado de modo a tornar o
projeto impossível de manter por uma única pessoa.

## 6. Requisitos

### Requisitos funcionais

- `RF-01` — A branch `main` deve ser alvo de uma regra de proteção ativa.
- `RF-02` — O fluxo normal de alteração da `main` deve ocorrer por Pull Request.
- `RF-03` — O status check da suíte de testes deve ser obrigatório antes do
  merge.
- `RF-04` — Um Pull Request com o check obrigatório reprovado deve permanecer
  bloqueado para merge normal.
- `RF-05` — Um Pull Request com o check obrigatório aprovado deve poder
  prosseguir para revisão e merge, desde que os demais critérios do projeto
  sejam atendidos.
- `RF-06` — A configuração final deve preservar uma forma segura de
  administração ou recuperação do repositório para situações excepcionais.
- `RF-07` — A política efetivamente configurada no GitHub deve ser documentada
  no repositório.

### Requisitos de qualidade

- `RQ-01` — A regra deve ser simples e limitada ao escopo da Issue #12.
- `RQ-02` — A proteção não deve depender de credenciais, secrets ou dados
  proprietários.
- `RQ-03` — O status check obrigatório deve corresponder ao check realmente
  emitido pelo workflow existente.
- `RQ-04` — A validação deve produzir evidências observáveis e registráveis no
  Pull Request.
- `RQ-05` — Nenhuma falha deliberada utilizada para validar o gate pode
  permanecer no estado final destinado ao merge.
- `RQ-06` — Os 24 testes existentes devem permanecer aprovados no estado final.
- `RQ-07` — A configuração não deve exigir, nesta fase, uma segunda pessoa para
  aprovar o Pull Request.

## 7. Proposta técnica

### Visão geral

Utilizar o mecanismo nativo de proteção de branches do GitHub, preferencialmente
um Ruleset quando disponível para o repositório, ou a proteção clássica de
branch caso essa seja a opção adequada apresentada pela interface.

A política será aplicada especificamente à branch:

```text
main
```

A configuração mínima desejada será:

1. exigir Pull Request antes da integração;
2. exigir aprovação do status check da CI;
3. impedir merge normal com check pendente ou falhando;
4. não exigir aprovação obrigatória de um segundo reviewer nesta fase;
5. não habilitar regras adicionais que ampliem o escopo sem necessidade;
6. preservar capacidade administrativa de recuperação, documentando que
   qualquer bypass é excepcional.

### Status check esperado

O workflow atual possui:

```text
Workflow: Testes
Job:      Python 3.11
```

O nome do status check apresentado pela interface do GitHub deverá ser
confirmado durante a configuração.

A hipótese inicial é que o check a ser selecionado corresponda ao job:

```text
Python 3.11
```

Essa hipótese não deve ser tratada como fato até a interface do GitHub exibir o
check disponível para seleção.

### Fluxo esperado

```text
branch de trabalho
      ↓
push
      ↓
Pull Request → main
      ↓
GitHub Actions
      ↓
Python 3.11
      ↓
24 testes
      ↓
┌───────────────────────┐
│ check falhou/pendente │
└───────────┬───────────┘
            ↓
       merge bloqueado

ou

┌───────────────────────┐
│    check aprovado     │
└───────────┬───────────┘
            ↓
        code review
            ↓
           merge
            ↓
           main
```

### Contratos de dados

Não há alteração de contrato de dados, modelos Pydantic, JSON Schema, Enums ou
interfaces funcionais do agente.

A mudança é de governança do repositório.

### Arquivos previstos

- `docs/specs/0012_main_branch_protection.md` — contrato técnico do incremento;
- `docs/04_engineering_workflow.md` — documentar que a CI aprovada passa a ser
  gate obrigatório da `main`;
- `CHANGELOG.md` — registrar, em `Unreleased`, a evolução de governança, caso o
  changelog atual utilize esse nível de alteração.

Não são previstas alterações permanentes em arquivos de código Python.

A configuração de proteção propriamente dita será realizada no GitHub e,
portanto, não será representada integralmente por um arquivo versionado. Por
isso a documentação e as evidências do Pull Request são obrigatórias para
preservar rastreabilidade.

## 8. Estratégia de testes e TDD

### Natureza do TDD neste incremento

Este incremento não introduz comportamento funcional em Python. Portanto, o
ciclo TDD clássico baseado em teste unitário permanente não é a principal
ferramenta de validação.

Será utilizada uma adaptação comportamental do ciclo:

```text
VERMELHO → VERDE → REGRESSÃO
```

onde o comportamento sob teste é a governança do GitHub.

### Vermelho

Antes da implementação, o critério de proteção ainda não está satisfeito:

```text
CI existe
≠
CI obrigatória para merge
```

A evidência inicial é a ausência de uma regra que obrigue o check antes da
integração.

Após configurar a proteção, deverá ser criado ou utilizado um Pull Request de
validação em branch isolada.

Para comprovar o bloqueio, poderá ser produzida temporariamente uma falha
controlada na branch de validação, suficiente para fazer a CI reprovar.

Essa falha:

- deve existir apenas na branch/PR de validação;
- não pode ser incorporada à `main`;
- deve ser removida ou revertida antes do estado final do Pull Request.

O resultado esperado do cenário vermelho é:

```text
CI = falhou
merge normal = bloqueado
```

### Verde

Depois de confirmar o bloqueio:

1. remover ou reverter a falha controlada;
2. executar os testes localmente;
3. enviar novo commit para a mesma branch;
4. aguardar nova execução do GitHub Actions;
5. confirmar que o check passa.

Resultado esperado:

```text
CI = aprovada
merge normal = disponível, sujeito à revisão
```

### Regressão

Antes do merge final:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
git diff --check
git status -sb
```

A suíte deverá retornar:

```text
Ran 24 tests
OK
```

ou número superior, caso testes permanentes legítimos tenham sido adicionados
por outro incremento antes da conclusão desta SPEC.

### Validações previstas

- regra/ruleset aplica-se efetivamente à `main`;
- Pull Request é exigido no fluxo normal;
- check correto da CI é obrigatório;
- CI falhando bloqueia merge;
- CI aprovada libera o gate automatizado;
- nenhum teste deliberadamente quebrado permanece no diff final;
- suíte completa continua verde;
- documentação corresponde à configuração real.

## 9. Gates de qualidade

Antes do Pull Request final, executar:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
git diff --check
git status -sb
```

Quando houver arquivos staged, verificar também:

```powershell
git diff --cached --check
git diff --cached --stat
```

Critérios mínimos:

- 24 testes ou mais aprovados;
- `git diff --check` sem erros;
- nenhum erro deliberado usado na validação permanece no estado final;
- alterações versionadas limitadas aos documentos previstos;
- regra de proteção ativa na `main`;
- check obrigatório confirmado visualmente no GitHub;
- evidência de um cenário de CI reprovada com merge bloqueado;
- evidência posterior de CI aprovada;
- nenhum segredo ou dado real incluído;
- riscos e limitações registrados no Pull Request;
- Pull Request referencia `#12` e `SPEC-0012`.

## 10. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Selecionar o status check incorreto | Média | Alto | Confirmar o nome exato do check emitido pelo workflow antes de salvar a regra |
| Configuração excessivamente rígida para um único mantenedor | Média | Médio | Não exigir segundo reviewer nesta fase e preservar procedimento administrativo de recuperação |
| Bypass administrativo enfraquecer o gate | Baixa | Alto | Tratar bypass como exceção emergencial e nunca como fluxo normal |
| Falha controlada de CI permanecer no PR | Baixa | Alto | Reverter a falha, revisar `git diff` e exigir CI verde antes do merge |
| Configuração do GitHub não ficar registrada no histórico Git | Alta | Médio | Documentar política em `docs/04_engineering_workflow.md` e registrar evidências no PR |
| CI verde gerar falsa sensação de correção total | Média | Médio | Manter code review, critérios de aceite e responsabilidade humana |
| Mudança futura no nome do job quebrar o required check | Baixa | Médio | Revisar ruleset sempre que `.github/workflows/tests.yml` alterar nome/estrutura do job |

### Limitações conhecidas após o incremento

Mesmo com a proteção implementada:

- os testes cobrem apenas os comportamentos explicitamente modelados;
- o workflow utiliza inicialmente apenas Python 3.11 e `ubuntu-latest`;
- não haverá cobertura de testes obrigatória;
- não haverá análise estática obrigatória;
- não haverá reviewer externo obrigatório;
- um administrador poderá possuir mecanismos excepcionais de recuperação,
  dependendo das opções disponibilizadas pelo GitHub;
- configurações de governança do GitHub não são totalmente versionadas pelo
  Git tradicional.

## 11. Plano de reversão

Caso a proteção cause bloqueio indevido ou impeça operações legítimas:

1. não contornar silenciosamente o problema;
2. identificar qual regra está causando o bloqueio;
3. registrar a evidência na Issue #12 ou no Pull Request;
4. revisar o status check selecionado;
5. corrigir ou desativar apenas a regra problemática;
6. manter a CI existente funcionando;
7. validar novamente o fluxo;
8. atualizar a documentação para refletir a configuração real.

Se for necessário remover a proteção inteira por emergência, a decisão deverá
ser registrada e tratada como estado temporário, com nova Issue caso a correção
não possa ser feita imediatamente.

Nenhuma reversão deste incremento deverá exigir alteração de regras PDM/BOM ou
de contratos do agente.

## 12. Versionamento e release

### Impacto SemVer

`SEM ALTERAÇÃO`

Justificativa: este incremento altera governança do repositório e documentação
do processo de engenharia, sem modificar a API, os contratos de dados ou o
comportamento funcional publicado do agente.

### Publicação prevista

- versão planejada: `Unreleased`;
- criação de tag: não;
- criação de GitHub Release: não;
- atualização do `CHANGELOG.md`: sim, se compatível com a política atual do
  changelog.

## 13. Critérios de aceite

- [x] existe uma regra de proteção ativa aplicável à branch `main`;
- [x] o fluxo normal de integração da `main` exige Pull Request;
- [x] o workflow existente em `.github/workflows/tests.yml` continua
  operacional;
- [x] o status check correto da CI é obrigatório;
- [x] um Pull Request com CI pendente ou falhando não pode ser integrado pelo
  fluxo normal;
- [x] existe evidência observável de um cenário de CI reprovada com merge
  bloqueado;
- [x] a falha controlada usada na validação foi removida antes do estado final;
- [x] um Pull Request com CI aprovada pode prosseguir para revisão e merge;
- [x] a configuração não exige obrigatoriamente um segundo mantenedor nesta
  fase;
- [x] a política de proteção está documentada no repositório;
- [x] os 24 testes existentes continuam aprovados no estado final;
- [x] `git diff --check` não apresenta erros;
- [x] nenhuma credencial, secret ou dado proprietário foi incluído;
- [x] riscos, limitações e procedimento de reversão estão documentados;
- [x] a decisão final de merge permanece humana;
- [x] o Pull Request referencia a Issue #12 e esta SPEC.

## 14. Questões resolvidas

1. **Mecanismo de proteção adotado:** GitHub Ruleset.

2. **Status check obrigatório confirmado:** `Python 3.11`, apresentado no
   Pull Request como `Testes / Python 3.11`.

3. **Administração e recuperação:** o Ruleset foi mantido simples, sem exigência
   de segundo reviewer e sem bypass configurado para o fluxo normal. O
   proprietário do repositório mantém capacidade administrativa de alterar ou
   desativar o Ruleset em situação excepcional.

4. **Validação RED:** Pull Request experimental #13 confirmou que CI reprovada
   bloqueia o merge.

5. **Validação GREEN:** Pull Request #14 confirmou que CI aprovada satisfaz o
   required status check e libera o fluxo normal para merge.

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `2026-08-07` | Criar `SPEC-0012` para proteção da `main` | A CI já existe, mas ainda precisa tornar-se gate obrigatório de integração | Jakson Pascoal |
| `2026-08-07` | Não exigir segundo reviewer nesta fase | O projeto possui atualmente um único mantenedor principal | Jakson Pascoal |
| `2026-08-07` | Validar o gate com cenário controlado de falha e recuperação | O critério deve ser demonstrado por evidência observável, não apenas por configuração declarada | Jakson Pascoal |
| `2026-08-07` | Adotar GitHub Ruleset para proteger a `main` | É o mecanismo disponível e adequado ao repositório | Jakson Pascoal |
| `2026-08-07` | Confirmar `Python 3.11` como required status check | É o job real emitido pelo workflow `Testes` | Jakson Pascoal |
| `2026-08-07` | Validar cenário RED no PR #13 | A CI falhou e o merge permaneceu bloqueado | Jakson Pascoal |
| `2026-08-08` | Validar cenário GREEN no PR #14 | A CI foi aprovada e o merge foi liberado | Jakson Pascoal |

## 16. Rastreabilidade

Esta especificação implementa a Issue:

```text
#12 — [QUALITY] Proteger a branch main e exigir CI aprovada
```

O futuro Pull Request deverá referenciar:

```text
Closes #12
```

e identificar explicitamente:

```text
SPEC-0012
```

O incremento será considerado concluído somente quando configuração,
documentação e evidências forem coerentes entre si.
