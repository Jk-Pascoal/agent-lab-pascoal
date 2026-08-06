# Contribuindo com o Agent Lab Pascoal

Obrigado pelo interesse em contribuir com o Agent Lab Pascoal.

Este repositório é um laboratório progressivo de engenharia de agentes de IA
aplicado à governança de materiais PDM/BOM. O objetivo é aprender, construir e
avaliar componentes confiáveis sem substituir a decisão do especialista.

Este documento define o processo mínimo para propor, implementar, revisar e
incorporar mudanças no projeto.

## 1. Princípios do projeto

Toda contribuição deve respeitar estes princípios:

- começar pelo problema, não pela ferramenta;
- manter as decisões importantes explícitas e auditáveis;
- preferir soluções simples antes de adicionar IA ou novos frameworks;
- usar testes para proteger o comportamento esperado;
- avaliar qualidade e risco com métricas reproduzíveis;
- preservar a separação entre dados externos e o domínio da aplicação;
- não tratar recomendações do sistema como decisões finais;
- nunca incluir dados empresariais reais ou informações confidenciais.

## 2. Tipos de contribuição

São aceitas contribuições de:

- funcionalidade ou evolução do laboratório;
- correção de defeito;
- novos testes ou melhoria da cobertura existente;
- documentação técnica ou educacional;
- melhoria de qualidade, segurança ou observabilidade;
- governança do repositório e do processo de engenharia;
- manutenção de dependências e ferramentas.

Mudanças de escopo amplo devem ser divididas em incrementos pequenos e
verificáveis.

## 3. Fluxo obrigatório

O fluxo de engenharia adotado pelo projeto é:

```text
Issue → análise → SPEC → TDD → implementação → Pull Request
      → CI → revisão → merge → release
```

Nem toda mudança exige uma SPEC extensa, mas toda mudança precisa de contexto,
critério de aceitação e evidência de validação.

## 4. Antes de começar

Antes de alterar o código:

1. pesquise Issues abertas e fechadas para evitar duplicidade;
2. identifique se a mudança é uma melhoria, um defeito ou documentação;
3. abra uma Issue usando o formulário adequado;
4. descreva o problema observado e o resultado esperado;
5. registre riscos, restrições e itens fora do escopo;
6. aguarde a análise quando a proposta mudar arquitetura, domínio ou contrato.

Uma Issue bem formada deve explicar:

- qual problema precisa ser resolvido;
- quem ou qual componente é afetado;
- quais evidências demonstram o problema;
- qual comportamento é esperado;
- quais riscos precisam ser controlados;
- como saberemos que a mudança foi concluída.

## 5. Quando criar uma SPEC

Crie uma SPEC quando a contribuição:

- introduzir uma funcionalidade nova;
- alterar um contrato público ou saída estruturada;
- modificar regras do domínio PDM/BOM;
- afetar múltiplos módulos;
- introduzir dependência, integração ou decisão arquitetural;
- possuir risco relevante para dados, segurança ou operação;
- exigir critérios de aceitação além de uma correção direta.

Correções pequenas, documentação isolada e ajustes internos podem usar apenas a
Issue, desde que o problema e os critérios de aceitação estejam claros.

Use o arquivo `docs/specs/SPEC_TEMPLATE.md` como ponto de partida.

Nome recomendado:

```text
docs/specs/NNNN_descricao_curta.md
```

O número `NNNN` deve corresponder ao número da Issue, preenchido com zeros à
esquerda. Exemplo para a Issue 8:

```text
docs/specs/0008_engineering_workflow.md
```

## 6. Preparação do ambiente local

Requisitos mínimos:

- Python 3.11;
- Git;
- ambiente virtual Python recomendado;
- acesso a um terminal na raiz do repositório.

Instale o projeto em modo editável:

```powershell
python -m pip install -e .
```

Confirme o estado inicial executando a suíte completa:

```powershell
python -m unittest discover -s tests -v
```

Antes de iniciar uma mudança, todos os testes existentes devem estar aprovados.
Caso exista uma falha anterior, registre-a na Issue antes de continuar.

## 7. Branch de trabalho

Atualize a branch principal antes de criar sua branch:

```powershell
git switch main
git pull origin main
```

Crie uma branch específica para a mudança:

```powershell
git switch -c tipo/descricao-curta
```

Padrões recomendados:

```text
agent/issue-NNN-descricao
feature/issue-NNN-descricao
fix/issue-NNN-descricao
docs/issue-NNN-descricao
test/issue-NNN-descricao
```

