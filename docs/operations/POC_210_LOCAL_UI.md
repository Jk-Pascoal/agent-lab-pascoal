# Issue #210 — jornada operacional local (PoC sintética)

**Estado:** implementação experimental em PR, sem alegação de release ou aceite industrial.

## Executar em três passos

Na raiz do repositório, com Python 3.11+:

1. Instalar: python -m pip install -e .
2. Iniciar: python -m agent_lab.poc_local_ui
3. Abrir: http://127.0.0.1:8765/

Importar a fixture sintética tests/fixtures/poc_204_catalog_synthetic_v1.csv e clicar em
**Executar diagnóstico verificado**. Filtrar recomendações REVIEW/REJECT, inspecionar
evidências e baixar relatório JSON, manifesto SHA-256 e triagem CSV.

## Fronteiras de segurança

- Servidor somente em 127.0.0.1; sem ERP, banco remoto, LLM, SSO ou dados reais.
- Arquivos sintéticos ou expressamente autorizados, máximo 256 KiB e 200 materiais.
- Token CSRF local, Host e Origin locais; sem nomes de arquivo fornecidos pelo usuário.
- Pipeline #204 real: adaptador CSV, diagnóstico, exportador JSON/manifesto,
  verificador fail-closed e triagem independente.
- A UI mantém dados em diretório temporário por processo; Ctrl+C encerra e descarta.
- source_row e source_sha256: UNAVAILABLE; HumanReview: NOT_RECORDED.
- Manifesto prova integridade dos bytes do relatório, não origem do CSV ou
  durabilidade em power-loss. Sem alegação de GT, recall, 100 mil SKUs ou produção.
- Interface web local ainda exige review de segurança e teste manual antes de piloto.

## Testes

Runner: python -m unittest discover -s tests -v

O teste tests/test_poc_local_ui.py usa a fixture CSV real via HTTP local, verifica
relatório/manifesto/triagem e falhas de manifesto ausente, CSV inválido,
upload excessivo, token, origem e Host externos.

**Não alterar:** T02 FROZEN, GT, SR-001/B2, D-03/D-04 nem os marcos históricos.
