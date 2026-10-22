from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

TOKEN_TYPES = [
    ('PALAVRA_RESERVADA', r'\b(if|else|while|for|def|return|True|False)\b'),
    ('IDENTIFICADOR', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('LITERAL_REAL', r'\b\d+\.\d+\b'),
    ('LITERAL_INTEIRO', r'\b\d+\b'),
    ('LITERAL_STRING', r'"[^"]*"|\'[^\']*\''),
    ('OPERADOR', r'==|!=|<=|>=|[+\-*/=<>]'),
    ('DELIMITADOR', r'[()\[\]:,]'),
    ('COMENTARIO', r'#[^\n]*'),
    ('ESPACO', r'[ \t\n]+'),
    ('ERRO', r'.')
]

def analisar_lexico(codigo):
    tokens = []
    erros = []
    linha = 1
    coluna = 1
    regex_master = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_TYPES)
    for match in re.finditer(regex_master, codigo):
        tipo = match.lastgroup
        lexema = match.group()
        if tipo == 'ESPACO' or tipo == 'COMENTARIO':
            pass
        elif tipo == 'ERRO':
            erros.append({
                "tipo": "ERRO_LEXICO",
                "lexema": lexema,
                "linha": linha,
                "coluna": coluna,
                "mensagem": f"Caractere não reconhecido: '{lexema}'"
            })
        else:
            tokens.append({
                "tipo": tipo,
                "lexema": lexema,
                "linha": linha,
                "coluna": coluna
            })
        quebras = lexema.count('\n')
        if quebras > 0:
            linha += quebras
            coluna = len(lexema.split('\n')[-1]) + 1
        else:
            coluna += len(lexema)
    return tokens, erros

@app.route('/api/analisar', methods=['POST'])
def analisar_codigo():
    if not request.is_json:
        return jsonify({"erro": "Formato inválido."}), 400
    dados = request.get_json()
    codigo = dados.get('codigo', '')
    if not codigo or codigo.strip() == '':
        return jsonify({"erro": "O código não pode estar vazio."}), 400
    tokens, erros = analisar_lexico(codigo)
    sucesso = len(erros) == 0
    return jsonify({
        "sucesso": sucesso,
        "tokens": tokens,
        "erros": erros
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
