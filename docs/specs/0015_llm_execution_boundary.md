# SPEC 0015 — Fronteira de execução da LLM para análise de materiais

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0015` |
| Status | `Aprovada` |
| Issue relacionada | `#15` — `[FEATURE] Criar fronteira de execução da LLM para análise de materiais` |
| Responsável | Jakson Pascoal (`Jk-Pascoal`) |
| Data de criação | `2026-08-09` |
| Última atualização | `2026-08-09` |
| Área | Agentes / LLM estruturado |

## 1. Contexto

O Agent Lab Pascoal já possui uma base determinística de governança PDM/BOM e
uma fronteira estruturada para futuras respostas produzidas por agentes com LLM.

O domínio atual define `MaterialRecord` como registro de entrada independente de
framework e provedor. A camada de contrato estruturado define
`GovernanceAgentOutput`, validado por Pydantic, com:

- `material_id`;
- `decision`;
- `confidence`;
- `issues`;
- `summary`;
- `evidence`.

Também já existem:

- `parse_governance_agent_output()`, que valida JSON bruto;
- `governance_agent_output_schema()`, que exporta o contrato em JSON Schema;
- rejeição de campos inesperados;
- limites explícitos para `confidence`;
- reutilização dos Enums `GovernanceDecision` e `IssueType`;
- 24 testes automatizados aprovados;
- CI obrigatória na branch `main`.

Ainda não existe, porém, uma camada que execute o fluxo:

```text
MaterialRecord
      ↓
construção da solicitação
      ↓
LLM Provider
      ↓
JSON bruto
      ↓
validação Pydantic
      ↓
GovernanceAgentOutput
```

A ausência dessa fronteira impede que a integração futura com uma LLM real seja
feita de forma desacoplada, testável e independente de fornecedor.

## 2. Problema, evidências e impacto

### Problema

Se uma integração real com LLM for adicionada diretamente ao código de domínio
ou ao módulo de schema, diferentes responsabilidades poderão ficar misturadas:

- construção de prompt;
- transporte para a API;
- escolha de fornecedor;
- configuração do modelo;
- recepção da resposta;
- parsing;
- validação estrutural;
- tratamento de erros;
- regras do domínio.

Esse acoplamento dificultaria testes determinísticos e aumentaria o custo de
substituição de provedores.

### Evidências

O estado atual do repositório apresenta:

- `MaterialRecord` como modelo de entrada de domínio;
- `GovernanceAgentOutput` como contrato estruturado de saída;
- parsing de JSON bruto já implementado;
- JSON Schema já exportável;
- 24 testes automatizados aprovados;
- nenhuma chamada real a uma API de LLM;
- nenhum contrato explícito para providers;
- nenhum Fake/Stub Provider;
- nenhum serviço que conecte material, provider e validação;
- nenhuma dependência de internet ou credencial nos testes atuais.

### Impacto

Sem uma fronteira explícita de execução:

- o domínio poderá depender diretamente de SDKs externos;
- os testes poderão passar a exigir rede, credenciais e custo;
- mudanças de fornecedor poderão contaminar várias camadas;
- respostas probabilísticas poderão tornar testes instáveis;
- a validação Pydantic poderá ser contornada acidentalmente;
- prompt e transporte poderão ficar inseparáveis;
- será mais difícil medir isoladamente erros do modelo, do provider e do domínio.

Com a fronteira proposta, o projeto poderá testar toda a arquitetura de
integração antes de escolher um provedor real.

## 3. Objetivo

Criar uma camada mínima e independente de fornecedor capaz de:

1. receber um `MaterialRecord`;
2. construir uma solicitação determinística para análise;
3. fornecer ao provider o prompt e o JSON Schema esperado;
4. receber uma resposta em JSON bruto;
5. validar a resposta por meio de `parse_governance_agent_output()`;
6. retornar somente um `GovernanceAgentOutput` estruturalmente válido.

A propriedade central deste incremento será:

```text
MaterialRecord
   +
LLMProvider
   ↓
GovernanceLLMService
   ↓
JSON bruto
   ↓
Pydantic
   ↓
GovernanceAgentOutput
```

