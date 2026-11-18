"""Análise léxica (scanner) — Etapa 3, com ajustes da Etapa 4.

O scanner percorre o código-fonte com uma expressão regular mestre formada
por grupos nomeados. Cada grupo corresponde a uma categoria léxica.

Ajustes da Etapa 4 (sem quebrar o contrato da Etapa 3):
- literais numéricos malformados (ex.: ``12abc``) geram UM erro léxico
  em vez de um erro por caractere;
- strings não fechadas na mesma linha geram erro léxico específico;
- ``\\r`` (quebra de linha do Windows) é tratado como espaço.

Também fica aqui a geração dos *tokens estruturais* (NOVA_LINHA,
INDENTACAO, DEDENTACAO e FIM_DE_ARQUIVO), que o parser precisa para
reconhecer os blocos de Python. Esses tokens NÃO aparecem na tabela de
tokens da interface: eles são derivados das linhas e do recuo do código.
"""

import re

PALAVRAS_RESERVADAS = ("if", "else", "while", "for", "def", "return", "True", "False")

TOKEN_TYPES = [
    ("PALAVRA_RESERVADA", r"\b(?:" + "|".join(PALAVRAS_RESERVADAS) + r")\b"),
    ("NUMERO_MALFORMADO", r"\d+(?:\.\d+)?[a-zA-Z_][a-zA-Z0-9_]*"),
    ("IDENTIFICADOR", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
    ("LITERAL_REAL", r"\b\d+\.\d+\b"),
    ("LITERAL_INTEIRO", r"\b\d+\b"),
    ("LITERAL_STRING", r"\"[^\"\n]*\"|'[^'\n]*'"),
    ("STRING_NAO_FECHADA", r"\"[^\"\n]*|'[^'\n]*"),
    ("OPERADOR", r"==|!=|<=|>=|[+\-*/=<>]"),
    ("DELIMITADOR", r"[()\[\]:,]"),
    ("COMENTARIO", r"#[^\n]*"),
    ("ESPACO", r"[ \t\r\n]+"),
    ("ERRO", r"."),
]

_REGEX_MESTRE = re.compile("|".join(f"(?P<{nome}>{padrao})" for nome, padrao in TOKEN_TYPES))

_MENSAGENS_ERRO = {
    "ERRO": "Caractere não reconhecido: '{lexema}'",
    "NUMERO_MALFORMADO": "Literal numérico malformado: '{lexema}' (um nome não pode começar com dígito)",
    "STRING_NAO_FECHADA": "String não fechada: {lexema} (faltou a aspa final na mesma linha)",
}


def analisar_lexico(codigo):
    """Retorna (tokens, erros). Cada item traz tipo, lexema, linha e coluna."""
    tokens = []
    erros = []
    linha = 1
    coluna = 1
    for match in _REGEX_MESTRE.finditer(codigo):
        tipo = match.lastgroup
        lexema = match.group()
        if tipo in ("ESPACO", "COMENTARIO"):
            pass
        elif tipo in _MENSAGENS_ERRO:
            erros.append({
                "tipo": "ERRO_LEXICO",
                "lexema": lexema,
                "linha": linha,
                "coluna": coluna,
                "mensagem": _MENSAGENS_ERRO[tipo].format(lexema=lexema),
            })
        else:
            tokens.append({
                "tipo": tipo,
                "lexema": lexema,
                "linha": linha,
                "coluna": coluna,
            })
        quebras = lexema.count("\n")
        if quebras > 0:
            linha += quebras
            coluna = len(lexema.split("\n")[-1]) + 1
        else:
            coluna += len(lexema)
    return tokens, erros


class ErroIndentacao(Exception):
    """Recuo inconsistente detectado ao montar os tokens estruturais."""

    def __init__(self, mensagem, linha, coluna, dica=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        self.dica = dica


def _largura_recuo(prefixo):
    """Largura do recuo com a regra do Python: tab avança até o próximo múltiplo de 8."""
    largura = 0
    for ch in prefixo:
        largura = (largura // 8 + 1) * 8 if ch == "\t" else largura + 1
    return largura


def gerar_tokens_estruturais(codigo, tokens):
    """Intercala NOVA_LINHA, INDENTACAO e DEDENTACAO entre os tokens léxicos.

    Linhas vazias ou só com comentários não produzem tokens e são ignoradas,
    como no Python. Levanta ErroIndentacao quando o recuo é inconsistente.
    """
    linhas_fonte = codigo.split("\n")
    por_linha = {}
    for tok in tokens:
        por_linha.setdefault(tok["linha"], []).append(tok)

    saida = []
    pilha = [0]
    ultima_linha, ultima_coluna = 1, 1
    for numero in sorted(por_linha):
        texto = linhas_fonte[numero - 1].replace("\r", "")
        prefixo = texto[: len(texto) - len(texto.lstrip(" \t"))]
        if " " in prefixo and "\t" in prefixo:
            raise ErroIndentacao(
                "Indentação mistura espaços e tabulações",
                numero, 1,
                "Use apenas espaços (recomendado: 4 por nível).",
            )
        recuo = _largura_recuo(prefixo)
        if recuo > pilha[-1]:
            pilha.append(recuo)
            saida.append({"tipo": "INDENTACAO", "lexema": "", "linha": numero, "coluna": 1})
        elif recuo < pilha[-1]:
            while recuo < pilha[-1]:
                pilha.pop()
                saida.append({"tipo": "DEDENTACAO", "lexema": "", "linha": numero, "coluna": 1})
            if recuo != pilha[-1]:
                raise ErroIndentacao(
                    "Indentação inconsistente: o recuo desta linha não corresponde a nenhum bloco anterior",
                    numero, 1,
                    "Alinhe a linha com o início de um bloco existente.",
                )
        saida.extend(por_linha[numero])
        ultimo = por_linha[numero][-1]
        ultima_linha = numero
        ultima_coluna = ultimo["coluna"] + len(ultimo["lexema"])
        saida.append({"tipo": "NOVA_LINHA", "lexema": "", "linha": numero, "coluna": ultima_coluna})

    while len(pilha) > 1:
        pilha.pop()
        saida.append({"tipo": "DEDENTACAO", "lexema": "", "linha": ultima_linha, "coluna": ultima_coluna})
    saida.append({"tipo": "FIM_DE_ARQUIVO", "lexema": "", "linha": ultima_linha, "coluna": ultima_coluna})
    return saida
