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
        2. Términos técnicos coincidentes
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
        Encuentra el ticket más similar a la consulta proporcionada.
        Solo devuelve el ticket más relevante si supera el umbral de similitud.
        Args:
            query: La consulta a buscar
            k: Número máximo de tickets similares a devolver (por defecto 1)
        """
        tiempo_inicio = time.time()
        print(f"\n{'='*80}")
        print(f"Búsqueda del ticket más similar iniciada: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Consulta: {query}")
        print(f"{'='*80}")
            
        # Cargar tickets
        tickets = self._cargar_tickets()
        if not tickets:
            return []
            
        try:
            # Filtrar tickets resueltos
            print("\n📊 Analizando tickets resueltos...")
            tickets_resueltos = [t for t in tickets if t['status'] == 'resuelto' and t.get('respuesta')]
            print(f"📊 Tickets resueltos disponibles: {len(tickets_resueltos)}")
            
            # Analizar similitudes
            print("\n📊 Calculando similitudes...")
            tiempo_analisis = time.time()
            mejor_ticket = None
            mejor_score = 0.5  # Umbral mínimo de similitud
            
            for ticket in tickets_resueltos:
                score = self._calcular_similitud_tickets(query, ticket['consulta'])
                if score > mejor_score:
                    mejor_score = score
                    ticket_copy = ticket.copy()
                    ticket_copy['similarity_score'] = score
                    mejor_ticket = ticket_copy
            
            tiempo_analisis = time.time() - tiempo_analisis
            print(f"⏱️ Tiempo de análisis: {tiempo_analisis:.2f} segundos")
            
            # Mostrar resultado
            tiempo_total = time.time() - tiempo_inicio
            print(f"⏱️ Tiempo total: {tiempo_total:.2f} segundos")
            
            if mejor_ticket:
                print("\n🎯 Ticket más relevante encontrado:")
                print(f"Ticket #{mejor_ticket['id']} - Score: {mejor_ticket['similarity_score']:.2%}")
                print(f"Cliente: {mejor_ticket['cliente']}")
                print(f"Consulta: {mejor_ticket['consulta'][:100]}...")
                return [mejor_ticket]
            else:
                print("\n❌ No se encontraron tickets similares que superen el umbral de similitud")
                return []
            
        except Exception as e:
            print(f"❌ Error buscando tickets similares: {str(e)}")
            return []