A implementação deverá ser completamente testável sem internet, sem API key e
sem chamada real a modelos externos.

## 4. Escopo

### Incluído

- criar um contrato mínimo e explícito para providers de LLM;
- manter o contrato independente de OpenAI, Anthropic, Gemini ou outro SDK;
- criar uma fronteira de execução para análise de um `MaterialRecord`;
- criar uma representação textual determinística dos dados do material;
- fornecer ao provider o JSON Schema de `GovernanceAgentOutput`;
- receber JSON bruto do provider;
- reutilizar `parse_governance_agent_output()` como gate estrutural;
- retornar somente `GovernanceAgentOutput` validado;
- criar Fake/Stub Provider para os testes;
- verificar que o provider recebe o prompt esperado;
- verificar que o provider recebe o schema esperado;
- validar cenário de resposta JSON válida;
- validar cenário de resposta JSON malformada ou estruturalmente inválida;
- manter a suíte existente aprovada;
- documentar limitações e decisões arquiteturais relevantes.

### Fora do escopo

- integração real com OpenAI;
- integração real com Anthropic;
- integração real com Gemini;
- qualquer outro SDK de fornecedor;
- chaves de API;
- secrets;
- chamadas HTTP;
- streaming;
- retry;
- backoff;
- timeout de rede;
- fallback entre provedores;
- seleção dinâmica de modelos;
- contabilização de tokens;
- custo financeiro por chamada;
- observabilidade de produção;
- embeddings;
- busca semântica;
- RAG;
- memória;
- tool calling;
- LangGraph;
- multiagentes;
- fine-tuning;
- alterações nas regras determinísticas PDM/BOM;
- decisão automática de cadastro sem revisão humana.

## 5. Responsabilidade humana e limites do agente

A nova fronteira produzirá uma recomendação estruturada, não uma decisão final
de negócio.

Mesmo quando um `GovernanceAgentOutput` for estruturalmente válido, continuam
sob responsabilidade humana:

- interpretar a recomendação;
- verificar as evidências apresentadas;
- confirmar coerência com regras PDM/BOM;
- decidir aprovar, revisar ou rejeitar um cadastro;
- avaliar conflitos com normas, políticas ou contexto empresarial;
- determinar se a confiança informada é aceitável.

A validação Pydantic demonstra conformidade estrutural. Ela não demonstra
veracidade, completude semântica ou correção técnica da análise.

O Fake Provider demonstra a arquitetura da fronteira. Ele não demonstra
qualidade de uma LLM real.

## 6. Requisitos

### Requisitos funcionais

- `RF-01` — Deve existir um contrato explícito `LLMProvider` independente de fornecedor.
- `RF-02` — O provider deve receber uma solicitação textual determinística.
- `RF-03` — O provider deve receber o JSON Schema esperado para a resposta.
- `RF-04` — A fronteira deve aceitar um `MaterialRecord` como entrada.
- `RF-05` — A fronteira deve construir a solicitação a partir dos campos do material.
- `RF-06` — A resposta do provider deve ser recebida como JSON bruto.
- `RF-07` — O JSON bruto deve obrigatoriamente passar por `parse_governance_agent_output()`.
- `RF-08` — JSON válido deve resultar em `GovernanceAgentOutput`.
- `RF-09` — JSON inválido deve continuar produzindo erro de validação, sem entrada silenciosa no domínio.
- `RF-10` — Deve existir um Fake/Stub Provider para testes determinísticos.
- `RF-11` — A implementação não deve realizar chamadas externas neste incremento.

### Requisitos de qualidade

- `RQ-01` — O domínio não deve importar SDKs ou tipos específicos de fornecedor.
- `RQ-02` — Os testes devem executar sem internet.
- `RQ-03` — Os testes devem executar sem API key.
- `RQ-04` — O contrato do provider deve possuir a menor superfície possível.
- `RQ-05` — O prompt produzido deve ser determinístico para a mesma entrada.
- `RQ-06` — O JSON Schema utilizado deve vir de `governance_agent_output_schema()`.
- `RQ-07` — A suíte existente deve permanecer aprovada.
- `RQ-08` — Nenhum dado empresarial real deve ser necessário para os testes.
- `RQ-09` — Nenhum secret ou credencial deve ser versionado.
- `RQ-10` — A implementação deve preservar a responsabilidade humana pela decisão final.

