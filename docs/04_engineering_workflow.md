# Workflow de Engenharia do Agent Lab Pascoal

## 1. Objetivo

Este documento define o processo utilizado para planejar, implementar,
verificar e incorporar mudanças no Agent Lab Pascoal.

O workflow transforma uma necessidade em uma alteração rastreável:

```text
Issue → análise → SPEC → TDD → implementação → Pull Request
      → CI → revisão → merge → release
```

Cada etapa reduz uma incerteza diferente. A Issue explica o problema; a SPEC
registra a decisão; os testes verificam o comportamento; o Pull Request reúne
as evidências; a revisão controla a qualidade; e a release comunica uma versão.

## 2. Princípios do processo

### 2.1 Problema antes da solução

Uma mudança deve começar pela compreensão do problema, das evidências e do
impacto. Escolher uma tecnologia antes de compreender a necessidade aumenta o
risco de produzir uma solução elegante para o problema errado.

### 2.2 Mudanças pequenas e verificáveis

Cada incremento deve possuir escopo limitado, critérios de aceite claros e uma
forma objetiva de validação. Mudanças menores são mais fáceis de testar,
revisar, explicar e reverter.

### 2.3 Evidência antes de confiança

Uma afirmação como "funcionou" não substitui a saída dos testes, a inspeção do
diff ou uma validação reproduzível. Confiança técnica deve nascer de evidências.

### 2.4 Rastreabilidade

Deve ser possível percorrer o caminho nos dois sentidos:

```text
necessidade → Issue → SPEC → código/teste → PR → versão
versão → PR → código/teste → SPEC → Issue → necessidade
```

### 2.5 Responsabilidade humana

O sistema pode analisar, validar e recomendar. A decisão final sobre aprovação,
rejeição, exceções de governança ou alterações PDM/BOM continua pertencendo ao
especialista humano responsável.

## 3. Artefatos e suas funções

| Artefato | Pergunta respondida |
| --- | --- |
| Issue | Qual problema existe e por que ele importa? |
| SPEC | O que será construído, como será validado e quais são os limites? |
| Branch | Onde a mudança ficará isolada durante o desenvolvimento? |
| Teste | Como demonstramos que o comportamento está correto? |
| Commit | Qual unidade de mudança foi registrada no histórico? |
| Pull Request | A mudança está pronta, comprovada e revisável? |
| CI | Os gates automatizados foram executados de forma reproduzível? |
| Revisão | O escopo, a qualidade e os riscos são aceitáveis? |
| Merge | A mudança aprovada foi incorporada à branch principal? |
| Tag | Qual commit representa uma versão específica? |
| GitHub Release | Como essa versão é comunicada aos usuários? |
| CHANGELOG | Quais mudanças relevantes ocorreram entre as versões? |

## 4. Etapa 1 — Issue

### Finalidade

A Issue registra uma necessidade antes do início da implementação. Ela é a
origem formal do trabalho e não deve ser apenas uma lista de tarefas.

### Conteúdo mínimo

- problema;
- evidências;
- impacto;
- objetivo;
- escopo e itens fora do escopo;
- critérios de aceite;
- riscos ou limitações já conhecidos.

### Tipos iniciais

- **Feature:** nova capacidade ou evolução compatível;
- **Bug:** comportamento incorreto ou regressão reproduzível.

### Gate de saída

A Issue está pronta para análise quando o problema pode ser compreendido sem
depender de uma conversa externa e seus critérios de aceite são verificáveis.

## 5. Etapa 2 — Análise

### Finalidade

A análise separa fatos, hipóteses e decisões. Seu objetivo é confirmar se o
problema existe, delimitar o incremento e identificar dependências.

### Perguntas orientadoras

1. Qual evidência comprova o problema?
2. Qual comportamento já existe?
3. Qual é a menor mudança capaz de gerar valor?
4. O que explicitamente não será alterado?
5. Existe risco para contratos, dados ou regras PDM/BOM?
6. Como a mudança será testada e revertida?
7. A solução mais simples já é suficiente?

### Gate de saída

A análise termina quando há informação suficiente para escrever uma SPEC sem
inventar requisitos durante a implementação.

## 6. Etapa 3 — SPEC

### Finalidade

A SPEC é o contrato técnico do incremento. Ela registra a decisão antes que o
código torne essa decisão mais cara de modificar.

### Quando criar

Uma SPEC é recomendada quando a mudança:

- introduz comportamento ou contrato novo;
- altera arquitetura, fluxo ou dados;
- possui risco relevante;
- exige mais de um arquivo ou etapa coordenada;
- precisa permanecer compreensível no futuro.

Correções triviais podem usar uma Issue detalhada, desde que a rastreabilidade
e os critérios de aceite sejam preservados.

### Nomenclatura

```text
docs/specs/NNNN_nome_descritivo.md
```

Exemplo:

```text
docs/specs/0008_engineering_workflow.md
```

### Conteúdo mínimo

