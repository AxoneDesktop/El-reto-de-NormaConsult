import os
import json
import time
from rag_engine import RAGEngine

def print_separator():
    print("\n" + "="*80 + "\n")

def test_normativas_search():
    print("🔍 TEST 1: BÚSQUEDA EN NORMATIVAS")
    print_separator()
    
    queries = [
        # Pruebas de búsqueda semántica
        ("Requisitos de ventanas en dormitorios", "Búsqueda sobre ventanas"),
        ("Protección contra el ruido en medianeras", "Búsqueda sobre acústica"),
        ("Sistema de climatización eficiente", "Búsqueda sobre climatización"),
        ("Anchura mínima de pasillos", "Búsqueda sobre accesibilidad"),
        ("Detectores de humo obligatorios", "Búsqueda sobre seguridad"),
        
        # Pruebas de sinónimos y términos relacionados
        ("Aislante en muros", "Búsqueda con sinónimo de aislamiento"),
        ("Transmisión de calor en fachadas", "Búsqueda relacionada con aislamiento térmico"),
        ("Evacuación en caso de fuego", "Búsqueda relacionada con incendios"),
        
        # Pruebas de consultas complejas
        ("Requisitos de ventilación y aislamiento en un sótano", "Búsqueda multi-concepto"),
        ("Normas de seguridad para escaleras en edificios altos", "Búsqueda específica"),
    ]
    
    rag = RAGEngine('data/normativas', 'data/tickets.json')
    
    for query, description in queries:
        print(f"\n📝 {description}")
        print(f"Consulta: '{query}'")
        
        start_time = time.time()
        results = rag.search_normativas(query)
        search_time = time.time() - start_time
        
        print(f"\nTiempo de búsqueda: {search_time:.2f} segundos")
        print(f"Resultados encontrados: {len(results)}")
        
        if results:
            print("\nTop 3 resultados más relevantes:")
            for i, result in enumerate(results[:3], 1):
                print(f"\n{i}. Documento: {result['documento']}")
                print(f"   Relevancia: {(1 - result['score']/10)*100:.1f}%")
                print(f"   Extracto: {result['contenido'][:200]}...")

def test_similar_tickets():
    print("\n🎫 TEST 2: BÚSQUEDA DE TICKETS SIMILARES")
    print_separator()
    
    test_queries = [
        ("Necesito saber los requisitos de aislamiento para una fachada nueva", "Consulta sobre aislamiento"),
        ("¿Qué medidas de seguridad contra incendios necesito en un parking?", "Consulta sobre seguridad"),
        ("¿Es obligatorio poner un ascensor en un edificio de 3 plantas?", "Consulta sobre accesibilidad"),
        ("Reforma de baños, ¿qué normativa de ventilación aplica?", "Consulta sobre ventilación"),
    ]
    
    rag = RAGEngine('data/normativas', 'data/tickets.json')
    
    for query, description in test_queries:
        print(f"\n📝 {description}")
        print(f"Nueva consulta: '{query}'")
        
        start_time = time.time()
        similar_tickets = rag.find_similar_tickets(query)
        search_time = time.time() - start_time
        
        print(f"\nTiempo de búsqueda: {search_time:.2f} segundos")
        print(f"Tickets similares encontrados: {len(similar_tickets)}")
        
        if similar_tickets:
            print("\nTickets más relevantes:")
            for i, ticket in enumerate(similar_tickets[:2], 1):
                print(f"\n{i}. Ticket #{ticket['id']} - Cliente: {ticket['cliente']}")
                print(f"   Similitud: {(1 - ticket.get('similarity_score', 0)/10)*100:.1f}%")
                print(f"   Consulta original: {ticket['consulta']}")
                if ticket.get('respuesta'):
                    print(f"   Respuesta: {ticket['respuesta'][:200]}...")

def test_system_performance():
    print("\n⚡ TEST 3: RENDIMIENTO DEL SISTEMA")
    print_separator()
    
    rag = RAGEngine('data/normativas', 'data/tickets.json')
    
    # Test 1: Velocidad de inicialización
    print("Prueba de reinicialización del sistema...")
    start_time = time.time()
    rag = RAGEngine('data/normativas', 'data/tickets.json')
    init_time = time.time() - start_time
    print(f"Tiempo de inicialización: {init_time:.2f} segundos")
    
    # Test 2: Prueba de carga
    print("\nPrueba de carga (10 búsquedas consecutivas)...")
    query = "requisitos de ventilación"
    times = []
    
    for i in range(10):
        start_time = time.time()
        results = rag.search_normativas(query)
        times.append(time.time() - start_time)
    
    avg_time = sum(times) / len(times)
    print(f"Tiempo promedio de búsqueda: {avg_time:.2f} segundos")
    print(f"Tiempo mínimo: {min(times):.2f} segundos")
    print(f"Tiempo máximo: {max(times):.2f} segundos")

def main():
    print("🚀 INICIANDO PRUEBAS EXHAUSTIVAS DEL SISTEMA")
    print_separator()
    
    try:
        test_normativas_search()
        test_similar_tickets()
        test_system_performance()
        
        print("\n✅ TODAS LAS PRUEBAS COMPLETADAS")
        print_separator()
        
    except Exception as e:
        print(f"\n❌ ERROR EN LAS PRUEBAS: {str(e)}")
        raise

if __name__ == "__main__":
    main()