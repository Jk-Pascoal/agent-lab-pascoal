# Política de Versionamento e Releases

Este documento define como o Agent Lab Pascoal identifica, comunica e publica
mudanças. A política torna a evolução do laboratório rastreável sem transformar
cada experimento em uma promessa de estabilidade prematura.

## 1. Objetivos

O versionamento deve permitir que uma pessoa consiga responder:

- qual versão está sendo utilizada;
- quais mudanças foram incorporadas;
- se uma atualização é compatível com o uso anterior;
- quais contratos ou comportamentos foram alterados;
- quais testes e evidências sustentam a publicação;
- como relacionar uma release a Issues, SPECs, commits e Pull Requests.

## 2. Padrão adotado

O projeto adota Versionamento Semântico, representado por:

```text
MAJOR.MINOR.PATCH
```

Exemplo:

```text
0.2.1
```

Cada posição comunica uma categoria de mudança:

- `MAJOR`: mudança incompatível em comportamento ou contrato público;
- `MINOR`: funcionalidade compatível adicionada;
- `PATCH`: correção ou manutenção compatível.

## 3. Significado de versão pública

Uma versão pública representa um ponto reproduzível do repositório. Ela deve
corresponder a:

- um commit incorporado à branch `main`;
- uma entrada no `CHANGELOG.md`;
- uma tag Git anotada;
- uma release no GitHub quando a publicação for formal;
- uma suíte de testes aprovada;
- documentação coerente com o comportamento publicado.

Uma branch de trabalho, um commit intermediário ou um Pull Request aberto não é
uma release.

## 4. Fase inicial `0.x`

Enquanto o projeto estiver em desenvolvimento inicial, as versões começam com
`0`:

```text
0.MINOR.PATCH
```

Nesta fase:

- a arquitetura ainda pode evoluir rapidamente;
- contratos públicos ainda podem mudar;
- compatibilidade deve ser considerada, mas não é garantida indefinidamente;
- toda incompatibilidade precisa ser documentada;
- uma mudança incompatível normalmente incrementa `MINOR`;
- correções compatíveis incrementam `PATCH`.

Exemplos:

```text
0.1.0  baseline determinístico inicial
0.2.0  saída estruturada e fronteira JSON
0.2.1  correção compatível na validação da saída
0.3.0  nova etapa de orquestração do agente
```

O número inicial `0` não significa ausência de qualidade. Ele comunica que a
interface do laboratório ainda está amadurecendo.

## 5. Versão `1.0.0`

A versão `1.0.0` deve ser considerada somente quando:

- o escopo principal do agente estiver definido;
- os contratos públicos estiverem documentados;
- o fluxo de execução estiver estável;
- as métricas e critérios de avaliação estiverem estabelecidos;
- houver testes suficientes para proteger o comportamento essencial;
- o processo de release estiver sendo usado de forma consistente;
- mudanças incompatíveis puderem ser tratadas como exceção planejada.

A promoção para `1.0.0` exige uma Issue e uma SPEC próprias.

## 6. O que é uma interface pública

Para fins de versionamento, são considerados públicos:

- modelos e campos aceitos por interfaces de entrada;
- saídas estruturadas do agente;
- JSON Schemas exportados;
- Enums e valores usados em integrações;
- funções documentadas para uso externo;
- comandos de terminal documentados;
- formatos de arquivos de entrada e saída;
- decisões, alertas e códigos de erro expostos;
- configurações descritas no README ou em documentação de uso;
- comportamento prometido pelos critérios de aceitação publicados.

Detalhes internos podem mudar sem impacto de versão quando não alterarem o
comportamento observável.

## 7. Quando incrementar `MAJOR`

Após `1.0.0`, incremente `MAJOR` quando ocorrer uma mudança incompatível, como:

- remover ou renomear campo obrigatório de contrato público;
- alterar o significado de uma decisão existente;
- remover valor de Enum usado externamente;
- mudar formato de arquivo sem aceitar o formato anterior;
- alterar comando público de maneira incompatível;
- modificar regra central com efeito incompatível nos resultados;
- remover funcionalidade documentada sem caminho de migração compatível.

Exemplo:

```text
1.4.2 → 2.0.0
```

