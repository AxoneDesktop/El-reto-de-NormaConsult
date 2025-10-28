import os
import json
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from datetime import datetime
import tiktoken
import openai
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self, normativas_dir: str, tickets_file: str):
        self.normativas_dir = normativas_dir
        self.tickets_file = tickets_file
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.normativas_index = None
        self.tickets_index = None
        self.normativas_data = []
        self.tickets_data = []
        self._initialize_indexes()

    def _initialize_indexes(self):
        # Crear índices FAISS
        self.normativas_index = faiss.IndexFlatL2(384)  # dimensión del modelo
        self.tickets_index = faiss.IndexFlatL2(384)
        
        # Cargar y procesar normativas
        self._process_normativas()
        
        # Cargar y procesar tickets
        self._process_tickets()

    def _process_normativas(self):
        self.normativas_data = []
        embeddings = []
        
        for filename in os.listdir(self.normativas_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(self.normativas_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Dividir el contenido en chunks
                chunks = self._split_into_chunks(content)
                
                for chunk in chunks:
                    embedding = self.model.encode([chunk])[0]
                    embeddings.append(embedding)
                    self.normativas_data.append({
                        'documento': filename.replace('.txt', ''),
                        'contenido': chunk
                    })
        
        if embeddings:
            self.normativas_index.add(np.array(embeddings))

    def _process_tickets(self):
        if not os.path.exists(self.tickets_file):
            return
        
        with open(self.tickets_file, 'r', encoding='utf-8') as f:
            tickets = json.load(f)
        
        self.tickets_data = []
        embeddings = []
        
        for ticket in tickets:
            if ticket['status'] == 'resuelto' and 'respuesta' in ticket:
                embedding = self.model.encode([ticket['consulta']])[0]
                embeddings.append(embedding)
                self.tickets_data.append(ticket)
        
        if embeddings:
            self.tickets_index.add(np.array(embeddings))

    def _split_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        # Dividir el texto en párrafos
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

    def search_normativas(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
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
                    results.append(result)
                    print(f"RAG Engine - Resultado {i+1}: {result['documento']} (score: {result['score']})")
            
            print(f"RAG Engine - Búsqueda completada. {len(results)} resultados encontrados")
            return results
            
        except Exception as e:
            print(f"RAG Engine - Error en búsqueda: {str(e)}")
            raise

    def find_similar_tickets(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        if not self.tickets_data:  # Si no hay tickets previos
            return []
        
        query_vector = self.model.encode([query])[0]
        D, I = self.tickets_index.search(np.array([query_vector]), k)
        
        results = []
        for i, idx in enumerate(I[0]):
            if idx >= 0 and idx < len(self.tickets_data):
                ticket = self.tickets_data[idx].copy()
                ticket['similarity_score'] = float(D[0][i])
                results.append(ticket)
        
        return results

    def generate_response(self, query: str, context: List[Dict[str, Any]]) -> str:
        # Preparar el contexto
        context_text = "\n\n".join([
            f"Documento: {item['documento']}\nContenido: {item['contenido']}"
            for item in context
        ])
        
        # Construir el prompt
        system_prompt = """Eres un experto en normativas de construcción que trabaja en NormaConsult. 
        Tu tarea es responder consultas técnicas basándote en la información proporcionada en el contexto.
        Debes ser preciso y citar las normativas específicas cuando sea posible."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Consulta: {query}\n\nContexto relevante:\n{context_text}"""}
        ]
        
        # Llamar a la API de OpenAI usando el cliente actualizado
        try:
            client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error al generar respuesta: {str(e)}"

    def refresh_indexes(self):
        """Actualizar los índices con nuevos documentos o tickets"""
        self.normativas_index = faiss.IndexFlatL2(384)
        self.tickets_index = faiss.IndexFlatL2(384)
        self._process_normativas()
        self._process_tickets()