# Casos de teste — Etapa 4

Casos definidos **antes** da interpretação dos resultados. Qualquer ajuste posterior deve ser registrado na seção
"Histórico de alterações" ao final, com a justificativa.

- **Origem:** todos os casos foram elaborados pelo autor a partir da gramática documentada no README, salvo indicação.
- **Execução automatizada:** `docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v`
- **Registro dos resultados:** a coluna "Status" será preenchida na Etapa 6 (aprovado / reprovado / pendente), junto com o
  resultado observado, o defeito encontrado e a correção realizada (ver `registro_testes.md`).
- **Arquivo de teste:** `backend/tests/test_parser.py` (P), `backend/tests/test_api_etapa4.py` (A),
  `backend/tests/test_scanner.py` (S, regressão da Etapa 3).

## 1. Casos válidos

| ID | Entrada | Resultado esperado | Análise | Critério | Teste |
|---|---|---|---|---|---|
| CT-01 | `x = 10` | 3 tokens; AST `Programa → Atribuicao(=) → [Identificador x, LiteralInteiro 10]`; sem erros | Léxica + sintática | Correção sintática, correção da AST | P `test_ct01` |
| CT-02 | `x = 1 + 2 * 3` | `*` é filho do `+` (precedência) | Sintática | Correção da AST | P `test_ct02` |
| CT-03 | `x = (1 + 2) * 3` | `+` é filho do `*`; parênteses não viram nós | Sintática | Correção da AST | P `test_ct03` |
| CT-04 | `x = 10 - 3 - 2` | associatividade à esquerda: `(10 - 3) - 2` | Sintática | Correção da AST | P `test_ct04` |
| CT-05 | `x = -3.5` | `OperacaoUnaria(-) → LiteralReal 3.5` | Léxica + sintática | Correção léxica e da AST | P `test_ct05` |
| CT-06 | `ok = x >= 10` | `OperacaoRelacional(>=)` | Sintática | Correção sintática | P `test_ct06` |
| CT-07 | `if x > 0:` + bloco | nó `Se` com condição e `Bloco(então)` | Sintática | Correção sintática | P `test_ct07` |
| CT-08 | `if`/`else` | `Se` com `Bloco(então)` e `Bloco(senão)` | Sintática | Correção sintática | P `test_ct08` |
| CT-09 | `while i < 3:` + bloco | nó `Enquanto` com condição e `Bloco(corpo)` | Sintática | Correção sintática | P `test_ct09` |
| CT-10 | `while` contendo `if` e atribuição | blocos aninhados na ordem correta | Sintática | Correção da AST | P `test_ct10` |
| CT-11 | `def soma(a, b): return a + b` | `Funcao(soma)`, `Parametros[a, b]`, `Retorno` | Sintática | Correção sintática | P `test_ct11` |
| CT-12 | Programa combinado (função, atribuições, while, if/else, chamadas) | 5 comandos de topo na ordem do código | Léxica + sintática | Fluxo completo | P `test_ct12` |
| CT-13 | `x = 1 + 2` | posição do nó `+` igual à do token `+` | Léxica + sintática | Consistência entre visualizações | P `test_ct13` |

## 2. Erros léxicos

| ID | Entrada | Resultado esperado | Análise | Critério | Teste |
|---|---|---|---|---|---|
| CT-40 | `x = 12abc` | 1 erro léxico "Literal numérico malformado", linha 1, coluna 5 | Léxica | Detecção de erros | P `test_ct40` |
| CT-41 | `x = "abc` | 1 erro léxico "String não fechada" | Léxica | Detecção de erros | P `test_ct41` |
| CT-42 | `x = @` + `y = 2` (linha 2 válida) | erro léxico; parser **não** executado; `etapas.sintatica = "nao_executada"`; `ast = null` | Léxica + decisão de projeto | Detecção de erros | P `test_ct42` |
| CT-43 | `x = @` | `Caractere não reconhecido: '@'` (formato da Etapa 3 preservado) | Léxica | Regressão | S `test_erro_lexico`, A `test_erro_lexico_mantem_formato_da_etapa3` |

Comentário não fechado: **não se aplica**, pois Python só tem comentários de linha (`#`), que terminam na quebra de linha.

## 3. Erros sintáticos

Python não usa `;` nem `}`; os casos equivalentes são a falta de `:`, a falta de `)` e a indentação incorreta.

