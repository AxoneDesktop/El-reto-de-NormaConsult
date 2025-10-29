import os
import json
from typing import List, Dict, Any
from datetime import datetime
import time

class RAGEngine:
    def __init__(self, tickets_file: str):
        self.tickets_file = tickets_file
        print(f"Inicializando RAG Engine con archivo de tickets: {tickets_file}")
        
    def _cargar_tickets(self) -> List[Dict]:
        """Carga los tickets solo cuando son necesarios"""
        print("\n📂 Cargando tickets desde el archivo...")
        tiempo_inicio = time.time()
        
        if not os.path.exists(self.tickets_file):
            print("❌ Error: Archivo de tickets no encontrado")
            return []
            
        try:
            with open(self.tickets_file, 'r', encoding='utf-8') as f:
                tickets = json.load(f)
            tiempo_carga = time.time() - tiempo_inicio
            print(f"✅ Tickets cargados correctamente en {tiempo_carga:.2f} segundos")
            print(f"📊 Total de tickets: {len(tickets)}")
            return tickets
        except Exception as e:
            print(f"❌ Error cargando tickets: {str(e)}")
            return []
        
    def _calcular_similitud_tickets(self, consulta: str, ticket_consulta: str) -> float:
        """
        Calcula la similitud entre dos consultas usando varios criterios:
        1. Palabras compartidas
        2. Secuencias de palabras comunes
        3. Términos técnicos coincidentes
        """
        # Convertir a minúsculas
        consulta = consulta.lower()
        ticket_consulta = ticket_consulta.lower()
        
        # Lista de términos técnicos comunes en construcción
        terminos_tecnicos = {
            'aislamiento', 'térmico', 'acústico', 'ventilación', 'salubridad',
            'eficiencia', 'energética', 'resistencia', 'fuego', 'evacuación',
            'accesibilidad', 'seguridad', 'estructura', 'cimentación', 'instalaciones'
        }
        
        # 1. Calcular similitud por palabras compartidas
        palabras_consulta = set(consulta.split())
        palabras_ticket = set(ticket_consulta.split())
        palabras_comunes = palabras_consulta & palabras_ticket
        
        # 2. Calcular términos técnicos compartidos
        terminos_consulta = palabras_consulta & terminos_tecnicos
        terminos_ticket = palabras_ticket & terminos_tecnicos
        terminos_comunes = terminos_consulta & terminos_ticket
        
        # Calcular puntuación
        score = 0.0
        if len(palabras_consulta) > 0:
            # 60% del score basado en palabras comunes
            score += 0.6 * (len(palabras_comunes) / len(palabras_consulta))
            # 40% del score basado en términos técnicos
            if len(terminos_consulta) > 0:
                score += 0.4 * (len(terminos_comunes) / len(terminos_consulta))
        
        return score

    def find_similar_tickets(self, query: str, k: int = 1) -> List[Dict[str, Any]]:
        """
        Encuentra el ticket más similar y muestra métricas detalladas del proceso.
        Args:
            query: La consulta a buscar
            k: Número máximo de tickets similares a devolver (por defecto 1 para mostrar solo el más similar)
        """
        tiempo_inicio = time.time()
        print(f"\n{'='*80}")
        print(f"Búsqueda de tickets similares iniciada: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Consulta: {query}")
        print(f"{'='*80}")
        
        # No usamos caché para asegurar búsquedas frescas cada vez
        tiempo_inicio = time.time()
            
        # Cargar tickets
        tickets = self._cargar_tickets()
        if not tickets:
            return []
            
        try:
            # Filtrar tickets resueltos
            print("\n� Analizando tickets resueltos...")
            tickets_resueltos = [t for t in tickets if t['status'] == 'resuelto' and t.get('respuesta')]
            print(f"📊 Tickets resueltos disponibles: {len(tickets_resueltos)}")
            
            # Analizar similitudes
            print("\n📊 Calculando similitudes...")
            tiempo_analisis = time.time()
            similar_tickets = []
            
            for ticket in tickets_resueltos:
                score = self._calcular_similitud_tickets(query, ticket['consulta'])
                if score > 0.5:  # Umbral más alto para mostrar solo coincidencias muy relevantes
                    ticket_copy = ticket.copy()
                    ticket_copy['similarity_score'] = score
                    similar_tickets.append(ticket_copy)
            
            tiempo_analisis = time.time() - tiempo_analisis
            print(f"⏱️ Tiempo de análisis: {tiempo_analisis:.2f} segundos")
            
            # Ordenar por relevancia
            similar_tickets.sort(key=lambda x: x['similarity_score'], reverse=True)
            similar_tickets = similar_tickets[:k]
            
            # Mostrar resultados
            tiempo_total = time.time() - tiempo_inicio
            print(f"\n📊 Resultados encontrados: {len(similar_tickets)}")
            print(f"⏱️ Tiempo total: {tiempo_total:.2f} segundos")
            print("\n🎯 Tickets más relevantes encontrados:")
            
            for i, ticket in enumerate(similar_tickets, 1):
                print(f"\n{'-'*40}")
                print(f"Ticket #{ticket['id']} - Score: {ticket['similarity_score']:.2%}")
                print(f"Cliente: {ticket['cliente']}")
                print(f"Consulta: {ticket['consulta'][:100]}...")
                
                # Calcular tiempo de respuesta original del ticket
                fecha_creacion = datetime.fromisoformat(ticket['fecha_creacion'])
                fecha_respuesta = datetime.fromisoformat(ticket['fecha_respuesta'])
                tiempo_respuesta = fecha_respuesta - fecha_creacion
                print(f"Tiempo de respuesta original: {tiempo_respuesta}")
            
            # Guardar en caché
            self._cache[cache_key] = similar_tickets
            print(f"\n{'='*80}")
            return similar_tickets
            
        except Exception as e:
            print(f"❌ Error buscando tickets similares: {str(e)}")
            return []

    def find_similar_tickets(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Encuentra tickets similares basados en la consulta proporcionada.
        Solo devuelve tickets resueltos que puedan servir como referencia.
        """
        print(f"RAG Engine - Buscando tickets similares a: '{query}'")
        
        if not self.tickets_data:
            print("RAG Engine - No hay tickets previos para comparar")
            return []
        
        try:
            query_vector = self.model.encode([query])[0]
            D, I = self.tickets_index.search(np.array([query_vector]), k)
            
            results = []
            for i, idx in enumerate(I[0]):
                if idx >= 0 and idx < len(self.tickets_data):
                    ticket = self.tickets_data[idx].copy()
                    ticket['similarity_score'] = float(D[0][i])
                    results.append(ticket)
                    print(f"RAG Engine - Ticket similar encontrado: #{ticket['id']}")
            
            return results
            
        except Exception as e:
            print(f"RAG Engine - Error buscando tickets similares: {str(e)}")
            return []

    def find_similar_tickets(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Encuentra tickets similares basados en palabras clave compartidas.
        Solo devuelve tickets que estén resueltos.
        """
        # Convertir la consulta a palabras clave
        query_words = set(query.lower().split())
        
        # Cargar tickets
        if not os.path.exists(self.tickets_file):
            print("Archivo de tickets no encontrado")
            return []
            
        try:
            with open(self.tickets_file, 'r', encoding='utf-8') as f:
                tickets = json.load(f)
            
            # Filtrar solo tickets resueltos y calcular similitud
            similar_tickets = []
            for ticket in tickets:
                if ticket['status'] == 'resuelto' and ticket.get('respuesta'):
                    # Convertir la consulta del ticket a palabras clave
                    ticket_words = set(ticket['consulta'].lower().split())
                    
                    # Calcular palabras compartidas
                    common_words = len(query_words & ticket_words)
                    
                    if common_words > 0:
                        # Añadir score de similitud
                        ticket_copy = ticket.copy()
                        ticket_copy['similarity_score'] = common_words / len(query_words)
                        similar_tickets.append(ticket_copy)
            
            # Ordenar por score de similitud y tomar los k más similares
            similar_tickets.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_tickets[:k]
            
        except Exception as e:
            print(f"Error buscando tickets similares: {str(e)}")
            return []

    def generate_response(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Genera una respuesta basada en el contexto más relevante encontrado."""
        if not context:
            return "No se encontró información relevante para generar una respuesta."
        
        # Ordenar el contexto por relevancia (score más bajo = más relevante)
        sorted_context = sorted(context, key=lambda x: x.get('score', float('inf')))
        
        # Tomar el fragmento más relevante
        best_match = sorted_context[0]
        
        # Devolver una respuesta formateada con la información más relevante
        response = (
            f"Según el documento {best_match['documento']}:\n\n"
            f"{best_match['contenido']}\n\n"
            "Para obtener más información, consulte el documento completo."
        )
        
        return response

    def refresh_indexes(self):
        """Actualizar los índices con nuevos documentos o tickets"""
        self.normativas_index = faiss.IndexFlatL2(384)
        self.tickets_index = faiss.IndexFlatL2(384)
        self._process_normativas()
        self._process_tickets()