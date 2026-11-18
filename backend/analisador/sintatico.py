"""Análise sintática (parser) — Etapa 4.

Parser descendente recursivo escrito à mão: cada não terminal da gramática
(dicionário ``GRAMATICA`` abaixo) corresponde a um método da classe ``Parser``.
A saída é uma árvore sintática abstrata (AST) serializável em JSON.

Decisões de projeto:
- o parser para no PRIMEIRO erro sintático (sem recuperação), para evitar
  erros em cascata que confundem o estudante;
- parênteses orientam a construção da árvore, mas não viram nós da AST;
- comparações encadeadas (``a < b < c``) são rejeitadas com mensagem própria;
- cada nó registra a regra gramatical que o reconheceu, o token que o
  identifica (``linha``/``coluna``) e o trecho completo (``inicio``/``fim``).
"""

import sys

from .lexico import ErroIndentacao, gerar_tokens_estruturais

MAX_PROFUNDIDADE = 100

SIMBOLO_INICIAL = "programa"

# Fonte única da gramática: usada na documentação, nas mensagens de erro,
# nos nós da AST e devolvida pela rota GET /api/gramatica.
GRAMATICA = {
    "programa": '{ comando } FIM_DE_ARQUIVO',
    "comando": 'comando_simples NOVA_LINHA | se | enquanto | funcao',
    "comando_simples": 'retorno | atribuicao | expressao',
    "atribuicao": 'IDENTIFICADOR "=" expressao',
    "retorno": '"return" [ expressao ]',
    "se": '"if" expressao ":" bloco [ "else" ":" bloco ]',
    "enquanto": '"while" expressao ":" bloco',
    "funcao": '"def" IDENTIFICADOR "(" [ parametros ] ")" ":" bloco',
    "parametros": 'IDENTIFICADOR { "," IDENTIFICADOR }',
    "bloco": 'NOVA_LINHA INDENTACAO comando { comando } DEDENTACAO',
    "expressao": 'aritmetica [ op_relacional aritmetica ]',
    "op_relacional": '"==" | "!=" | "<" | ">" | "<=" | ">="',
    "aritmetica": 'termo { ( "+" | "-" ) termo }',
    "termo": 'fator { ( "*" | "/" ) fator }',
    "fator": '( "+" | "-" ) fator | atomo',
    "atomo": 'IDENTIFICADOR [ "(" [ argumentos ] ")" ] | LITERAL_INTEIRO | LITERAL_REAL '
             '| LITERAL_STRING | "True" | "False" | "(" expressao ")"',
    "argumentos": 'expressao { "," expressao }',
}

OPERADORES_RELACIONAIS = ("==", "!=", "<", ">", "<=", ">=")

_DESCRICAO_ESTRUTURAL = {
    "NOVA_LINHA": "fim da linha",
    "INDENTACAO": "um aumento de indentação",
    "DEDENTACAO": "o fim do bloco indentado",
    "FIM_DE_ARQUIVO": "o fim do código",
}

TOKENS_ESTRUTURAIS = tuple(_DESCRICAO_ESTRUTURAL)