- contexto, problema, evidências e impacto;
- objetivo, escopo e itens fora do escopo;
- requisitos funcionais e de qualidade;
- proposta técnica e arquivos afetados;
- estratégia TDD e gates de qualidade;
- riscos, limitações e reversão;
- impacto de versionamento;
- critérios de aceite;
- responsabilidade humana.

### Gate de saída

A SPEC está pronta quando uma pessoa que não participou da conversa consegue
compreender o que será feito, o que não será feito e como o resultado será
verificado.

## 7. Etapa 4 — Branch

### Finalidade

A branch isola o trabalho em andamento da branch `main`.

### Preparação

```powershell
git switch main
git pull origin main
git switch -c tipo/descricao-curta
```

### Padrões de nome

```text
agent/issue-08-governance-workflow
feature/descricao-curta
fix/descricao-curta
docs/descricao-curta
```

O nome deve indicar a natureza e o propósito da mudança. Quando possível,
inclua o número da Issue.

### Gate de saída

Antes de editar arquivos, confirme:

```powershell
git status -sb
```

A saída deve mostrar a branch correta e não deve conter alterações antigas não
relacionadas ao novo incremento.

## 8. Etapa 5 — TDD

TDD significa desenvolver guiado por testes. O ciclo utilizado é:

```text
Vermelho → Verde → Regressão → Refatoração segura
```

### 8.1 Vermelho

Crie primeiro um teste que represente o comportamento desejado. Ele deve falhar
por uma razão conhecida: o comportamento ainda não existe ou está incorreto.

O vermelho comprova que o teste é capaz de detectar a ausência da solução.

### 8.2 Verde

Implemente a menor mudança suficiente para o teste passar. Evite adicionar
funcionalidades não solicitadas pela Issue ou pela SPEC.

### 8.3 Regressão

Execute a suíte completa. Um teste específico aprovado não garante que outras
partes do sistema permaneceram corretas.

```powershell
python -m unittest discover -s tests -v
```

### 8.4 Refatoração segura

Depois que os testes estiverem verdes, melhore nomes, estrutura ou duplicação
sem alterar o comportamento. Execute novamente a suíte após a refatoração.

### TDD em mudanças documentais

Quando não há código funcional, os critérios de aceite funcionam como uma
verificação inicialmente reprovada: os documentos ou templates ainda não
existem. A regressão continua obrigatória para demonstrar que a documentação
não alterou acidentalmente o sistema.

## 9. Etapa 6 — Implementação

### Regras

- modificar somente arquivos previstos;
- preservar contratos existentes, salvo decisão explícita na SPEC;
- reutilizar modelos e Enums do domínio;
- evitar dependências desnecessárias;
- não versionar dados reais, credenciais ou segredos;
- manter funções e arquivos com responsabilidade clara;
- documentar limitações conhecidas.

### Inspeção durante o trabalho

```powershell
git status -sb
git diff
```

O `git diff` deve ser lido como uma explicação da mudança, não apenas como um
passo burocrático antes do commit.

## 10. Etapa 7 — Commit

### Finalidade

Um commit registra uma unidade coerente de alteração. Ele não é uma versão nem
uma release.

### Boas práticas

- escrever a mensagem no imperativo ou como ação concluída;
- descrever o resultado, não o ato de editar;
- evitar misturar mudanças independentes;
- não usar mensagens vagas como `ajustes` ou `alterações`.

Exemplos:

```text
Adiciona contrato estruturado para saídas de agentes
Valida JSON bruto antes da entrada no domínio
Documenta workflow de engenharia e versionamento
```

Antes do commit:

```powershell
git diff --check
git diff --cached --check
git diff --cached --stat
```

## 11. Etapa 8 — Pull Request

### Finalidade

O Pull Request é o pacote de revisão. Ele conecta problema, decisão,
implementação e evidências.

### Conteúdo mínimo

- vínculo com a Issue e a SPEC;
- problema e objetivo;
- mudanças realizadas e itens fora do escopo;
- evidências do ciclo TDD;
- comandos e resultados de validação;
- riscos e limitações;
- impacto de segurança e dados;
- responsabilidade humana;
- impacto SemVer;
- plano de reversão.

### Gate de saída

O Pull Request está pronto para revisão quando outra pessoa consegue reproduzir
as validações e compreender o diff sem depender de explicações privadas.

## 12. Etapa 9 — CI

CI significa integração contínua. Seu papel é executar gates automaticamente
em um ambiente reproduzível sempre que houver push ou Pull Request.

Gates planejados:

- instalação controlada das dependências;
- execução da suíte de testes;
- verificação de formatação e qualidade;
- validação de arquivos de configuração;
- bloqueio do merge quando um gate obrigatório falhar.

O workflow de GitHub Actions não é criado na Issue #8. Até a automação ser
implementada em Issue própria, os comandos são executados localmente e seus
resultados registrados no Pull Request.

## 13. Etapa 10 — Code review

