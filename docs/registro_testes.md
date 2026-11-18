# Registro de Testes

## Etapa 4 — Parser e AST

- **Comando:** `docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v`
- **Casos planejados:** ver `docs/casos-de-teste.md` (definidos antes da execução formal).
- **Arquivos:** `tests/test_scanner.py` (regressão da Etapa 3), `tests/test_parser.py`, `tests/test_api_etapa4.py`.
- **Execução formal e preenchimento da tabela abaixo:** Etapa 6.

| ID | Entrada | Resultado esperado | Resultado observado | Status | Defeito | Correção |
|---|---|---|---|---|---|---|
| CT-01 | `x = 10` | ver casos-de-teste.md | | pendente | | |
| ... | | | | | | |

## Etapa 3 — Scanner

- **Comando:** `docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v`
- **Resultado:** 4 testes passaram com sucesso (tokens básicos, palavras reservadas, erro léxico, requisição vazia).
- **Falhas encontradas:** nenhuma na execução final.

### Testes de regressão (Etapas 1 e 2)
- O ambiente Docker subiu corretamente.
- A comunicação frontend-backend continua funcionando.
- A interface não quebrou ao inserir entradas inválidas.