## 7. Proposta técnica

### 7.1 Visão geral

A solução será dividida em três responsabilidades:

```text
MaterialRecord
     ↓
Prompt Builder
     ↓
GovernanceLLMService
     ↓
LLMProvider
     ↓
JSON bruto
     ↓
parse_governance_agent_output()
     ↓
GovernanceAgentOutput
```

### 7.2 Contrato do provider

O contrato proposto é conceitualmente equivalente a:

```python
from typing import Protocol

class LLMProvider(Protocol):
    def generate(
        self,
        *,
        prompt: str,
        response_schema: dict[str, object],
    ) -> str:
        ...
```

A decisão de utilizar `Protocol` permite tipagem estrutural e testes com
implementações simples, sem exigir herança concreta.

O contrato deverá permanecer intencionalmente pequeno.

### 7.3 Serviço de execução

O serviço deverá possuir comportamento equivalente a:

```python
def analyze_material(
    material: MaterialRecord,
    provider: LLMProvider,
) -> GovernanceAgentOutput:
    ...
```

Fluxo interno:

```text
material
   ↓
build_governance_prompt(material)
   ↓
governance_agent_output_schema()
   ↓
provider.generate(...)
   ↓
raw_json
   ↓
parse_governance_agent_output(raw_json)
   ↓
GovernanceAgentOutput
```

### 7.4 Construção do prompt

O prompt inicial deverá ser simples, explícito e determinístico.

Ele deverá incluir os campos:

```text
material_id
description_short
long_description
unit
manufacturer
manufacturer_part_number
material_group
status
```

Não será objetivo desta Issue otimizar linguagem de prompt ou comparar versões
de prompt.

### 7.5 JSON Schema

O serviço deverá reutilizar:

```python
governance_agent_output_schema()
```

O schema não deverá ser duplicado manualmente em outro módulo.

### 7.6 Fake Provider

Os testes utilizarão um provider controlado, conceitualmente:

```python
class FakeLLMProvider:
    def __init__(self, response: str):
        self.response = response
        self.last_prompt = None
        self.last_schema = None

    def generate(
        self,
        *,
        prompt: str,
        response_schema: dict[str, object],
    ) -> str:
        self.last_prompt = prompt
        self.last_schema = response_schema
        return self.response
```

### 7.7 Alternativas consideradas

#### Provider específico de OpenAI desde já

Rejeitado neste incremento, pois introduziria SDK, credencial e detalhes de
fornecedor antes de a arquitetura da fronteira estar testada.

#### Função global que chama diretamente uma API

Rejeitada, pois mistura transporte, fornecedor e domínio.

#### Interface extremamente genérica para qualquer tipo de IA

Rejeitada por representar abstração prematura.

### 7.8 Contratos de dados

Contratos reutilizados sem alteração:

- `MaterialRecord`;
- `GovernanceDecision`;
- `IssueType`;
- `GovernanceAgentOutput`;
- JSON Schema de `GovernanceAgentOutput`.

### 7.9 Arquivos previstos

- `src/agent_lab/llm_provider.py` — definir o `LLMProvider`;
- `src/agent_lab/llm_service.py` — construir o prompt e coordenar provider, schema e parsing;
- `tests/test_llm_service.py` — Fake Provider e testes do fluxo;
- `docs/specs/0015_llm_execution_boundary.md` — esta especificação.

Arquivos opcionais, somente se necessário:

- `src/agent_lab/__init__.py`;
- `CHANGELOG.md`.

Não são previstas alterações em:

- `src/agent_lab/domain.py`;
- `src/agent_lab/validator.py`;
- regras determinísticas existentes;
- datasets sintéticos existentes.

## 8. Estratégia de testes e TDD

