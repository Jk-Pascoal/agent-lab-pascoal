# Dados

## `synthetic/materials.csv`

Conjunto inteiramente sintético criado para o aprendizado. Ele contém exemplos de:

- registros adequados;
- descrições incompletas;
- unidades suspeitas;
- campos ausentes;
- abreviações;
- possíveis duplicidades.

O campo `expected_issue` é o rótulo didático utilizado para validar o comportamento do sistema. Ele não deverá ser oferecido ao agente como variável de entrada.

## Regras de uso

- Não substituir este arquivo por dados empresariais sem anonimização.
- Não versionar chaves de API ou credenciais.
- Preservar uma separação entre dados de treino, validação e teste quando modelos forem introduzidos.

