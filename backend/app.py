from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/analisar', methods=['POST'])
def analisar_codigo():
    # Verifica se a requisição tem JSON
    if not request.is_json:
        return jsonify({"erro": "Formato de requisição inválido. Esperado JSON."}), 400

    dados = request.get_json()
    codigo = dados.get('codigo', '')

    # Validação do backend (não confiar apenas no frontend)
    if not codigo or not isinstance(codigo, str):
        return jsonify({"erro": "O campo 'codigo' é obrigatório e deve ser texto."}), 400
        
    if codigo.strip() == '':
        return jsonify({"erro": "O código não pode conter apenas espaços em branco."}), 400

    # Simula o recebimento (as análises reais virão nas próximas etapas)
    return jsonify({
        "mensagem": "Código recebido e validado com sucesso!",
        "recebido": codigo
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
