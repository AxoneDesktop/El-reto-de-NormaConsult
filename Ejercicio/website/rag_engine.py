import os
import json
import time
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


class RAGEngine:
    def __init__(self, normativas_dir: str, tickets_file: str):
        self.normativas_dir = normativas_dir
        self.tickets_file = tickets_file

        print("🧠 Inicializando RAG Engine...")
        print("📥 Descargando modelo de embeddings (puede tardar la primera vez)...")

        # Modelo de embeddings
        try:
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            print("✅ Modelo cargado correctamente")
        except Exception as e:
            print(f"❌ Error al cargar el modelo: {e}")
            raise

        # Índices FAISS
        self.normativas_index = None
        self.tickets_index = None

        # Datos
        self.normativas_data = []
        self.tickets_data = []

        # Inicializar índices
        self._initialize_indexes()

        print(f"✅ RAG Engine listo: {len(self.tickets_data)} tickets | {len(self.normativas_data)} fragmentos de normativas")
    
    def _initialize_indexes(self):
        """Inicializar los índices FAISS"""
        self.normativas_index = faiss.IndexFlatL2(384)
        self.tickets_index = faiss.IndexFlatL2(384)
        
        # Cargar y procesar normativas
        self._process_normativas()
        
        # Cargar y procesar tickets
        self._process_tickets()

    # =========================
    # NORMATIVAS
    # =========================
    def _process_normativas(self):
        """Carga e indexa todas las normativas .txt"""
        self.normativas_data = []
        embeddings = []

        if not os.path.exists(self.normativas_dir):
            print(f"⚠️ Directorio de normativas no encontrado: {self.normativas_dir}")
            return

        files = [f for f in os.listdir(self.normativas_dir) if f.endswith(".txt")]
        print(f"📄 Procesando {len(files)} archivos de normativas...")

        for idx, filename in enumerate(files, 1):
            filepath = os.path.join(self.normativas_dir, filename)
            print(f"  [{idx}/{len(files)}] Procesando {filename}...")
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not content.strip():
                    print(f"    ⚠️ Archivo vacío, saltando...")
                    continue

                chunks = self._split_into_chunks(content)
                print(f"    → {len(chunks)} fragmentos generados")

                for chunk in chunks:
                    if len(chunk.strip()) < 50:  # Ignorar chunks muy pequeños
                        continue
                    
                    embedding = self.model.encode([chunk])[0]
                    embeddings.append(embedding)
                    self.normativas_data.append({
                        'documento': filename.replace('.txt', ''),
                        'contenido': chunk
                    })
            except Exception as e:
                print(f"    ❌ Error procesando {filename}: {e}")
                continue

        if embeddings:
            self.normativas_index.add(np.array(embeddings))
            print(f"📘 {len(self.normativas_data)} fragmentos de normativas indexados.")
    
    # =========================
    # UTILIDAD
    # =========================
    def _split_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """Divide el texto en fragmentos manejables"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
    def _process_tickets(self):
        """Carga tickets y genera sus embeddings"""
        if not os.path.exists(self.tickets_file):
            print("⚠️ Archivo de tickets no encontrado.")
            return

        print(f"🎫 Procesando tickets...")
        
        try:
            with open(self.tickets_file, 'r', encoding='utf-8') as f:
                tickets = json.load(f)
        except Exception as e:
            print(f"❌ Error leyendo tickets: {e}")
            return

        self.tickets_data = []
        embeddings = []

        for ticket in tickets:
            if ticket.get('status') == 'resuelto' and ticket.get('respuesta'):
                try:
                    embedding = self.model.encode([ticket['consulta']])[0]
                    embeddings.append(embedding)
                    self.tickets_data.append(ticket)
                except Exception as e:
                    print(f"  ⚠️ Error procesando ticket {ticket.get('id')}: {e}")
                    continue

        if embeddings:
            self.tickets_index.add(np.array(embeddings))
            print(f"📨 {len(self.tickets_data)} tickets resueltos indexados.")

    # =========================
    # UTILIDAD
    # =========================
    def _split_into_chunks(self, text: str, chunk_size: int = 600) -> List[str]:
        """Divide el texto en fragmentos manejables"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    # =========================
    # BÚSQUEDA DE NORMATIVAS
    # =========================
    def search_normativas(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Busca normativas similares al texto dado usando búsqueda semántica"""
        print(f"RAG Engine - Buscando: '{query}'")
        
        try:
            # Verificar que tenemos datos indexados
            if self.normativas_index is None or self.normativas_index.ntotal == 0:
                print("RAG Engine - Error: No hay documentos indexados")
                return []
            
            print(f"RAG Engine - Codificando consulta...")
            query_vector = self.model.encode([query])[0]
            
            print(f"RAG Engine - Realizando búsqueda en el índice...")
            D, I = self.normativas_index.search(np.array([query_vector]), k)
            
            results = []
            print(f"RAG Engine - Procesando {len(I[0])} resultados...")
            
            for i, idx in enumerate(I[0]):
                if idx >= 0 and idx < len(self.normativas_data):
                    result = self.normativas_data[idx].copy()
                    result['score'] = float(D[0][i])
                    result['similarity_score'] = round(1 - float(D[0][i]) / 10, 3)
                    results.append(result)
                    print(f"RAG Engine - Resultado {i+1}: {result['documento']} (score: {result['score']})")
            
            print(f"RAG Engine - Búsqueda completada. {len(results)} resultados encontrados")
            return results
            
        except Exception as e:
            print(f"RAG Engine - Error en búsqueda: {str(e)}")
            raise

    # =========================
    # BÚSQUEDA DE TICKETS
    # =========================
    def find_similar_tickets(self, query: str, k: int = 1) -> List[Dict[str, Any]]:
        """Encuentra el ticket más similar por embeddings (solo el más relevante)"""
        if not self.tickets_data:
            print("⚠️ No hay tickets cargados.")
            return []

        query_vector = self.model.encode([query])[0]
        D, I = self.tickets_index.search(np.array([query_vector]), k)

        results = []
        for i, idx in enumerate(I[0]):
            if idx >= 0 and idx < len(self.tickets_data):
                ticket = self.tickets_data[idx].copy()
                ticket['similarity_score'] = round(1 - float(D[0][i]) / 10, 3)
                results.append(ticket)

        print(f"🎯 {len(results)} ticket(s) más relevante(s) encontrado(s).")
        return results

    # =========================
    # RESPUESTAS GENERADAS
    # =========================
    def generate_response(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Genera una respuesta mostrando los fragmentos más relevantes de las normativas"""
        if not context:
            return "No se encontró información relevante en las normativas."

        # Crear respuesta con los fragmentos más relevantes
        response_parts = ["📘 **Información encontrada en las normativas:**\n"]
        
        for i, item in enumerate(context[:3], 1):  # Mostrar los 3 más relevantes
            doc_name = item['documento'].replace('_', ' ')
            similarity = item.get('similarity_score', 0)
            
            response_parts.append(f"\n**{i}. {doc_name}** (Relevancia: {similarity:.1%})")
            response_parts.append(f"{item['contenido'][:400]}...")
            response_parts.append("---")
        
        response_parts.append("\n💡 **Sugerencia:** Revisa estos fragmentos para elaborar tu respuesta al cliente.")
        
        return "\n".join(response_parts)

    # =========================
    # REFRESCAR ÍNDICES
    # =========================
    def refresh_indexes(self):
        """Reconstruye los índices FAISS tras actualizar documentos"""
        print("🔄 Actualizando índices...")
        self.normativas_index = faiss.IndexFlatL2(384)
        self.tickets_index = faiss.IndexFlatL2(384)
        self._process_normativas()
        self._process_tickets()
        print("✅ Índices actualizados correctamente.")
