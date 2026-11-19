# Registro de Testes

Comando (com os contêineres rodando):

```bash
docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v
```

## Execução de 18/11/2026 (3) — branch `ollama` (assistente de IA)

| Arquivo | Testes | Resultado |
|---|---|---|
| `backend/tests/test_scanner.py` | 82 | aprovados |
| `backend/tests/test_parser.py` | 59 | aprovados |
| `backend/tests/test_api_etapa4.py` | 15 | aprovados |
| `backend/tests/test_ia.py` | 26 | aprovados (Ollama simulado) |
| `tests_interface/test_interface.py` | 16 | aprovados com um Ollama simulado no ar; os testes de IA e de análise também passaram com o Ollama desligado |

**Pendente:** teste com o Llama 3.2 real no Docker (instalação do modelo, explicação de nó e de erro, tempo de
resposta, volume persistente após `docker compose down` e `up`).

## Execução de 18/11/2026 (2) — requisitos completos da Etapa 4

| Arquivo | Testes | Resultado |
|---|---|---|
| `backend/tests/test_scanner.py` | 82 | 82 aprovados |
| `backend/tests/test_parser.py` | 59 | 59 aprovados |
| `backend/tests/test_api_etapa4.py` | 15 | 15 aprovados |
| `tests_interface/test_interface.py` | 13 | 13 aprovados |
| **Total** | **169** | **169 aprovados, 0 falhas** |

- Backend: Python 3.13 e pytest 8, fora do Docker. Interface: Playwright com Chrome, com o backend Flask e o frontend
  servidos localmente (sem nginx).
- Novos testes do parser: exemplos do enunciado (`10 + 5 * 2`, `20 - 5 - 3`, `(10 + 5) * 2`), regra gramatical de
  cada nó, posições inicial e final, consumo de todos os tokens pelo parser, posições dos nós iguais às da tabela,
  mensagens que citam a construção aberta, regra violada no erro e ausência de detalhes internos nas mensagens.
- Novos testes de endpoint: blocos `lexico` e `sintatico` da resposta e rota `GET /api/gramatica`.
- Defeito encontrado e corrigido: com o registro da regra em análise, cada nível de aninhamento passou a usar mais
  quadros de pilha e o caso de 150 parênteses estourava a recursão do Python antes do limite de 100 níveis. Corrigido
  elevando o limite de recursão no parser e tratando `RecursionError` com mensagem didática (caso CT-53).

**Pendente:** repetir no ambiente Docker (`docker compose up -d --build` e
`docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v`) e validar o fluxo completo pela interface em
`http://localhost:8080`, registrando o resultado aqui.

## Execução de 18/11/2026 (1) — revisão da Etapa 3 e Etapa 4

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