Ao incrementar `MAJOR`, `MINOR` e `PATCH` voltam para zero.

## 8. Quando incrementar `MINOR`

Incremente `MINOR` quando adicionar funcionalidade compatível, como:

- novo recurso opcional;
- novo campo opcional com valor padrão seguro;
- novo tipo de análise sem remover resultados anteriores;
- nova métrica ou evidência compatível;
- nova integração que não altere o uso existente;
- novo comando mantendo os comandos anteriores;
- depreciação anunciada sem remoção imediata.

Exemplo:

```text
1.4.2 → 1.5.0
```

Ao incrementar `MINOR`, `PATCH` volta para zero.

Durante `0.x`, uma mudança incompatível planejada também incrementa `MINOR`:

```text
0.2.4 → 0.3.0
```

## 9. Quando incrementar `PATCH`

Incremente `PATCH` para mudanças compatíveis, como:

- correção de defeito;
- ajuste de validação que restaure o contrato documentado;
- melhoria interna sem alterar a interface pública;
- correção de documentação relacionada ao comportamento atual;
- melhoria de testes sem mudança funcional;
- atualização compatível de dependência;
- correção de segurança compatível.

Exemplo:

```text
1.4.2 → 1.4.3
```

## 10. Mudanças que podem não exigir release

Nem todo merge precisa gerar uma release imediata. Podem ser acumulados:

- ajustes editoriais sem impacto técnico;
- comentários e exemplos internos;
- manutenção de templates de Issue e Pull Request;
- reorganizações que não alterem uso ou comportamento;
- documentação do processo de aprendizagem.

Mesmo sem release imediata, mudanças relevantes devem permanecer registradas na
seção `Unreleased` do `CHANGELOG.md`.

## 11. Compatibilidade de contratos

Antes de alterar um contrato, avalie:

1. quais consumidores dependem dele;
2. se dados antigos continuam válidos;
3. se respostas antigas continuam interpretáveis;
4. se a alteração pode ser aditiva;
5. se é necessário um período de depreciação;
6. se exemplos, testes e JSON Schema foram atualizados;
7. qual incremento de versão comunica corretamente o impacto.

Alterações aditivas são preferíveis quando preservam clareza e segurança.

## 12. Contratos de agentes e LLMs

Prompts, modelos e provedores podem mudar sem impacto público somente quando a
saída observável continuar respeitando o mesmo contrato e os mesmos critérios de
qualidade.

Exigem avaliação de versão:

- adicionar, remover ou renomear campos de saída;
- alterar limites de confiança;
- mudar valores válidos de decisão ou de alerta;
- alterar a semântica de evidências;
- mudar tratamento de JSON inválido;
- alterar política de fallback;
- modificar comportamento de revisão humana;
- trocar modelo quando houver mudança mensurável nos resultados publicados.

Uma troca de LLM não deve ser tratada como mero detalhe se alterar qualidade,
custo, latência, privacidade ou decisões recomendadas.

## 13. Depreciação

Uma interface deve ser marcada como depreciada antes da remoção sempre que for
viável.

O aviso de depreciação deve informar:

- o elemento afetado;
- a alternativa recomendada;
- a versão em que a depreciação começou;
- a primeira versão em que a remoção pode ocorrer;
- instruções de migração;
- riscos de permanecer na interface antiga.

Uma depreciação compatível incrementa `MINOR`. A remoção posterior incrementa
`MAJOR` após `1.0.0` ou `MINOR` durante `0.x`.

## 14. Pré-releases

Versões ainda não prontas para uso geral podem receber identificadores:

```text
0.3.0-alpha.1
0.3.0-beta.1
0.3.0-rc.1
```

Significados:

- `alpha`: experimento inicial, sujeito a mudanças frequentes;
- `beta`: funcionalidade completa, ainda em validação;
- `rc`: candidata à release, aguardando confirmação final.

Pré-releases não devem substituir branches de trabalho. Elas servem para
publicar um ponto de validação deliberado.

## 15. Metadados de build

Quando necessário, informações de build podem ser adicionadas após `+`:

```text
0.3.0-beta.1+20260805
```