### 8.1 Vermelho

O primeiro teste deverá representar um fluxo que atualmente não existe:

```python
def test_analyze_material_returns_validated_output():
    provider = FakeLLMProvider(valid_json)
    result = analyze_material(material, provider)

    self.assertIsInstance(result, GovernanceAgentOutput)
```

Antes da implementação, o teste deve falhar porque `LLMProvider` e
`analyze_material()` ainda não existem.

### 8.2 Verde

Implementar a menor solução capaz de:

1. construir o prompt;
2. exportar o schema existente;
3. chamar `provider.generate(...)`;
4. validar o retorno;
5. retornar `GovernanceAgentOutput`.

### 8.3 Regressão

Após os novos testes ficarem verdes:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### 8.4 Testes previstos

- `T-01` — fluxo válido retorna `GovernanceAgentOutput`;
- `T-02` — provider recebe os campos do material no prompt;
- `T-03` — provider recebe o JSON Schema esperado;
- `T-04` — JSON malformado é rejeitado;
- `T-05` — JSON estruturalmente inválido é rejeitado;
- `T-06` — testes não dependem de fornecedor real;
- `T-07` — regressão dos 24 testes existentes.

## 9. Gates de qualidade

Antes do Pull Request:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
git diff --check
git status -sb
```

Quando houver arquivos staged:

```powershell
git diff --cached --check
git diff --cached --stat
```

Critérios mínimos:

- todos os testes existentes e novos aprovados;
- CI `Testes / Python 3.11` aprovada;
- required status check satisfeito;
- nenhuma chamada de rede nos testes;
- nenhuma dependência de chave de API;
- nenhum SDK de provedor adicionado;
- nenhum segredo versionado;
- alteração limitada aos arquivos previstos;
- nenhuma regra determinística PDM/BOM alterada;
- documentação e código coerentes;
- riscos e limitações registrados no Pull Request.

## 10. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Abstração prematura ficar genérica demais | Média | Médio | Manter `LLMProvider` mínimo |
| Contrato incorporar detalhes de fornecedor | Média | Alto | Não importar SDKs nem parâmetros específicos |
| Fake Provider gerar falsa confiança sobre LLM real | Alta | Médio | Documentar que o Fake valida arquitetura, não semântica |
| Prompt inicial ser insuficiente para modelo real | Alta | Médio | Avaliar prompts em incremento posterior |
| Schema ser duplicado e divergir | Baixa | Alto | Reutilizar `governance_agent_output_schema()` |
| JSON válido ser semanticamente incorreto | Alta | Alto | Manter revisão humana |
| Testes dependerem de rede | Baixa | Alto | Utilizar exclusivamente Fake Provider |

### Limitações conhecidas após o incremento

Mesmo após a conclusão:

- nenhuma LLM real terá sido chamada;
- não haverá evidência de qualidade semântica de modelos externos;
- não haverá medição de precisão/recall da camada LLM;
- não haverá retry ou fallback;
- não haverá gestão de secrets;
- não haverá contagem de tokens ou custos;
- não haverá RAG;
- não haverá tool calling;
- o prompt será apenas uma primeira versão estrutural;
- validação estrutural não equivale a validação factual.

## 11. Plano de reversão

Em caso de regressão:

1. não integrar o Pull Request enquanto os checks estiverem falhando;
2. identificar se o problema está no contrato, serviço ou testes;
3. corrigir na branch da Issue;
4. se já incorporado, reverter o Pull Request;
5. remover os módulos novos da fronteira de LLM;
6. preservar `llm_schema.py`, `domain.py` e o baseline determinístico;
7. executar novamente toda a suíte.

## 12. Versionamento e release

### Impacto SemVer

`MINOR`

Justificativa: a Issue adiciona uma nova capacidade compatível ao laboratório —
uma fronteira executável para providers de LLM — sem quebrar os contratos
existentes.

### Publicação prevista

- versão planejada: `Unreleased`;
- criação de tag: não;
- criação de GitHub Release: não;
- atualização do `CHANGELOG.md`: sim, caso a política atual registre novas capacidades funcionais.

## 13. Critérios de aceite

- [x] existe um contrato explícito `LLMProvider`;
- [x] o contrato não depende de SDK específico;
- [x] existe uma fronteira que recebe `MaterialRecord`;
- [x] o prompt é construído de forma determinística;
- [x] os campos relevantes do material são fornecidos ao provider;
- [x] o JSON Schema existente é fornecido ao provider;
- [x] o schema não é duplicado manualmente;
- [x] o provider retorna JSON bruto;
- [x] JSON bruto obrigatoriamente atravessa `parse_governance_agent_output()`;
- [x] JSON válido produz `GovernanceAgentOutput`;
- [x] JSON malformado é rejeitado;
- [x] JSON estruturalmente inválido é rejeitado;
- [x] existe Fake/Stub Provider nos testes;
- [x] os testes não utilizam internet;
- [x] os testes não utilizam API key;
- [x] nenhum SDK real de LLM é adicionado neste incremento;
- [x] nenhuma chamada real a LLM ocorre;
- [x] os 24 testes anteriores continuam aprovados;
- [x] os novos testes da Issue #15 estão aprovados;
- [ ] a CI `Testes / Python 3.11` está aprovada no Pull Request;
- [ ] nenhum segredo, credencial ou dado proprietário foi incluído;
- [ ] nenhuma regra determinística PDM/BOM foi alterada;
- [ ] riscos e limitações estão registrados;
- [ ] a decisão final de governança permanece humana;
- [ ] o Pull Request referencia a Issue #15 e esta SPEC.

## 14. Questões em aberto

1. **Local do Fake Provider**
   - manter dentro de `tests/test_llm_service.py`, salvo evidência de reutilização.

2. **Formato final do prompt**
   - primeira versão simples e determinística;
   - otimização e versionamento de prompts ficam fora desta Issue.

3. **Tratamento de erro do provider**
   - nesta Issue, erros de parsing/validação serão propagados;
   - retry, fallback e classificação de erros ficam para quando houver provider real.

4. **Consistência entre `material_id` de entrada e saída**
   - não será adicionada regra semântica nova nesta primeira fronteira;
   - avaliar em Issue posterior, salvo decisão antes do início da implementação.

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `2026-08-09` | Criar fronteira antes de integrar provider real | Reduz acoplamento e permite testar sem rede ou credenciais | Jakson Pascoal |
| `2026-08-09` | Utilizar contrato mínimo de provider | Evita abstração prematura e dependência de fornecedor | Jakson Pascoal |
| `2026-08-09` | Utilizar Fake/Stub Provider no TDD | Mantém testes determinísticos, rápidos e sem custo | Jakson Pascoal |
| `2026-08-09` | Reutilizar `governance_agent_output_schema()` | Mantém uma única fonte de verdade para o contrato de saída | Jakson Pascoal |
| `2026-08-09` | Reutilizar `parse_governance_agent_output()` | Garante que toda resposta externa atravesse a fronteira Pydantic | Jakson Pascoal |
| `2026-08-09` | Validar TDD RED com ausência de `llm_service` | O novo teste falhou com `ModuleNotFoundError`, comprovando que a fronteira ainda não existia | Jakson Pascoal |
| `2026-08-09` | Implementar `LLMProvider` como `Protocol` mínimo | Mantém desacoplamento de fornecedores e facilita Fake Provider | Jakson Pascoal |
| `2026-08-09` | Implementar `GovernanceLLMService` mínimo | Coordena prompt, schema, provider e parsing sem ampliar o escopo | Jakson Pascoal |
| `2026-08-09` | Validar GREEN local com 31 testes | Os 24 testes anteriores e os 7 novos foram aprovados | Jakson Pascoal |

## 16. Rastreabilidade

Esta especificação implementa a Issue:

```text
#15 — [FEATURE] Criar fronteira de execução da LLM para análise de materiais
```

O Pull Request deverá referenciar:

```text
Closes #15
```

e identificar explicitamente:

```text
SPEC-0015
docs/specs/0015_llm_execution_boundary.md
```
