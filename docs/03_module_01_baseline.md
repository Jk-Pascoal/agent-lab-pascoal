# Módulo 1 — Baseline determinístico

## Por que começar sem LLM

Um sistema de IA só demonstra valor quando supera uma referência mensurável. O baseline deste módulo usa apenas regras explícitas e Python padrão.

Ele permite responder:

- quais defeitos podem ser resolvidos com regras simples;
- onde as regras se tornam frágeis;
- qual ganho um LLM ou embeddings deverão demonstrar;
- qual custo e risco adicionais são aceitáveis.

## Fluxo

1. Ler o material.
2. Verificar campos obrigatórios.
3. Validar unidade e status.
4. Procurar termos ambíguos.
5. Verificar atributos técnicos por família.
6. Comparar com materiais anteriores.
7. Produzir uma recomendação.
8. Comparar o resultado com o rótulo esperado.

## Decisões

| Condição | Recomendação |
|---|---|
| Regra impeditiva | `REJECT` |
| Alerta ou possível duplicidade | `REVIEW` |
| Nenhum problema detectado | `APPROVE` |

## Limitações conscientes

- abreviações precisam estar previamente cadastradas;
- regras técnicas são específicas para famílias conhecidas;
- descrições semanticamente semelhantes podem escapar;
- regras não compreendem contexto;
- novos padrões exigem manutenção manual.

Essas limitações formarão a justificativa experimental para os próximos módulos.

## Dois conjuntos, duas perguntas

- `materials.csv`: as regras reconhecem os exemplos usados no desenvolvimento?
- `materials_challenge.csv`: as mesmas regras generalizam para novas grafias e exceções?

Uma pontuação perfeita no primeiro conjunto não constitui evidência de
generalização. Por isso o relatório separa:

- **correspondência exata:** todos os alertas previstos coincidem com o rótulo;
- **cobertura do rótulo:** o defeito esperado aparece entre os alertas;
- **precisão e recall de duplicidades:** qualidade específica da busca por
  materiais repetidos.

## Primeiro experimento

| Conjunto | Registros | Correspondência exata | Precisão de duplicidade | Recall de duplicidade |
|---|---:|---:|---:|---:|
| Desenvolvimento | 20 | 100% | 100% | 100% |
| Desafio | 10 | 80% | 0% | 0% |

O conjunto de desafio expôs dois erros:

1. `ACOPL FLEX 95` não foi associado a `ACOPLAMENTO ELASTICO TAM 95`.
2. Um fluido fornecido em balde foi tratado como unidade suspeita, embora
   `PC` possa representar corretamente um recipiente.

O resultado demonstra que regras são fortes em situações previamente
enumeradas, mas frágeis diante de sinonímia e contexto. Essas duas falhas serão
casos de teste para as futuras abordagens com embeddings e LLM.
