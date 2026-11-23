from flask import Flask, request, jsonify
from flask_cors import CORS

from analisador import analisar_lexico, analisar_sintatico, GRAMATICA, SIMBOLO_INICIAL
from analisador.lexico import TOKEN_TYPES, PALAVRAS_RESERVADAS
import ia

app = Flask(__name__)
CORS(app)

MAX_CARACTERES = 5000

__all__ = ["app", "analisar", "analisar_lexico", "analisar_sintatico", "MAX_CARACTERES"]

# Correspondência entre os terminais da gramática e as categorias de token do scanner.
TERMINAIS = {
    "IDENTIFICADOR": "IDENTIFICADOR",
    "LITERAL_INTEIRO": "LITERAL_INTEIRO",
    "LITERAL_REAL": "LITERAL_REAL",
    "LITERAL_STRING": "LITERAL_STRING",
    **{f'"{p}"': "PALAVRA_RESERVADA" for p in PALAVRAS_RESERVADAS if p != "for"},
    **{f'"{o}"': "OPERADOR" for o in ("=", "+", "-", "*", "/", "==", "!=", "<", ">", "<=", ">=")},
    **{f'"{d}"': "DELIMITADOR" for d in ("(", ")", ":", ",")},
    "NOVA_LINHA": "estrutural (fim de linha com comando)",
    "INDENTACAO": "estrutural (aumento do recuo)",
    "DEDENTACAO": "estrutural (redução do recuo)",
    "FIM_DE_ARQUIVO": "estrutural (fim do código)",
}


def analisar(codigo):
    """Executa o pipeline: scanner -> (decisão) -> parser.

    Decisão de projeto: se houver erro léxico, o parser NÃO é executado,
    porque a sequência de tokens está incompleta e geraria erros sintáticos
    em cascata que não correspondem ao problema real.
    """
    tokens, erros_lexicos = analisar_lexico(codigo)
    executar_parser = not erros_lexicos
    ast, erros_sintaticos, consumidos = None, [], []
    if executar_parser:
        ast, erros_sintaticos, consumidos = analisar_sintatico(codigo, tokens, detalhes=True)

    etapas = {
        "lexica": "erro" if erros_lexicos else "ok",
        "sintatica": ("erro" if erros_sintaticos else "ok") if executar_parser else "nao_executada",
        "semantica": "nao_implementada",
    }
    return {
        # Campos da Etapa 3 (preservados para compatibilidade)
        "sucesso": not erros_lexicos and not erros_sintaticos,
        "tokens": tokens,
        "erros": erros_lexicos + erros_sintaticos,
        # Campos da Etapa 4
        "ast": ast,
        "etapas": etapas,
        "lexico": {"sucesso": not erros_lexicos, "tokens": tokens, "erros": erros_lexicos},
        "sintatico": {
            "executado": executar_parser,
            "sucesso": executar_parser and not erros_sintaticos,
            "ast": ast,
            "erros": erros_sintaticos,
            "tokens_consumidos": len(consumidos),
            "motivo": None if executar_parser else
                      "A análise sintática não foi executada porque há erros léxicos.",
        },
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
    try:
        return jsonify(analisar(codigo)), 200
    except Exception:  # nunca expor detalhes internos ao estudante
        app.logger.exception("Falha inesperada na análise")
        return jsonify({"erro": "Erro interno ao analisar o código. Tente novamente ou simplifique o programa."}), 500


@app.route('/api/gramatica', methods=['GET'])
def gramatica():
    """Gramática usada pelo parser (fonte única para a interface e a documentação)."""
    return jsonify({
        "simbolo_inicial": SIMBOLO_INICIAL,
        "producoes": GRAMATICA,
        "nao_terminais": list(GRAMATICA),
        "terminais": TERMINAIS,
        "categorias_lexicas": [nome for nome, _ in TOKEN_TYPES],
    }), 200


# ---------------------------------------------------------------- assistente de IA (opcional)

@app.route('/api/ia/status', methods=['GET'])
def ia_status():
    return jsonify(ia.status()), 200


@app.route('/api/ia/aquecer', methods=['POST'])
def ia_aquecer():
    """Carrega o modelo na memória antes da primeira pergunta (em segundo plano)."""
    return jsonify({"iniciado": ia.aquecer()}), 202


@app.route('/api/ia/explicar', methods=['POST'])
def ia_explicar():
    """Explicação didática gerada pelo Ollama a partir da análise REAL do código.

    Corpo: {"tipo": "no"|"erro"|"token"|"pergunta", "codigo": "...",
            "caminho": [índices dos filhos a partir da raiz] (tipo "no"),
            "indice": posição na lista de erros ou de tokens (tipos "erro" e "token"),
            "pergunta": "..." (opcional, obrigatória no tipo "pergunta")}
    """
    if not request.is_json:
        return jsonify({"erro": "Formato inválido."}), 400
    dados = request.get_json(silent=True) or {}
    tipo = dados.get("tipo")
    codigo = dados.get("codigo") or ""
    if not isinstance(codigo, str) or len(codigo) > MAX_CARACTERES:
        return jsonify({"erro": f"O código deve ser um texto de até {MAX_CARACTERES} caracteres."}), 400
    if tipo != "pergunta" and not codigo.strip():
        return jsonify({"erro": "Analise um código antes de pedir uma explicação."}), 400
    try:
        analise = analisar(codigo) if codigo.strip() else None
        mensagens, pergunta = ia.montar_mensagens(tipo, dados.get("pergunta"), codigo, analise,
                                                  caminho=dados.get("caminho"), indice=dados.get("indice"))
        texto, modelo = ia.explicar(mensagens)
    except ia.ErroIA as e:
        return jsonify({"erro": e.mensagem}), e.status
    return jsonify({"explicacao": texto, "modelo": modelo, "pergunta": pergunta, "gerado_por_ia": True}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
