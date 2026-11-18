from flask import Flask, request, jsonify
from flask_cors import CORS

from analisador import analisar_lexico, analisar_sintatico

app = Flask(__name__)
CORS(app)

MAX_CARACTERES = 5000

__all__ = ["app", "analisar_lexico", "analisar_sintatico", "MAX_CARACTERES"]


def analisar(codigo):
    """Executa o pipeline: scanner -> (decisão) -> parser.

    Decisão de projeto: se houver erro léxico, o parser NÃO é executado,
    porque a sequência de tokens está incompleta e geraria erros sintáticos
    em cascata que não correspondem ao problema real.
    """
    tokens, erros_lexicos = analisar_lexico(codigo)
    etapas = {"lexica": "erro" if erros_lexicos else "ok",
              "sintatica": "nao_executada",
              "semantica": "nao_implementada"}
    ast = None
    erros_sintaticos = []
    if not erros_lexicos:
        ast, erros_sintaticos = analisar_sintatico(codigo, tokens)
        etapas["sintatica"] = "erro" if erros_sintaticos else "ok"
    erros = erros_lexicos + erros_sintaticos
    return {
        "sucesso": not erros,
        "tokens": tokens,
        "erros": erros,
        "ast": ast,
        "etapas": etapas,
    }


@app.route('/api/analisar', methods=['POST'])
def analisar_codigo():
    if not request.is_json:
        return jsonify({"erro": "Formato inválido."}), 400
    dados = request.get_json(silent=True) or {}
    codigo = dados.get('codigo', '')
    if not isinstance(codigo, str):
        return jsonify({"erro": "O campo 'codigo' deve ser um texto."}), 400
    if not codigo or codigo.strip() == '':
        return jsonify({"erro": "O código não pode estar vazio."}), 400
    if len(codigo) > MAX_CARACTERES:
        return jsonify({"erro": f"O código excede o limite de {MAX_CARACTERES} caracteres "
                                f"({len(codigo)} enviados)."}), 400
    return jsonify(analisar(codigo)), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
