from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configurações
DATA_FILE = 'data/pedidos.json'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.example.com')
EMAIL_PORT = os.getenv('EMAIL_PORT', 587)
EMAIL_USER = os.getenv('EMAIL_USER', 'user@example.com')
EMAIL_PASS = os.getenv('EMAIL_PASS', 'password')

# Garante que o diretório data existe
os.makedirs('data', exist_ok=True)

# Inicializa o arquivo de pedidos se não existir
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# Dados do cardápio (pode ser movido para um banco de dados)
MENU = {
    "margherita": {"name": "Margherita", "price": 45.90},
    "pepperoni": {"name": "Pepperoni", "price": 52.90},
    "quatro-queijos": {"name": "Quatro Queijos", "price": 55.90},
    "calabresa": {"name": "Calabresa", "price": 48.90},
    "portuguesa": {"name": "Portuguesa", "price": 58.90},
    "frango-catupiry": {"name": "Frango com Catupiry", "price": 56.90}
}

SIZES = {
    "pequena": {"name": "Pequena", "slices": 4, "multiplier": 1.0},
    "media": {"name": "Média", "slices": 6, "multiplier": 1.2},
    "grande": {"name": "Grande", "slices": 8, "multiplier": 1.5},
    "familia": {"name": "Família", "slices": 12, "multiplier": 2.0}
}

# Rota principal - pode servir o frontend
@app.route('/')
def home():
    return render_template('index.html')  # Ou redirecionar para o frontend estático

# API para obter o cardápio
@app.route('/api/menu', methods=['GET'])
def get_menu():
    return jsonify({"menu": MENU, "sizes": SIZES})

# API para enviar pedido
@app.route('/api/pedido', methods=['POST'])
def create_order():
    try:
        data = request.json
        
        # Validação básica
        required_fields = ['nome', 'telefone', 'endereco', 'pizza', 'tamanho']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Campo obrigatório faltando: {field}"}), 400
        
        if data['pizza'] not in MENU:
            return jsonify({"error": "Pizza inválida"}), 400
        
        if data['tamanho'] not in SIZES:
            return jsonify({"error": "Tamanho inválido"}), 400
        
        # Calcula o preço total
        pizza_price = MENU[data['pizza']]['price']
        size_multiplier = SIZES[data['tamanho']]['multiplier']
        total_price = pizza_price * size_multiplier
        
        # Cria o objeto do pedido
        pedido = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "cliente": {
                "nome": data['nome'],
                "telefone": data['telefone'],
                "endereco": data['endereco']
            },
            "pizza": data['pizza'],
            "tamanho": data['tamanho'],
            "observacoes": data.get('observacoes', ''),
            "preco": total_price,
            "status": "recebido",
            "data": datetime.now().isoformat()
        }
        
        # Salva o pedido
        with open(DATA_FILE, 'r+') as f:
            pedidos = json.load(f)
            pedidos.append(pedido)
            f.seek(0)
            json.dump(pedidos, f, indent=2)
        
        # Envia e-mail de confirmação (simulado)
        send_confirmation_email(pedido)
        
        return jsonify({
            "message": "Pedido recebido com sucesso!",
            "pedido": pedido
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_confirmation_email(pedido):
    """Função para enviar e-mail de confirmação (simulada)"""
    try:
        # Configuração do e-mail
        msg = MIMEText(f"""
        Olá {pedido['cliente']['nome']},
        
        Seu pedido na Pizzaria Delícia foi recebido!
        
        Detalhes do pedido:
        - Pizza: {MENU[pedido['pizza']]['name']}
        - Tamanho: {SIZES[pedido['tamanho']]['name']}
        - Preço total: R$ {pedido['preco']:.2f}
        - Endereço de entrega: {pedido['cliente']['endereco']}
        
        Status: {pedido['status']}
        
        Obrigado por escolher a Pizzaria Delícia!
        """)
        
        msg['Subject'] = f"Pizzaria Delícia - Confirmação de Pedido #{pedido['id']}"
        msg['From'] = EMAIL_USER
        msg['To'] = "cliente@example.com"  # Em produção, usar o e-mail do cliente
        
        # Simula o envio (em produção, descomente abaixo)
        print(f"E-mail enviado para {pedido['cliente']['nome']}")
        """
        # Código real para enviar e-mail (descomente em produção)
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, [msg['To']], msg.as_string())
        """
        
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

if __name__ == '__main__':
    app.run(debug=True)