| ID | Entrada | Resultado esperado | Análise | Critério | Teste |
|---|---|---|---|---|---|
| CT-20 | `if x > 0` (sem `:`) | esperado `':' ao final do if`, encontrado fim da linha; linha 1, coluna 9 | Sintática | Detecção de erros, clareza das mensagens | P `test_ct20` |
| CT-21 | `print(1` | esperado `')'` | Sintática | Detecção de erros | P `test_ct21` |
| CT-22 | `x = ` | esperado operando, encontrado fim da linha | Sintática | Detecção de erros | P `test_ct22` |
| CT-23 | `else:` sem `if` | mensagem "'else' sem 'if' correspondente" | Sintática | Clareza das mensagens | P `test_ct23` |
| CT-24 | `x = 1 + * 2` | encontrado `'*'`, coluna 9 | Sintática | Detecção de erros | P `test_ct24` |
| CT-25 | `if = 5` | dica: palavra reservada não pode ser nome | Sintática | Clareza das mensagens | P `test_ct25` |
| CT-26 | `if x > 0:` no fim do código | encontrado "o fim do código" | Sintática | Detecção de erros | P `test_ct26` |
| CT-27 | linha recuada sem bloco | "Indentação inesperada", linha 2 | Sintática | Detecção de erros | P `test_ct27` |
| CT-28 | recuo que não volta a um nível anterior | "Indentação inconsistente", linha 3 | Sintática | Detecção de erros | P `test_ct28` |
| CT-29 | `x = a < b < c` | "Comparações encadeadas ... não são suportadas" | Sintática | Indicação de limitações | P `test_ct29` |
| CT-30 | `for i in x:` | "A estrutura 'for' não é suportada nesta versão" | Sintática | Indicação de limitações | P `test_ct30` |
| CT-31 | `x = 1 +` | erro com os campos do contrato (`esperado`, `encontrado`, `dica`, ...) e `ast = null` | Sintática | Contrato de comunicação | P `test_erro_sintatico_tem_campos_do_contrato` |

## 4. Erros semânticos (previstos para a Etapa 5 — ainda não executáveis)

| ID | Entrada | Resultado esperado | Análise |
|---|---|---|---|
| CT-60 | `y = x + 1` sem atribuição anterior de `x` | "Variável 'x' usada antes de receber valor" | Semântica |
| CT-61 | `r = soma(1)` com `def soma(a, b)` | "Número de argumentos incompatível" | Semântica |
| CT-62 | `r = f(2)` sem `def f` (exceto `print`) | "Função 'f' não definida" | Semântica |
| CT-63 | `return 1` fora de função | "'return' fora de uma função" | Semântica |
| CT-64 | `x = "a" + 1` | "Tipos incompatíveis na operação '+'" (somente se a verificação de tipos entrar no escopo) | Semântica |

Redeclaração de identificador: **não se aplica** a Python, em que a reatribuição é permitida.

## 5. Casos de borda e validação de entrada

| ID | Entrada | Resultado esperado | Análise | Teste |
|---|---|---|---|---|
| CT-50 | apenas comentários | sucesso; `Programa` sem filhos | Léxica + sintática | P `test_ct50` |
| CT-51 | `print(1)` (um único comando) | AST com 1 comando | Sintática | P `test_ct51` |
| CT-52 | 50 parênteses aninhados | AST válida | Sintática | P `test_ct52` |
| CT-53 | 150 parênteses aninhados | erro "Aninhamento excede o limite de 100 níveis" | Sintática (segurança) | P `test_ct53` |
| CT-54 | quebras de linha `\r\n` (Windows) | AST válida | Léxica + sintática | P `test_ct54` |
| CT-55 | campo vazio | HTTP 400 "O código não pode estar vazio." | Validação de entrada | A `test_codigo_vazio` |
| CT-56 | apenas espaços e tabulações | HTTP 400 | Validação de entrada | A `test_codigo_so_com_espacos` |
| CT-57 | mais de 5000 caracteres | HTTP 400 com mensagem de limite | Validação de entrada | A `test_codigo_acima_do_limite` |
| CT-58 | `codigo` não textual (`123`) | HTTP 400 | Validação de entrada | A `test_codigo_nao_texto` |
| CT-59 | corpo sem JSON | HTTP 400 | Validação de entrada | A `test_requisicao_sem_json` |

## 6. Testes manuais da interface (fluxo completo)

Fluxo: inserir código → solicitar análise → visualizar tokens → visualizar AST ou erros.

| ID | Ação | Resultado esperado | Status |
|---|---|---|---|
| CM-01 | Selecionar cada exemplo do menu e clicar em "Analisar" | resultado coerente com o grupo do exemplo (válido, erro léxico ou erro sintático) | Etapa 6 |
| CM-02 | Clicar em um nó da AST | o token correspondente fica destacado na tabela e o trecho é selecionado no editor | Etapa 6 |
| CM-03 | Clicar em "Linha X, coluna Y" de um erro | o editor seleciona a posição do erro | Etapa 6 |
| CM-04 | Alternar entre AST hierárquica e gráfica; expandir/recolher | as duas visões mostram a mesma árvore | Etapa 6 |
| CM-05 | Usar só o teclado (Tab, Enter, Ctrl+Enter, Esc+Tab para sair do editor) | todas as ações são possíveis sem mouse | Etapa 6 |
| CM-06 | Abrir em largura de 390 px (celular) | layout em uma coluna, sem rolagem horizontal da página | Etapa 6 |
| CM-07 | Botões A− / A+ | fonte muda entre 12 e 24 px | Etapa 6 |
| CM-08 | Digitar mais de 5000 caracteres | contador fica vermelho e a análise é bloqueada com aviso | Etapa 6 |
| CM-09 | Ambiente limpo: `git clone` + `docker compose up -d --build` | interface em `localhost:8080` e API em `localhost:5000` funcionando | Etapa 6 |

## Histórico de alterações

| Data | Alteração | Justificativa |
|---|---|---|
| 2026-11 | Versão inicial (Etapa 4) | — |