Metadados não alteram a precedência da versão e não substituem a tag ou o hash
do commit como fonte de rastreabilidade.

## 16. Fonte da versão

Enquanto não existir automação específica, a versão declarada no
`pyproject.toml` é a fonte principal da versão do pacote.

Antes de uma release, confirme que estão alinhados:

- versão em `pyproject.toml`;
- título da seção correspondente no `CHANGELOG.md`;
- tag Git;
- título da GitHub Release;
- documentação que mencione a versão atual.

Não mantenha números divergentes em arquivos diferentes.

## 17. Tags Git

Tags de release usam o prefixo `v`:

```text
v0.1.0
v0.2.0
v1.0.0
```

Use tags anotadas para registrar contexto:

```powershell
git tag -a v0.2.0 -m "Release v0.2.0"
```

A tag deve apontar para um commit já incorporado à `main`. Não crie tag de
release em uma branch ainda não revisada.

## 18. GitHub Releases

Uma GitHub Release deve ser criada a partir da tag correspondente e resumir:

- objetivo da versão;
- principais funcionalidades;
- correções relevantes;
- mudanças incompatíveis;
- instruções de migração;
- limitações conhecidas;
- referências a Issues, SPECs e Pull Requests;
- evidências de teste e avaliação.

O texto da release pode ser derivado do `CHANGELOG.md`, mas deve continuar
compreensível isoladamente.

## 19. CHANGELOG

O projeto mantém um `CHANGELOG.md` orientado a pessoas, não uma cópia bruta do
histórico de commits.

As entradas são organizadas em:

```text
Added
Changed
Deprecated
Removed
Fixed
Security
```

Toda mudança ainda não publicada entra em `Unreleased`. Durante a release:

1. mova as entradas aplicáveis para uma seção com a nova versão;
2. informe a data no formato `AAAA-MM-DD`;
3. mantenha `Unreleased` disponível para o próximo ciclo;
4. confirme que incompatibilidades e migrações estão visíveis;
5. relacione a versão à tag correspondente.

## 20. Decisão do incremento

O autor do Pull Request propõe o impacto de versão. A revisão confirma ou
corrige a classificação antes do merge.

Use esta sequência:

```text
A mudança quebra um contrato público?
├── Sim → MAJOR após 1.0.0; MINOR durante 0.x
└── Não
    ├── Adiciona comportamento público compatível? → MINOR
    └── Corrige ou mantém comportamento compatível? → PATCH
```

Quando houver dúvida, escolha a categoria que comunica o maior risco plausível
e documente a justificativa no Pull Request.

## 21. Release normal

Uma release normal segue este processo:

1. confirmar que as mudanças previstas foram incorporadas à `main`;
2. definir o próximo número conforme esta política;
3. atualizar `CHANGELOG.md`;
4. atualizar a versão em `pyproject.toml`;
5. abrir Pull Request exclusivo de release, quando apropriado;
6. executar testes e verificações;
7. revisar compatibilidade, segurança e documentação;
8. incorporar o Pull Request de release;
9. criar a tag anotada no commit correto;
10. enviar a tag ao repositório remoto;
11. criar a GitHub Release;
12. verificar links, artefatos e instruções publicados.

Comandos somente depois da aprovação do incremento e do commit de release:

