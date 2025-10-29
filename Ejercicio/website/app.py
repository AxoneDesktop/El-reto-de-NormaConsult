from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
from rag_engine import RAGEngine

app = Flask(__name__)

# Ruta de datos
TICKETS_FILE = 'data/tickets.json'

# Inicializar el motor RAG
rag_engine = None

def initialize_rag():
    global rag_engine
    if rag_engine is None:
        print("Inicializando motor RAG para tickets similares...")
        rag_engine = RAGEngine(TICKETS_FILE)
        print("Motor RAG inicializado correctamente")

# Cargar tickets
def load_tickets():
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tickets, f, ensure_ascii=False, indent=2)

# Página principal
@app.route('/')
def index():
    return render_template('index.html')

# ============= SISTEMA DE TICKETS =============

@app.route('/tickets')
def tickets_page():
    return render_template('tickets.html')

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    tickets = load_tickets()
    status = request.args.get('status', 'all')
    
    if status != 'all':
        tickets = [t for t in tickets if t['status'] == status]
    
    return jsonify(tickets)

@app.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    tickets = load_tickets()
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    
    if ticket:
        return jsonify(ticket)
    return jsonify({'error': 'Ticket no encontrado'}), 404

@app.route('/api/tickets/<int:ticket_id>/similar', methods=['GET'])
def find_similar_tickets(ticket_id):
    """Buscar tickets similares de forma explícita"""
    tickets = load_tickets()
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    
    if not ticket:
        return jsonify({'error': 'Ticket no encontrado'}), 404
    
    if rag_engine:
        try:
            similar_tickets = rag_engine.find_similar_tickets(ticket['consulta'])
            return jsonify({'similar_tickets': similar_tickets})
        except Exception as e:
            print(f"Error al buscar tickets similares: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'RAG engine no inicializado'}), 500

@app.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    tickets = load_tickets()
    data = request.json
    
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            ticket['status'] = data.get('status', ticket['status'])
            ticket['respuesta'] = data.get('respuesta', ticket['respuesta'])
            ticket['fecha_respuesta'] = datetime.now().isoformat()
            save_tickets(tickets)
            return jsonify(ticket)
    
    return jsonify({'error': 'Ticket no encontrado'}), 404

if __name__ == '__main__':
    # Crear directorio de datos si no existe
    os.makedirs('data', exist_ok=True)
    
    # Inicializar el motor RAG antes de arrancar la aplicación
    initialize_rag()
    
    app.run(debug=True, host='0.0.0.0', port=5010)
