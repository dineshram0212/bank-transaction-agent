import os
import numpy as np
import pandas as pd
import sqlite3
from sentence_transformers import SentenceTransformer
import chromadb
from more_itertools import batched
from utils import clean_text, remove_stopwords


class VectorStore:
    def __init__(
            self, 
            db_path: str = "./transactions.db",
            persist_dir: str = "./chroma_store", 
            collection_name: str = "transactions",
        ):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(collection_name)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.db_path = db_path
    
    def load_data(self, file_path: str, embeddings_path: str = "data_embeddings.npy"):
        df = pd.read_csv(file_path)
        df["uid"] = df.index
        df['merchant'] = df.merchant.fillna('')
        df['desc'] = df.desc.fillna('')
        df['combined'] = df.apply(lambda row: clean_text(row["desc"]) + " " + clean_text(row["merchant"]), axis=1)
        df = df.drop_duplicates(subset=['combined'])
        texts = df['combined'].tolist()
        ids = df['uid'].astype(str).tolist()
        metadatas = [{"client_id": clnt} for clnt in df["clnt_id"]]

        if os.path.exists(embeddings_path):
            vectors = np.load(embeddings_path)
        else:
            vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True).tolist()
            np.save(embeddings_path, vectors)
        
        for batch in batched(zip(ids, texts, vectors, metadatas), 500):
            b_ids, b_docs, b_vecs, b_meta = zip(*batch)
            self.collection.add(
                ids=list(b_ids),
                documents=list(b_docs),
                embeddings=list(b_vecs),
                metadatas=list(b_meta)
            )

    def get_vector_matched_uids(self, query: str, client_id: int, top_k: int = 100) -> list[int]:
        """
        Perform vector search for a given query and client_id.
        Returns a list of matched uids (as integers).
        """
        
        # Encode the query
        vector = self.model.encode([query], normalize_embeddings=True).tolist()

        # Perform ChromaDB vector search with client_id filter
        result = self.collection.query(
            query_embeddings=vector,
            n_results=top_k,
            where={"client_id": client_id},
            include=["documents"]
        )

        # Return list of matched uids as integers
        return list(map(int, result["ids"][0]))
    
    def get_unique_merchants_and_descriptions(self, query: str, client_id: int, top_k: int = 100) -> tuple[list[str], set[str]]:
        """
        Get unique merchants and descriptions from a list of uids.
        """
        query = remove_stopwords(query)
        uids = self.get_vector_matched_uids(query, client_id, top_k)
        if not uids:
            return {"merchants": [], "descriptions": []}

        placeholders = ",".join("?" for _ in uids)
        conn = sqlite3.connect(self.db_path)

        query = f"""
            SELECT desc, merchant
            FROM transactions
            WHERE uid IN ({placeholders})
        """
        df = pd.read_sql_query(query, conn, params=uids)
        conn.close()

        merchants = df["merchant"].dropna().str.lower().str.strip().unique().tolist()
        descriptions = df["desc"].dropna().apply(clean_text).str.lower().str.strip().unique().tolist()
        description_keywords = set((" ".join(descriptions)).split())

        return merchants, description_keywords

    def clear_collection(self):
        self.collection.delete()