class ErroSintatico(Exception):
    def __init__(self, mensagem, token, esperado, dica=None, regra=None, abertura=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.token = token
        self.esperado = esperado
        self.dica = dica
        self.regra = regra
        self.abertura = abertura


def descrever(token):
    if token["tipo"] in _DESCRICAO_ESTRUTURAL:
        return _DESCRICAO_ESTRUTURAL[token["tipo"]]
    return f"'{token['lexema']}'"


def _pos(linha, coluna):
    return {"linha": linha, "coluna": coluna}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.profundidade = 0
        self.regras = []          # pilha de não terminais em análise (para as mensagens)
        self.ultimo = None        # último token léxico consumido (para a posição final dos nós)
        self.consumidos = []      # tokens léxicos consumidos, na ordem (consistência com a tabela)

    # ---------- utilitários ----------
    def atual(self):
        return self.tokens[self.pos]

    def proximo(self):
        return self.tokens[min(self.pos + 1, len(self.tokens) - 1)]

    def eh(self, tipo, lexema=None, token=None):
        tok = token or self.atual()
        return tok["tipo"] == tipo and (lexema is None or tok["lexema"] == lexema)

    def avancar(self):
        tok = self.atual()
        if tok["tipo"] != "FIM_DE_ARQUIVO":
            self.pos += 1
        if tok["tipo"] not in TOKENS_ESTRUTURAIS:
            self.ultimo = tok
            self.consumidos.append(tok)
        return tok

    def no(self, tipo, token, valor=None, filhos=None, regra=None, inicio=None):
        """Cria um nó. ``token`` é o token que identifica o nó; o fim do trecho
        é o último token consumido até aqui (o nó é criado ao final da regra)."""
        filhos = filhos or []
        if inicio is None:
            inicio = _pos(token["linha"], token["coluna"])
        if self.ultimo is not None:
            fim = _pos(self.ultimo["linha"], self.ultimo["coluna"] + max(len(self.ultimo["lexema"]), 1) - 1)
        else:
            fim = dict(inicio)
        return {
            "tipo": tipo,
            "valor": valor,
            "regra": regra or (self.regras[-1] if self.regras else SIMBOLO_INICIAL),
            "linha": token["linha"],
            "coluna": token["coluna"],
            "inicio": inicio,
            "fim": fim,
            "filhos": filhos,
        }

    def regra_atual(self):
        return self.regras[-1] if self.regras else SIMBOLO_INICIAL

    def erro(self, esperado, dica=None, token=None, abertura=None, construcao=None):
        tok = token or self.atual()
        if tok["tipo"] == "PALAVRA_RESERVADA" and dica is None and "nome" in esperado:
            dica = f"'{tok['lexema']}' é uma palavra reservada e não pode ser usada como nome."
        if tok["tipo"] == "FIM_DE_ARQUIVO" and abertura and construcao:
            mensagem = (f"O código terminou antes de concluir o {construcao} iniciado na linha "
                        f"{abertura['linha']}. Esperado {esperado}.")
        else:
            mensagem = f"Esperado {esperado}, mas foi encontrado {descrever(tok)}."
        raise ErroSintatico(mensagem, tok, esperado, dica, self.regra_atual(), abertura)

    def consumir(self, tipo, lexema=None, esperado=None, dica=None, abertura=None, construcao=None):
        if self.eh(tipo, lexema):
            return self.avancar()
        self.erro(esperado or (f"'{lexema}'" if lexema else tipo), dica, abertura=abertura, construcao=construcao)

    def entrar(self):
        self.profundidade += 1
        if self.profundidade > MAX_PROFUNDIDADE:
            raise ErroSintatico(
                f"Aninhamento excede o limite de {MAX_PROFUNDIDADE} níveis.",
                self.atual(), "menos níveis de aninhamento",
                "Divida a expressão ou o bloco em partes menores.", self.regra_atual(),
            )

    def sair(self):
        self.profundidade -= 1

    def _regra(nome):
        """Decorador: empilha o não terminal enquanto o método é executado."""
        def decorador(metodo):
            def envolvido(self, *args, **kwargs):
                self.regras.append(nome)
                try:
                    return metodo(self, *args, **kwargs)
                finally:
                    self.regras.pop()
            envolvido.__name__ = metodo.__name__
            return envolvido
        return decorador

    # ---------- regras ----------
    @_regra("programa")
    def programa(self):
        comandos = []
        while not self.eh("FIM_DE_ARQUIVO"):
            comandos.append(self.comando())
        inicio = comandos[0]["inicio"] if comandos else _pos(1, 1)
        return self.no("Programa", inicio, None, comandos, inicio=dict(inicio))

    @_regra("comando")
    def comando(self):
        tok = self.atual()
        if self.eh("INDENTACAO"):
            self.erro("um comando", "Indentação inesperada: só recue linhas dentro de if, while ou def.")
        if self.eh("PALAVRA_RESERVADA"):
            lex = tok["lexema"]
            if self.eh("OPERADOR", "=", self.proximo()):
                self.erro("um nome de variável", f"'{lex}' é uma palavra reservada e não pode ser usada como nome de variável.")
            if lex == "if":
                return self.se()
            if lex == "while":
                return self.enquanto()
            if lex == "def":
                return self.funcao()
            if lex == "else":
                raise ErroSintatico(
                    "'else' sem 'if' correspondente.", tok, "um comando",
                    "O else deve ficar alinhado com um if logo acima, depois do bloco do if.", "se",
                )
            if lex == "for":
                raise ErroSintatico(
                    "A estrutura 'for' não é suportada nesta versão.", tok, "um comando suportado",
                    "Use while para repetições.", "comando",
                )
        cmd = self.comando_simples()
        self.consumir("NOVA_LINHA", esperado="o fim da linha (um comando por linha)")
        return cmd

    @_regra("comando_simples")
    def comando_simples(self):
        tok = self.atual()
        if self.eh("PALAVRA_RESERVADA", "return"):
            return self.retorno()
        if self.eh("IDENTIFICADOR") and self.eh("OPERADOR", "=", self.proximo()):
            return self.atribuicao()
        return self.expressao()

    @_regra("retorno")
    def retorno(self):
        tok = self.avancar()  # return
        filhos = [] if self.eh("NOVA_LINHA") else [self.expressao()]
        return self.no("Retorno", tok, None, filhos)

    @_regra("atribuicao")
    def atribuicao(self):
        nome = self.avancar()
        alvo = self.no("Identificador", nome, nome["lexema"])
        self.avancar()  # '='
        valor = self.expressao()
        return self.no("Atribuicao", nome, "=", [alvo, valor])

    @_regra("bloco")
    def bloco(self, rotulo, construcao, abertura):
        inicio = self.atual()
        self.consumir("NOVA_LINHA", esperado=f"o fim da linha após ':' do {construcao}",
                      dica="O corpo deve começar na linha seguinte, indentado.",
                      abertura=abertura, construcao=construcao)
        self.consumir("INDENTACAO", esperado=f"um bloco indentado no corpo do {construcao}",
                      dica="Recue as linhas do corpo (ex.: 4 espaços).",
                      abertura=abertura, construcao=construcao)
        self.entrar()
        comandos = [self.comando()]
        while not self.eh("DEDENTACAO") and not self.eh("FIM_DE_ARQUIVO"):
            comandos.append(self.comando())
        self.consumir("DEDENTACAO", esperado="o fim do bloco")
        self.sair()
        primeiro = comandos[0]
        return self.no("Bloco", primeiro, rotulo, comandos, inicio=dict(primeiro["inicio"]))

    def dois_pontos(self, construcao, abertura):
        self.consumir("DELIMITADOR", ":", esperado=f"':' ao final do {construcao}",
                      dica="Em Python, if, else, while e def terminam com ':'.",
                      abertura=abertura, construcao=construcao)

    @_regra("se")
    def se(self):
        tok = self.avancar()  # if
        abertura = _pos(tok["linha"], tok["coluna"])
        condicao = self.expressao()
        self.dois_pontos("if", abertura)
        filhos = [condicao, self.bloco("então", "if", abertura)]
        if self.eh("PALAVRA_RESERVADA", "else"):
            tok_else = self.avancar()
            ab_else = _pos(tok_else["linha"], tok_else["coluna"])
            self.dois_pontos("else", ab_else)
            filhos.append(self.bloco("senão", "else", ab_else))
        return self.no("Se", tok, None, filhos)

    @_regra("enquanto")
    def enquanto(self):
        tok = self.avancar()  # while
        abertura = _pos(tok["linha"], tok["coluna"])
        condicao = self.expressao()
        self.dois_pontos("while", abertura)
        return self.no("Enquanto", tok, None, [condicao, self.bloco("corpo", "while", abertura)])

    @_regra("funcao")
    def funcao(self):
        tok = self.avancar()  # def
        abertura = _pos(tok["linha"], tok["coluna"])
        nome = self.consumir("IDENTIFICADOR", esperado="o nome da função", abertura=abertura, construcao="def")
        par = self.consumir("DELIMITADOR", "(", esperado="'(' após o nome da função", abertura=abertura, construcao="def")
        params = self.parametros(par) if not self.eh("DELIMITADOR", ")") else \
            self.no("Parametros", nome, None, [], regra="parametros")
        self.consumir("DELIMITADOR", ")",
                      esperado=f"')' para fechar a lista de parâmetros aberta na coluna {par['coluna']}",
                      abertura=abertura, construcao="def")
        self.dois_pontos("def", abertura)
        corpo = self.bloco("corpo", "def", abertura)
        return self.no("Funcao", tok, nome["lexema"], [params, corpo])

    @_regra("parametros")
    def parametros(self, par):
        p = self.consumir("IDENTIFICADOR", esperado="o nome de um parâmetro")
        params = [self.no("Parametro", p, p["lexema"])]
        while self.eh("DELIMITADOR", ","):
            self.avancar()
            p = self.consumir("IDENTIFICADOR", esperado="o nome de um parâmetro após ','")
            params.append(self.no("Parametro", p, p["lexema"]))
        return self.no("Parametros", params[0], None, params)

    @_regra("expressao")
    def expressao(self):
        self.entrar()
        esquerda = self.aritmetica()
        if self.eh("OPERADOR") and self.atual()["lexema"] in OPERADORES_RELACIONAIS:
            op = self.avancar()
            direita = self.aritmetica()
            esquerda = self.no("OperacaoRelacional", op, op["lexema"], [esquerda, direita],
                               inicio=dict(esquerda["inicio"]))
            if self.eh("OPERADOR") and self.atual()["lexema"] in OPERADORES_RELACIONAIS:
                raise ErroSintatico(
                    "Comparações encadeadas (ex.: a < b < c) não são suportadas nesta versão.",
                    self.atual(), "o fim da expressão", "Separe em duas comparações.", "expressao",
                )
        self.sair()
        return esquerda

    @_regra("aritmetica")
    def aritmetica(self):
        esquerda = self.termo()
        while self.eh("OPERADOR", "+") or self.eh("OPERADOR", "-"):
            op = self.avancar()
            direita = self.termo()
            esquerda = self.no("OperacaoBinaria", op, op["lexema"], [esquerda, direita],
                               inicio=dict(esquerda["inicio"]))
        return esquerda

    @_regra("termo")
    def termo(self):
        esquerda = self.fator()
        while self.eh("OPERADOR", "*") or self.eh("OPERADOR", "/"):
            op = self.avancar()
            direita = self.fator()
            esquerda = self.no("OperacaoBinaria", op, op["lexema"], [esquerda, direita],
                               inicio=dict(esquerda["inicio"]))
        return esquerda

    @_regra("fator")
    def fator(self):
        if self.eh("OPERADOR", "+") or self.eh("OPERADOR", "-"):
            op = self.avancar()
            self.entrar()
            operando = self.fator()
            self.sair()
            return self.no("OperacaoUnaria", op, op["lexema"], [operando])
        return self.atomo()

    @_regra("atomo")
    def atomo(self):
        tok = self.atual()
        tipo = tok["tipo"]
        if tipo == "IDENTIFICADOR":
            self.avancar()
            if self.eh("DELIMITADOR", "("):
                par = self.avancar()
                args = self.argumentos() if not self.eh("DELIMITADOR", ")") else []
                self.consumir("DELIMITADOR", ")",
                              esperado=f"')' para fechar a chamada de '{tok['lexema']}' aberta na coluna {par['coluna']}",
                              abertura=_pos(par["linha"], par["coluna"]), construcao=f"chamada de '{tok['lexema']}'")
                return self.no("Chamada", tok, tok["lexema"], args)
            return self.no("Identificador", tok, tok["lexema"])
        if tipo == "LITERAL_INTEIRO":
            self.avancar()
            return self.no("LiteralInteiro", tok, tok["lexema"])
        if tipo == "LITERAL_REAL":
            self.avancar()
            return self.no("LiteralReal", tok, tok["lexema"])
        if tipo == "LITERAL_STRING":
            self.avancar()
            return self.no("LiteralTexto", tok, tok["lexema"])
        if self.eh("PALAVRA_RESERVADA", "True") or self.eh("PALAVRA_RESERVADA", "False"):
            self.avancar()
            return self.no("LiteralLogico", tok, tok["lexema"])
        if self.eh("DELIMITADOR", "("):
            par = self.avancar()
            interna = self.expressao()
            self.consumir("DELIMITADOR", ")",
                          esperado=f"')' para fechar o parêntese aberto na linha {par['linha']}, coluna {par['coluna']}",
                          abertura=_pos(par["linha"], par["coluna"]), construcao="parêntese")
            return interna
        self.erro("um operando (número, texto, variável, chamada ou '(')",
                  "Verifique se falta um valor antes ou depois de um operador.")

    @_regra("argumentos")
    def argumentos(self):
        args = [self.expressao()]
        while self.eh("DELIMITADOR", ","):
            self.avancar()
            args.append(self.expressao())
        return args

    del _regra


def _erro_dict(token, esperado, encontrado, mensagem, dica, regra, abertura=None):
    return {
        "tipo": "ERRO_SINTATICO",
        "lexema": token["lexema"] if token else "",
        "linha": token["linha"] if token else 1,
        "coluna": token["coluna"] if token else 1,
        "esperado": esperado,
        "encontrado": encontrado,
        "mensagem": mensagem,
        "dica": dica,
        "regra": regra,
        "producao": GRAMATICA.get(regra) if regra else None,
        "abertura": abertura,
    }


def analisar_sintatico(codigo, tokens, detalhes=False):
    """Retorna (ast, erros). Em caso de erro, ast é None e erros tem 1 item.

    Com ``detalhes=True`` retorna (ast, erros, consumidos), em que ``consumidos``
    é a lista de tokens léxicos efetivamente consumidos pelo parser.
    """
    consumidos = []
    try:
        estruturais = gerar_tokens_estruturais(codigo, tokens)
    except ErroIndentacao as e:
        erros = [{
            **_erro_dict({"lexema": "", "linha": e.linha, "coluna": e.coluna},
                         "indentação consistente", "recuo inválido", e.mensagem, e.dica, "bloco"),
        }]
        return (None, erros, consumidos) if detalhes else (None, erros)
    parser = Parser(estruturais)
    # Cada nível de aninhamento usa ~12 quadros de pilha; o limite de MAX_PROFUNDIDADE
    # níveis é verificado pelo parser antes de se aproximar deste teto.
    if sys.getrecursionlimit() < 3000:
        sys.setrecursionlimit(3000)
    try:
        ast = parser.programa()
        resultado = (ast, [])
    except RecursionError:
        tok = parser.atual()
        resultado = (None, [_erro_dict(tok, "menos níveis de aninhamento", descrever(tok),
                                       "O programa tem aninhamento profundo demais para ser analisado.",
                                       "Divida a expressão ou o bloco em partes menores.", parser.regra_atual())])
    except ErroSintatico as e:
        resultado = (None, [_erro_dict(e.token, e.esperado, descrever(e.token), e.mensagem,
                                       e.dica, e.regra, e.abertura)])
    consumidos = parser.consumidos
    return (*resultado, consumidos) if detalhes else resultado
