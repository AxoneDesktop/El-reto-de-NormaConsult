import os
from dotenv import load_dotenv
from rag_engine import RAGEngine

load_dotenv()

# Rutas de datos
NORMATIVAS_DIR = 'data/normativas'
TICKETS_FILE = 'data/tickets.json'

def test_rag_system():
    print("🔍 Iniciando prueba del sistema RAG...")
    
    # Verificar la API key
    print("\nVerificando API key de OpenAI...")
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"✅ API key encontrada: {api_key[:10]}...")
    else:
        print("❌ API key no encontrada")
    
    # 1. Probar inicialización del motor RAG
    print("\n1. Inicializando RAG Engine...")
    try:
        rag = RAGEngine(NORMATIVAS_DIR, TICKETS_FILE)
        print("✅ RAG Engine inicializado correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar RAG Engine: {str(e)}")
        return
    
    # 2. Probar búsqueda semántica
    print("\n2. Probando búsqueda semántica...")
    try:
        query = "requisitos de aislamiento térmico en edificios"
        results = rag.search_normativas(query)
        print(f"✅ Búsqueda exitosa - Encontrados {len(results)} resultados")
        if results:
            print("\nPrimer resultado:")
            print(f"Documento: {results[0]['documento']}")
            print(f"Relevancia: {1 - results[0]['score']/10:.2%}")
            print("Extracto:", results[0]['contenido'][:200], "...")
    except Exception as e:
        print(f"❌ Error en búsqueda semántica: {str(e)}")
    
    # 3. Probar búsqueda de tickets similares
    print("\n3. Probando búsqueda de tickets similares...")
    try:
        query = "necesito información sobre los requisitos de ventilación"
        similar_tickets = rag.find_similar_tickets(query)
        print(f"✅ Búsqueda de tickets similares exitosa - Encontrados {len(similar_tickets)} tickets")
    except Exception as e:
        print(f"❌ Error en búsqueda de tickets similares: {str(e)}")
    
    # 4. Probar generación de respuesta
    print("\n4. Probando generación de respuesta...")
    try:
        if os.getenv('OPENAI_API_KEY'):
            context = rag.search_normativas("ventilación en viviendas")
            response = rag.generate_response("¿Cuáles son los requisitos de ventilación para una vivienda?", context)
            print("✅ Generación de respuesta exitosa")
            print("\nRespuesta generada:", response[:200], "...")
        else:
            print("⚠️ Omitiendo prueba de generación - No se encontró OPENAI_API_KEY")
    except Exception as e:
        print(f"❌ Error en generación de respuesta: {str(e)}")
    
    print("\n✨ Pruebas completadas")

if __name__ == "__main__":
    test_rag_system()