from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from datetime import datetime
from rag_engine import RAGEngine

app = Flask(__name__)

# Rutas de datos
TICKETS_FILE = 'data/tickets.json'
NORMATIVAS_DIR = 'data/normativas'

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
        # Buscar tickets similares
        if rag_engine and ticket['status'] == 'pendiente':
            similar_tickets = rag_engine.find_similar_tickets(ticket['consulta'])
            ticket['similar_tickets'] = similar_tickets
        return jsonify(ticket)
    return jsonify({'error': 'Ticket no encontrado'}), 404

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

# ============= BÚSQUEDA DE NORMATIVAS =============

@app.route('/normativas')
def normativas_page():
    return render_template('normativas.html')

@app.route('/api/normativas/list', methods=['GET'])
def list_normativas():
    """Lista todos los documentos disponibles"""
    normativas = []
    
    if os.path.exists(NORMATIVAS_DIR):
        for filename in os.listdir(NORMATIVAS_DIR):
            if filename.endswith('.txt'):
                filepath = os.path.join(NORMATIVAS_DIR, filename)
                normativas.append({
                    'nombre': filename.replace('.txt', ''),
                    'archivo': filename
                })
    
    return jsonify(normativas)

@app.route('/api/normativas/search', methods=['POST'])
def search_normativas():
    """Búsqueda semántica en normativas"""
    try:
        data = request.json
        query = data.get('query', '')
        
        print(f"Búsqueda recibida: '{query}'")
        
        if not query:
            print("Error: Consulta vacía")
            return jsonify({'error': 'La consulta está vacía'}), 400
            
        if not rag_engine:
            print("Error: RAG engine no inicializado")
            return jsonify({'error': 'Sistema no inicializado'}), 500
        
        # Realizar búsqueda semántica
        print("Ejecutando búsqueda semántica...")
        results = rag_engine.search_normativas(query)
        print(f"Resultados encontrados: {len(results)}")
        
        # Formatear resultados
        formatted_results = []
        for result in results:
            relevancia = float(1 - (result['score'] / 10))  # Normalizar score
            
            # Dividir el contenido en líneas para mostrar el contexto
            contenido_lines = result['contenido'].split('\n')
            line_number = 1  # Comenzar desde la línea 1
            
            formatted_results.append({
                'documento': result['documento'],
                'archivo': result['documento'] + '.txt',
                'relevancia': relevancia,
                'coincidencias': [{
                    'line': contenido_lines[0] if contenido_lines else '',  # Primera línea como línea principal
                    'line_number': line_number,
                    'context': result['contenido'],  # Contenido completo como contexto
                    'score': float(result['score'])  # Convertir a float para serialización
                }],
                'num_coincidencias': 1  # Para mantener compatibilidad con el frontend
            })
        
        response_data = {
            'results': formatted_results,
            'query': query
        }
        print(f"Enviando respuesta con {len(formatted_results)} resultados")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error en search_normativas: {str(e)}")
        return jsonify({
            'error': f'Error al realizar la búsqueda: {str(e)}',
            'details': str(e)
        }), 500

@app.route('/api/normativas/download/<filename>')
def download_normativa(filename):
    """Descargar documento completo"""
    filepath = os.path.join(NORMATIVAS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'Archivo no encontrado'}), 404

@app.route('/api/normativas/suggest_response', methods=['POST'])
def suggest_response():
    """Generar sugerencia de respuesta basada en normativas"""
    data = request.json
    query = data.get('query', '')
    
    if not query or not rag_engine:
        return jsonify({'error': 'Consulta vacía o sistema no inicializado'}), 400
    
    try:
        # Primero buscar las normativas relevantes
        context = rag_engine.search_normativas(query)
        
        # Generar respuesta usando el contexto encontrado
        response = rag_engine.generate_response(query, context)
        
        return jsonify({
            'suggestion': response,
            'status': 'success',
            'context': context  # Incluir el contexto usado para generar la respuesta
        })
    except Exception as e:
        print(f"Error en suggest_response: {str(e)}")  # Para debugging
        return jsonify({
            'error': f'Error al generar sugerencia: {str(e)}',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    # Crear directorios si no existen
    os.makedirs('data', exist_ok=True)
    os.makedirs(NORMATIVAS_DIR, exist_ok=True)
    
    # Inicializar el motor RAG antes de arrancar la aplicación
    initialize_rag()
    
    app.run(debug=True, host='0.0.0.0', port=5010)