```powershell
git switch main
git pull origin main
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

Substitua `X.Y.Z` pela versão efetivamente aprovada. Nunca copie esses comandos
com o marcador literal.

## 22. Hotfix

Um hotfix corrige problema urgente em uma versão publicada.

O processo deve:

- abrir uma Issue de defeito;
- registrar impacto e risco;
- criar teste que reproduza o problema;
- aplicar a menor correção segura;
- executar regressão completa;
- atualizar o CHANGELOG;
- incrementar `PATCH`, salvo incompatibilidade inevitável;
- passar por Pull Request e revisão;
- gerar nova tag e release.

Urgência não elimina rastreabilidade nem revisão.

## 23. Reversão

Se uma release introduzir risco significativo:

- interrompa sua adoção;
- registre uma Issue com evidências;
- avalie reversão ou hotfix;
- preserve o histórico Git;
- não mova nem reutilize a tag publicada;
- publique uma nova versão com a correção;
- registre o ocorrido no CHANGELOG e na release.

Tags publicadas são imutáveis. Uma correção posterior recebe novo número.

## 24. Segurança

Correções de segurança devem reduzir exposição sem divulgar detalhes que
facilitem exploração indevida.

Ao publicar:

- classifique o impacto de compatibilidade;
- atualize a seção `Security` do CHANGELOG;
- indique versões afetadas e corrigidas quando conhecidas;
- revogue imediatamente credenciais expostas;
- nunca inclua segredos em commit, tag ou release;
- preserve evidências em local apropriado e com acesso controlado.

## 25. Modelos, dados e reprodutibilidade

Quando uma versão depender de modelos ou conjuntos de dados, registre:

- identificador do modelo e do provedor;
- parâmetros relevantes;
- versão do contrato estruturado;
- origem e natureza sintética ou autorizada dos dados;
- conjunto de avaliação utilizado;
- métricas e limites de aceitação;
- limitações conhecidas.

Dados empresariais reais não devem ser publicados para tornar uma release
reproduzível. Use conjuntos sintéticos ou anonimizados autorizados.

## 26. Responsabilidade humana

Nenhuma versão transforma a recomendação do agente em decisão final.

Releases devem preservar:

- revisão humana nas decisões de governança PDM/BOM;
- evidências e alertas auditáveis;
- limites explícitos de confiança;
- possibilidade de contestação;
- registro das limitações do sistema.

Uma melhoria de desempenho não justifica remover controles humanos sem uma
Issue, uma SPEC, avaliação de risco e aprovação explícita.

## 27. Primeira release do laboratório

A primeira release formal será definida em incremento próprio. Antes dela,
devem estar concluídos:

- política de versionamento aprovada;
- CHANGELOG inicial;
- suíte de testes aprovada;
- documentação de execução atualizada;
- revisão da versão declarada no `pyproject.toml`;
- decisão explícita sobre o conteúdo da release;
- Pull Request de preparação da release.

A Issue 8 estabelece o processo, mas não cria automaticamente uma tag ou uma
GitHub Release.

## 28. Checklist de release

### Planejamento

- [ ] O escopo da release está definido.
- [ ] O incremento de versão foi justificado.
- [ ] Mudanças incompatíveis foram identificadas.
- [ ] Migrações e depreciações foram documentadas.

### Qualidade

- [ ] A suíte completa está aprovada.
- [ ] Os critérios de aceitação foram verificados.
- [ ] Contratos e JSON Schemas foram revisados.
- [ ] Métricas relevantes foram registradas.
- [ ] Não existem dados sensíveis ou credenciais.

### Documentação

- [ ] O `CHANGELOG.md` foi atualizado.
- [ ] A versão em `pyproject.toml` está correta.
- [ ] README e documentos afetados estão coerentes.
- [ ] Limitações conhecidas estão registradas.
- [ ] Responsabilidade humana permanece explícita.

### Publicação

- [ ] O commit de release está na `main`.
- [ ] A tag anotada aponta para o commit correto.
- [ ] A tag foi enviada ao repositório remoto.
- [ ] A GitHub Release foi criada a partir da tag.
- [ ] Links e notas da release foram conferidos.

## 29. Exemplos de classificação

| Mudança | Fase `0.x` | Após `1.0.0` |
| --- | --- | --- |
| Corrigir erro no cálculo sem alterar contrato | PATCH | PATCH |
| Adicionar campo opcional compatível | MINOR | MINOR |
| Adicionar nova métrica pública | MINOR | MINOR |
| Renomear campo obrigatório | MINOR | MAJOR |
| Remover valor de Enum público | MINOR | MAJOR |
| Refatorar internamente com mesmos resultados | PATCH | PATCH |
| Corrigir somente ortografia | Sem release ou PATCH | Sem release ou PATCH |
| Adicionar documentação de governança | Sem release, PATCH ou MINOR conforme impacto | Sem release, PATCH ou MINOR conforme impacto |

## 30. Regra final

O número da versão não mede a importância intelectual de uma mudança. Ele
comunica o impacto técnico esperado para quem depende do projeto.

Quando código, documentação, tag e CHANGELOG discordarem, a release ainda não
está pronta.