Exemplos:

```text
agent/issue-08-governance-workflow
fix/issue-12-invalid-confidence
docs/issue-15-update-readme
```

Use letras minúsculas, hífens e uma descrição curta. Não misture assuntos sem
relação na mesma branch.

## 8. Desenvolvimento orientado por testes

Mudanças de comportamento devem seguir o ciclo TDD:

```text
vermelho → verde → regressão
```

### Vermelho

Escreva primeiro um teste que represente o comportamento esperado e confirme
que ele falha pelo motivo correto.

### Verde

Implemente a menor mudança capaz de aprovar o novo teste.

### Regressão

Execute a suíte completa para confirmar que o comportamento anterior continua
protegido.

O teste deve ter nome descritivo e demonstrar uma regra observável. Evite testes
que dependam de rede, horário, serviços externos ou ordem de execução sem que
isso seja parte explícita do requisito.

## 9. Convenções de implementação

Ao alterar Python:

- use nomes que expressem a intenção do domínio;
- mantenha funções e classes com responsabilidade clara;
- preserve as anotações de tipo;
- evite duplicação de regras e valores já definidos no domínio;
- reutilize Enums e contratos existentes quando aplicável;
- valide dados externos antes de entregá-los ao domínio;
- não silencie exceções sem justificativa;
- mantenha o código determinístico quando não houver necessidade comprovada de IA;
- documente decisões que não sejam evidentes pelo próprio código.

Ao alterar contratos Pydantic:

- rejeite campos inesperados quando o contrato exigir fronteira estrita;
- defina limites e campos obrigatórios explicitamente;
- reutilize os Enums do domínio;
- teste entradas válidas e inválidas;
- considere compatibilidade antes de remover ou renomear campos;
- atualize o JSON Schema e a documentação afetada.

## 10. Documentação

Atualize a documentação quando a mudança alterar:

- instalação ou execução;
- arquitetura ou fluxo;
- comportamento público;
- contrato de dados;
- regra de domínio;
- política de engenharia;
- interpretação de métricas ou resultados.

O `README.md` deve apresentar o laboratório e seu uso. Explicações extensas,
decisões de projeto e conteúdo de estudo devem ficar em `docs/`.

Não inclua promessas comerciais, dados de clientes ou resultados não
reproduzíveis na documentação do laboratório.

## 11. Verificações locais

Antes de preparar um commit, execute:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Depois de selecionar os arquivos com `git add`, execute:

```powershell
git diff --cached --check
git diff --cached --stat
git diff --cached
```

Revise o diff integralmente. Confirme que somente arquivos pertencentes ao
escopo da Issue foram preparados.

## 12. Commits

Cada commit deve representar uma unidade lógica e compreensível.

Use mensagens no imperativo ou que descrevam claramente o resultado:

```text
Adiciona contrato estruturado para saídas de agentes
Valida saída JSON antes da entrada no domínio
Documenta workflow de engenharia da Issue 8
Corrige cálculo de recall de duplicidade
```

Evite mensagens vagas como:

```text
ajustes
mudanças
correção
update
```

Não inclua arquivos temporários, ambientes virtuais, caches, credenciais ou
configurações locais do editor.

## 13. Pull Request

Todo Pull Request deve:

- ter uma Issue relacionada;
- explicar o problema e a solução adotada;
- apontar a SPEC quando ela existir;
- listar os arquivos ou componentes principais alterados;
- registrar testes e verificações executados;
- apresentar riscos e limitações conhecidos;
- indicar impacto em contratos, dados e compatibilidade;
- manter escopo pequeno o suficiente para revisão;
- usar o template existente em `.github/PULL_REQUEST_TEMPLATE.md`.

Não marque o Pull Request como pronto enquanto os testes locais estiverem
falhando ou a documentação obrigatória estiver incompleta.

## 14. Critérios de revisão

A revisão deve verificar:

- aderência à Issue e à SPEC;
- correção do comportamento implementado;
- clareza e simplicidade da solução;
- cobertura dos critérios de aceitação;
- qualidade e independência dos testes;
- preservação dos testes anteriores;
- compatibilidade dos contratos;
- tratamento de erros e entradas inválidas;
- segurança e privacidade dos dados;
- rastreabilidade das decisões;
- atualização da documentação;
- ausência de mudanças fora do escopo.

Comentários de revisão devem se concentrar no código, nos requisitos e nos
riscos. Recomendações não obrigatórias devem ser diferenciadas de bloqueios.

