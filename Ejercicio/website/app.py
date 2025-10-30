from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
from rag_engine import RAGEngine

app = Flask(__name__)

# Rutas de datos (usar rutas absolutas)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TICKETS_FILE = os.path.join(BASE_DIR, 'data', 'tickets.json')
NORMATIVAS_DIR = os.path.join(BASE_DIR, 'data', 'normativas')

# Inicializar el motor RAG
rag_engine = None

def initialize_rag():
    global rag_engine
    if rag_engine is None:
        print("Inicializando motor RAG...")
        rag_engine = RAGEngine(NORMATIVAS_DIR, TICKETS_FILE)
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

# ============= SISTEMA DE NORMATIVAS =============

@app.route('/normativas')
def normativas_page():
    return render_template('normativas.html')

@app.route('/api/normativas/list', methods=['GET'])
def list_normativas():
    """Lista todos los documentos de normativas disponibles"""
    normativas = []
    
    if os.path.exists(NORMATIVAS_DIR):
        for filename in os.listdir(NORMATIVAS_DIR):
            if filename.endswith('.txt'):
                normativas.append({
                    'nombre': filename.replace('.txt', '').replace('_', ' '),
                    'archivo': filename
                })
    
    return jsonify(normativas)

@app.route('/api/normativas/search', methods=['POST'])
def search_normativas():
    """Buscar en normativas usando RAG"""
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Query vacío', 'results': []}), 400
    
    if not rag_engine:
        return jsonify({'error': 'RAG engine no inicializado', 'results': []}), 500
    
    try:
        print(f"Búsqueda recibida: '{query}'")
        
        # Buscar normativas similares
        normativas_results = rag_engine.search_normativas(query)
        
        print(f"Resultados encontrados: {len(normativas_results)}")
        
        # Formatear resultados para el frontend
        formatted_results = []
        for result in normativas_results:
            formatted_results.append({
                'documento': result['documento'],
                'relevancia': result.get('similarity_score', 0),
                'score': result.get('score', 0),
                'coincidencias': [{
                    'context': result['contenido'],
                    'line_number': 1
                }]
            })
        
        return jsonify({
            'query': query,
            'results': formatted_results
        })
        
    except Exception as e:
        print(f"Error en búsqueda de normativas: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'results': []
        }), 500
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    """Crear un nuevo ticket"""
    data = request.json
    tickets = load_tickets()
    
    # Generar nuevo ID
    next_id = max([t['id'] for t in tickets], default=0) + 1
    
    new_ticket = {
        'id': next_id,
        'cliente': data.get('cliente', ''),
        'consulta': data.get('consulta', ''),
        'status': 'pendiente',
        'fecha_creacion': datetime.now().isoformat(),
        'respuesta': None,
        'fecha_respuesta': None
    }
    
    tickets.append(new_ticket)
    save_tickets(tickets)
    
    # Refrescar índices del RAG para incluir el nuevo ticket
    if rag_engine:
        rag_engine.refresh_indexes()
    
    return jsonify(new_ticket), 201

if __name__ == '__main__':
    # Crear directorio de datos si no existe
    data_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(NORMATIVAS_DIR, exist_ok=True)
    
    # Inicializar el motor RAG antes de arrancar la aplicación
    initialize_rag()
    
    # Ejecutar en modo production (sin debug) para evitar problemas con el reloader
    app.run(debug=False, host='0.0.0.0', port=5010)
