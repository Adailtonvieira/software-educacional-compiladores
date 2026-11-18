# Registro de Testes

Comando (com os contêineres rodando):

```bash
docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v
```

## Execução de 18/11/2026 — revisão da Etapa 3 e Etapa 4

| Arquivo | Testes | Resultado |
|---|---|---|
| `tests/test_scanner.py` | 82 | 82 aprovados |
| `tests/test_parser.py` | 34 | 34 aprovados |
| `tests/test_api_etapa4.py` | 11 | 11 aprovados |
| **Total** | **127** | **127 aprovados, 0 falhas** |

- Ambiente desta execução: Python 3.13 e pytest 8, fora do Docker. Repetir no contêiner (Python 3.11) com o comando
  acima e anotar o resultado aqui.
- Os números contam cada combinação dos testes parametrizados (por exemplo, um teste por palavra reservada).

### O que a suíte do scanner verifica

- Campos do token (`tipo`, `lexema`, `linha`, `coluna`) e do erro (`tipo`, `lexema`, `linha`, `coluna`, `mensagem`).
- Cada palavra reservada, e que prefixos como `iffy` e `true` são identificadores.
- Identificadores com `_` e dígitos.
- Literais inteiros, reais e de texto (aspas simples, duplas, vazias e com `#` dentro).
- Operadores de dois caracteres como um único token, inclusive sem espaços (`a<=b`).
- Cada delimitador.
- Comentários ignorados, inclusive com símbolos inválidos dentro; tabulação e `\r\n` como espaço.
- Linha e coluna em uma e em várias linhas, com linhas em branco e após comentário.
- Posição exata do erro; acúmulo de vários erros sem interromper a análise; tokens válidos reconhecidos depois de um
  erro; 13 símbolos fora do escopo.
- Número malformado (`12abc`) e string não fechada, cada um como um único erro.
- Caractere Unicode fora do escopo (`π`).
- Contagem por categoria de um programa completo e código vazio.

### Correções feitas nesta revisão

- Removido `backend/test_api.py`, teste da Etapa 2 que esperava o campo `mensagem` (retirado da API na Etapa 3) e
  falharia se executado. Os casos dele (código vazio, só espaços, sem JSON) estão em `tests/test_api_etapa4.py`.
- Suíte do scanner ampliada de 3 para 82 testes.

### Testes de regressão (Etapas 1 a 3)

- Os três testes originais do scanner foram mantidos sem alteração no início de `tests/test_scanner.py`.
- O formato da resposta da Etapa 3 (`sucesso`, `tokens`, `erros`) é verificado em `test_contrato_etapa3_preservado` e
  `test_erro_lexico_mantem_formato_da_etapa3`.
- A interface foi verificada no Chrome com todos os exemplos do menu.

## Etapa 3 (registro original)

- Resultado: 4 testes aprovados (tokens básicos, palavras reservadas, erro léxico, requisição vazia).
- Regressão: o ambiente Docker subiu; a comunicação frontend-backend funcionou; a interface não quebrou com entradas
  inválidas.
