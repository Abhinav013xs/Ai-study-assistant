import os
import logging
from typing import List, Dict, Any, Optional
try:
    import chromadb
except ImportError:
    chromadb = None

from app.core.config import settings
from app.services.embeddings import embeddings_service

logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self):
        self.client = None
        if chromadb is None:
            logger.warning("ChromaDB package is not installed. Similarity search is disabled.")
            return

        # Create persist directory if it does not exist
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        
        # Initialize persistent Client
        try:
            self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB PersistentClient: {str(e)}")
            # Fallback to ephemeral/in-memory client if persistent client fails
            self.client = chromadb.Client()

    def get_or_create_collection(self, collection_name: str = "study_materials"):
        """
        Retrieves or creates a ChromaDB collection.
        """
        if not self.client:
            raise RuntimeError("ChromaDB client is not initialized.")
        try:
            return self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Error getting/creating collection {collection_name}: {str(e)}")
            raise e

    def add_chunks(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        collection_name: str = "study_materials"
    ) -> bool:
        """
        Indexes text chunks and their embeddings into ChromaDB.
        """
        if not ids:
            return False
            
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Generate embeddings
            embeddings = embeddings_service.get_embeddings(texts)
            
            # Upsert into ChromaDB
            collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Successfully indexed {len(ids)} chunks to ChromaDB.")
            return True
        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {str(e)}")
            return False

    def query_similarity(
        self,
        query_text: str,
        limit: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
        collection_name: str = "study_materials"
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB for semantically similar chunks.
        Applies metadata filters (e.g. user_id, subject_id, file_ids).
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Generate query embedding
            query_embedding = embeddings_service.get_embedding(query_text)
            
            # Query collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter
            )
            
            # Parse results to a readable dictionary format
            parsed_results = []
            if results and results.get("documents"):
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)
                ids = results["ids"][0]
                
                for idx in range(len(documents)):
                    parsed_results.append({
                        "id": ids[idx],
                        "document": documents[idx],
                        "metadata": metadatas[idx],
                        "distance": distances[idx]
                    })
            return parsed_results
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {str(e)}")
            return []

    def delete_by_filter(self, where_filter: Dict[str, Any], collection_name: str = "study_materials") -> bool:
        """
        Deletes items in ChromaDB matching a metadata filter.
        Used when a file is deleted (e.g. delete chunks where file_id == X).
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(where=where_filter)
            logger.info(f"Deleted items in vector DB matching filter: {where_filter}")
            return True
        except Exception as e:
            logger.error(f"Error deleting items in vector DB: {str(e)}")
            return False

vector_db_service = VectorDBService()
