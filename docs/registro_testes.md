# Registro de Testes

Comando (com os contêineres rodando):

```bash
docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v
```

## Execução de 23/11/2026 — ambiente Docker real, pelo navegador

Aplicação rodando no computador do aluno com `docker compose` (frontend nginx em `localhost:8080`, backend Flask em
`localhost:5000`, Ollama com `llama3.2` instalado, sem GPU). Testes executados no Chrome, na interface e na API reais,
com a versão da `main` que contém zoom, passo a passo, código classificado e assistente de IA.

### Fluxo completo com todos os exemplos da interface (18)

| Exemplo | Léxica | Sintática | Tokens | Nós da AST | Erro (posição) | Status |
|---|---|---|---|---|---|---|
| Atribuição simples | ok | ok | 3 | 4 | — | aprovado |
| Precedência: 10 + 5 * 2 | ok | ok | 7 | 8 | — | aprovado |
| Associatividade: 20 - 5 - 3 | ok | ok | 7 | 8 | — | aprovado |
| Parênteses: (10 + 5) * 2 | ok | ok | 9 | 8 | — | aprovado |
| Precedência e parênteses | ok | ok | 22 | 21 | — | aprovado |
| Condicional if/else | ok | ok | 18 | 14 | — | aprovado |
| Repetição while | ok | ok | 17 | 16 | — | aprovado |
| Função com return | ok | ok | 24 | 17 | — | aprovado |
| Programa combinado | ok | ok | 49 | 41 | — | aprovado |
| Caractere não reconhecido | erro | não executada | 2 | — | 1:5 | aprovado |
| Número malformado | erro | não executada | 2 | — | 1:9 | aprovado |
| Erro léxico + código válido | erro | não executada | 7 | — | 1:7 | aprovado |
| Falta ':' no if | ok | erro | 7 | — | 1:9 | aprovado |
| Parêntese não fechado | ok | erro | 7 | — | 1:14 | aprovado |
| Operadores consecutivos | ok | erro | 6 | — | 1:9 | aprovado |
| else sem if | ok | erro | 5 | — | 1:1 | aprovado |
| Indentação inesperada | ok | erro | — | — | 2:1 ("aumento de indentação") | aprovado |
| Bloco ausente (fim inesperado) | ok | erro | — | — | 1:14 ("terminou antes de concluir o while iniciado na linha 1") | aprovado |

Em todos os válidos a mensagem informou que o parser consumiu todos os tokens (por exemplo, "7 de 7").

### Interface

| Verificação | Resultado observado | Status |
|---|---|---|
| AST de `resultado = 10 + 5 * 2` | Programa › Atribuicao(=) › Identificador(resultado) › OperacaoBinaria(+) › LiteralInteiro(10) › OperacaoBinaria(*) › LiteralInteiro(5) › LiteralInteiro(2): `*` abaixo de `+` | aprovado |
| Clique no nó `*` | editor seleciona `5 * 2`; tabela destaca o token `*` (linha 1, coluna 20); painel mostra a regra `termo = fator { ( "*" \| "/" ) fator }` e o trecho 1:18–1:22 | aprovado |
| Posições dos nós × tabela de tokens | os 7 nós (exceto Programa) têm posição presente na tabela | aprovado |
| Recolher / expandir tudo | todos os nós fechados / todos abertos | aprovado |
| Filtro por tipo (LiteralInteiro) | 3 destacados, 5 esmaecidos | aprovado |
| Passo a passo | 8 passos; o último conclui `Programa`; nenhum nó oculto ao final | aprovado |
| Visão gráfica e zoom | 8 nós; "ajustar à tela" 552 px num quadro de 556 px; 100% → 596 px; − → 477 px; + + → 745 px | aprovado |
| Campo vazio | aviso "Digite um código ou escolha um exemplo antes de analisar." | aprovado |
| 5400 caracteres | contador vermelho "5400 / 5000" e aviso de limite; análise não enviada | aprovado |

### API (backend no contêiner)

| Verificação | Resultado observado | Status |
|---|---|---|
| Código válido | HTTP 200; campos `ast, erros, etapas, lexico, sintatico, sucesso, tokens` | aprovado |
| Erro sintático | HTTP 200; `ast` nula; `ERRO_SINTATICO` 1:9, regra `se` | aprovado |
| Dois erros léxicos (`a = @` / `b = $`) | 2 erros (1:5 e 2:5), 7 tokens, parser não executado | aprovado |
| Vazio / só espaços / 5001 caracteres / não texto / sem JSON | HTTP 400 nos cinco casos, com mensagem | aprovado |
| Só comentário | HTTP 200, sucesso, `Programa` sem filhos | aprovado |
| 50 / 150 níveis de parênteses | 50: sucesso; 150: "Aninhamento excede o limite de 100 níveis." | aprovado |
| Quebras de linha `\r\n` | sucesso | aprovado |
| `GET /api/gramatica` | símbolo inicial `programa`, 17 não terminais | aprovado |

### Assistente de IA (Llama 3.2 real, sem GPU)

| Verificação | Tempo | Resultado | Status |
|---|---|---|---|
| `GET /api/ia/status` | — | disponível, `llama3.2` instalado | aprovado |
| Explicar o nó `*` | 51 s (1ª resposta, com carregamento) | citou posição, pai, filhos e a regra `termo` corretamente; chamou o próprio nó de "fator" (erro conceitual) | aprovado com ressalva |
| Entender o erro de `if x > 0` | 33 s | explicou a falta de `:` e a correção; disse que o bloco do if fica "entre chaves {}" (erro conceitual) | aprovado com ressalva |
| Explicar o token `if` | 36 s | explicou palavra reservada e a função do `if` | aprovado |
| Professor virtual: "Qual a diferença entre AST e árvore de derivação?" | 49 s | resposta conceitual genérica; traduziu AST como "Árvore de Estrutura" | aprovado com ressalva |

O tempo esgotado observado antes (limite de 180 s sem streaming) não ocorreu após a mudança para streaming e
contexto enxuto. As ressalvas confirmam que a IA pode errar conceitos e que o resultado oficial é o do compilador.

### Pendente

- Rodar a suíte automatizada dentro do contêiner e anotar aqui o total:
  `docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v` (esperado: 190 aprovados).
- Testar a interface em tela de celular no navegador real (no ambiente de desenvolvimento passou em 390 px).
- Persistência do volume do Ollama após `docker compose down` e `up` (o modelo não deve precisar de novo `pull`).

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