### Finalidade

A revisão de código não procura apenas erros sintáticos. Ela avalia se a mudança
é necessária, coerente, testável, segura e compatível com o domínio.

### Ordem recomendada de revisão

1. confirmar Issue, SPEC e critérios de aceite;
2. conferir se o diff respeita o escopo;
3. avaliar os testes antes da implementação;
4. verificar contratos, tipos e regras de domínio;
5. inspecionar riscos, limitações e reversão;
6. confirmar segurança dos dados e responsabilidade humana;
7. validar o impacto de versionamento.

### Possíveis resultados

- **Approve:** pronto para merge;
- **Comment:** observação sem bloqueio;
- **Request changes:** correção necessária antes do merge.

## 14. Etapa 11 — Merge

### Critérios mínimos

O merge somente deve ocorrer quando:

- Issue e SPEC estão vinculadas;
- critérios de aceite foram atendidos;
- testes específicos e suíte completa estão aprovados;
- `git diff --check` não apresenta erros;
- riscos e limitações foram registrados;
- não existem segredos ou dados reais no diff;
- a responsabilidade humana foi preservada;
- a revisão foi concluída;
- o impacto de versionamento foi definido.

Após o merge, atualize o ambiente local:

```powershell
git switch main
git pull origin main
```

Branches incorporadas podem ser removidas quando não forem mais necessárias.

## 15. Etapa 12 — Versionamento e release

O projeto utiliza SemVer:

```text
MAJOR.MINOR.PATCH
```

- `MAJOR`: mudança incompatível com contratos anteriores;
- `MINOR`: nova funcionalidade compatível;
- `PATCH`: correção compatível.

### Commit, tag e GitHub Release

| Elemento | Significado |
| --- | --- |
| Commit | Unidade registrada no histórico Git. |
| Tag | Referência imutável para um commit, como `v0.2.0`. |
| GitHub Release | Publicação associada à tag, com notas e artefatos. |

Um conjunto de commits pode formar uma versão. A tag aponta o commit exato da
versão. A GitHub Release comunica essa versão a pessoas que utilizam o projeto.

### CHANGELOG

Mudanças relevantes entram primeiro na seção `Unreleased`. Durante uma release,
os itens são movidos para uma seção com número da versão e data.

## 16. Gates de qualidade do projeto

### Gates locais atuais

```powershell
python -m unittest discover -s tests -v
git diff --check
git diff --cached --check
git status -sb
```

### Interpretação

- testes com `OK`: comportamentos verificados permanecem válidos;
- `git diff --check` sem saída: nenhum erro de espaços em branco foi detectado;
- `git status -sb`: branch e arquivos alterados estão visíveis;
- `git diff --cached --stat`: o conteúdo preparado para commit está delimitado.

Nenhum gate isolado prova qualidade absoluta. Juntos, eles reduzem classes
diferentes de risco.

## 17. Segurança de dados

Este repositório é público. Não devem ser versionados:

- cadastros reais de empresas;
- códigos internos ou informações comerciais;
- documentos proprietários;
- credenciais, tokens ou chaves de API;
- logs e capturas de tela contendo informações sensíveis.

Use dados sintéticos, anonimizados ou públicos com origem conhecida.

## 18. Aplicação à Issue #8

A Issue #8 utiliza o próprio workflow que pretende institucionalizar:

1. a Issue registra a ausência do processo formal;
2. `SPEC-0008` delimita o incremento;
3. a branch `agent/issue-08-governance-workflow` isola o trabalho;
4. os templates e documentos satisfazem os critérios inicialmente ausentes;
5. os 24 testes existentes verificam a ausência de regressão funcional;
6. o Pull Request reunirá evidências, riscos e limitações;
7. nenhuma tag ou release será criada neste incremento.

## 19. Checklist operacional resumido

### Antes de implementar

- [ ] Issue criada e analisada;
- [ ] escopo e critérios de aceite definidos;
- [ ] SPEC criada quando necessária;
- [ ] `main` atualizada;
- [ ] branch correta criada.

### Antes do commit

- [ ] testes específicos aprovados;
- [ ] suíte completa aprovada;
- [ ] diff revisado;
- [ ] nenhum dado sensível incluído;
- [ ] documentação atualizada;
- [ ] `git diff --cached --check` executado.

### Antes do merge

- [ ] Issue e SPEC vinculadas ao Pull Request;
- [ ] critérios de aceite atendidos;
- [ ] riscos e limitações registrados;
- [ ] responsabilidade humana preservada;
- [ ] revisão concluída;
- [ ] impacto SemVer definido;
- [ ] CHANGELOG atualizado quando aplicável.

## 20. Estado de evolução

Este workflow é versionado e deverá evoluir com o laboratório. Alterações no
processo devem ser propostas por Issue e revisadas por Pull Request, preservando
o mesmo princípio que o documento estabelece: nenhuma regra de engenharia deve
depender apenas da memória de quem a criou.