## 15. Critérios de merge

Um Pull Request somente pode ser incorporado quando:

- a Issue e a SPEC aplicável estiverem vinculadas;
- os critérios de aceitação estiverem atendidos;
- os testes locais e verificações automatizadas estiverem aprovados;
- não existirem conflitos com a branch principal;
- as revisões obrigatórias estiverem concluídas;
- os comentários bloqueadores estiverem resolvidos;
- a documentação e o `CHANGELOG.md` estiverem atualizados quando aplicável;
- o impacto de versão estiver identificado;
- nenhuma informação sensível tiver sido adicionada.

O merge não deve ser usado para contornar uma verificação pendente.

## 16. Segurança e privacidade dos dados

Este repositório é público. Nunca envie:

- cadastros reais de empresas;
- códigos internos de materiais ou equipamentos;
- informações comerciais ou contratuais;
- documentos proprietários;
- nomes ou dados pessoais sem autorização;
- tokens, senhas, chaves de API ou credenciais;
- arquivos de configuração que revelem segredos;
- respostas de serviços externos contendo dados sensíveis.

Use somente dados sintéticos, anonimizados e autorizados. Se um segredo for
enviado por engano, não tente apenas apagá-lo em um commit posterior: revogue a
credencial e registre o incidente de maneira segura.

## 17. Responsabilidade humana

O sistema oferece recomendações de apoio à governança. Ele não aprova, rejeita,
classifica ou altera definitivamente materiais de uma organização.

Decisões sobre PDM/BOM continuam sob responsabilidade de profissionais
autorizados. Toda contribuição deve preservar:

- possibilidade de revisão humana;
- evidências que sustentem a recomendação;
- diferenciação entre confiança do modelo e certeza factual;
- registro dos alertas e limitações;
- possibilidade de contestar ou substituir a recomendação;
- auditabilidade do processamento.

## 18. Versionamento e CHANGELOG

O projeto adota Versionamento Semântico para comunicar mudanças:

- `MAJOR`: mudança incompatível em contrato ou comportamento público;
- `MINOR`: funcionalidade compatível adicionada;
- `PATCH`: correção compatível ou ajuste de manutenção.

Durante a fase inicial `0.x`, mudanças incompatíveis ainda precisam ser
explicitamente documentadas.

Atualize o `CHANGELOG.md` quando a contribuição produzir alteração perceptível
para usuários, contratos, instalação ou operação. Correções puramente editoriais
podem ser omitidas.

A política completa fica em `VERSIONING.md`.

## 19. Após o merge

Depois da incorporação:

1. confirme que o Pull Request foi fechado como incorporado;
2. exclua a branch remota quando ela não for mais necessária;
3. volte para `main`;
4. atualize o repositório local;
5. exclua a branch local já incorporada;
6. execute a suíte na `main` quando a mudança for relevante;
7. confirme se Issue, documentação e CHANGELOG devem ser encerrados.

Exemplo:

```powershell
git switch main
git pull origin main
git branch -d tipo/descricao-curta
python -m unittest discover -s tests -v
```

## 20. Checklist resumido

### Antes de implementar

- [ ] Pesquisei Issues existentes.
- [ ] Abri ou vinculei a Issue correta.
- [ ] Defini problema, evidências e resultado esperado.
- [ ] Criei a SPEC quando necessária.
- [ ] Confirmei que a suíte inicial está aprovada.
- [ ] Criei uma branch específica.

### Antes do commit

- [ ] Escrevi ou atualizei testes.
- [ ] Executei a suíte completa.
- [ ] Atualizei a documentação afetada.
- [ ] Revisei `git diff --check`.
- [ ] Confirmei que não há dados sensíveis.
- [ ] Preparei somente arquivos do escopo.
- [ ] Revisei o diff preparado.

### Antes do merge

- [ ] O Pull Request referencia a Issue e a SPEC.
- [ ] Os critérios de aceitação foram demonstrados.
- [ ] Testes e verificações estão aprovados.
- [ ] Riscos e limitações estão documentados.
- [ ] Revisões e comentários bloqueadores foram resolvidos.
- [ ] O impacto de versão foi identificado.
- [ ] O CHANGELOG foi atualizado quando aplicável.

## 21. Dúvidas

Se o processo não estiver claro, registre a dúvida na Issue antes de implementar.
Perguntar cedo reduz retrabalho e mantém as decisões do laboratório rastreáveis.
