from rag_engine import RAGEngine

def test_semantic_search():
    print("🔍 Prueba de búsqueda semántica\n")
    
    # Inicializar el motor RAG
    rag = RAGEngine('data/normativas', 'data/tickets.json')
    
    # Pruebas de búsqueda con términos relacionados
    queries = [
        "aislamiento térmico en fachadas",
        "eficiencia energética en edificios",
        "transmitancia térmica de muros",
        "requisitos de ventilación en viviendas",
        "seguridad contra incendios en escaleras"
    ]
    
    for query in queries:
        print(f"\nConsulta: '{query}'")
        results = rag.search_normativas(query)
        
        print(f"Encontrados {len(results)} resultados relevantes:")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. Documento: {result['documento']}")
            print(f"   Relevancia: {(1 - result['score']/10)*100:.1f}%")
            print(f"   Extracto: {result['contenido'][:200]}...")

    # Prueba de tickets similares
    print("\n\n🎫 Prueba de búsqueda de tickets similares\n")
    query = "¿Qué requisitos de aislamiento térmico necesito para una fachada ventilada?"
    print(f"Consulta: '{query}'")
    
    similar_tickets = rag.find_similar_tickets(query)
    print(f"\nEncontrados {len(similar_tickets)} tickets similares:")
    
    for i, ticket in enumerate(similar_tickets[:2], 1):
        print(f"\n{i}. Ticket #{ticket['id']} - Cliente: {ticket['cliente']}")
        print(f"   Consulta original: {ticket['consulta']}")
        if ticket.get('respuesta'):
            print(f"   Respuesta: {ticket['respuesta'][:200]}...")

if __name__ == "__main__":
    test_semantic_search()