import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from utils import clean_text

class VectorStore:
    def __init__(
            self, 
            persist_dir: str = "./chroma_store", 
            collection_name: str = "transactions",
            embeddings: str = "data_embeddings.npy"
        ):
        self.client = chromadb.Client(Settings(persist_directory=persist_dir))
        self.collection = self.client.get_or_create_collection(collection_name)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings_path = embeddings
    
    def load_data(self, file_path: str):
        df = pd.read_csv(file_path)
        df['cat'] = df['cat'].fillna('Uncategorized')
        df['merchant'] = df['merchant'].fillna('')
        df = df.dropna(subset=['clnt_id', 'desc']).copy()

        df['combined'] = df.apply(lambda row: clean_text(str(row['desc'])) + ' ' + clean_text(str(row['merchant'])), axis=1)
        self.full_df = df  
        df = df.drop_duplicates(subset=['clnt_id', 'combined']).reset_index(drop=True)

        self.df = df
        self.docs = df['combined'].tolist()
        self.ids = [str(i) for i in range(len(df))]
        self.metadatas = df[['clnt_id', 'cat']].to_dict(orient='records')

        if os.path.exists(self.embeddings_path):
            self.embeddings = np.load(self.embeddings_path)
        else:
            self.embeddings = self.model.encode(self.docs, show_progress_bar=True).astype(np.float32)
            np.save(self.embeddings_path, self.embeddings)
        
        self.batch_add_to_chroma_meta()

        
    def batch_add_to_chroma_meta(self, batch_size=1000):
        for i in range(0, len(self.docs), batch_size):
            self.collection.add(
                documents=self.docs[i:i+batch_size],
                embeddings=self.embeddings[i:i+batch_size],
                ids=self.ids[i:i+batch_size],
                metadatas=self.metadatas[i:i+batch_size]
            )
    
    def clear_collection(self):
        self.collection.delete()

    def search(self, query: str, client_id: int, category: str, max_k: int = 5):
        where = {'$and': [
            {'clnt_id': {'$eq': client_id}},
            {'cat': {'$eq': category}}]}

        query_vec = self.model.encode([clean_text(query)]).tolist()
        result = self.collection.query(
            query_embeddings=query_vec,
            n_results=max_k,
            include=["documents"],
            where=where
        )

        docs = set(result['documents'][0])
        return self.full_df[(self.full_df['combined'].isin(docs)) & 
                       (self.full_df['clnt_id'] == client_id) & 
                       (self.full_df['cat'] == category)] 
    
    def semantic_search(self, query, client_id, category, threshold=0.75, max_k=500):
        where = {'$and': [
            {'clnt_id': {'$eq': int(client_id)}},
            {'cat': {'$eq': category}}
        ]}
        query_vec = self.model.encode([clean_text(query)]).tolist()

        result = self.collection.query(
            query_embeddings=query_vec,
            n_results=max_k,
            include=["documents", "distances"],
            where=where
        )

        filtered_docs = [
            doc for doc, dist in zip(result["documents"][0], result["distances"][0])
            if dist < (1 - threshold)
        ]

        return self.full_df[
            (self.full_df["combined"].isin(filtered_docs)) &
            (self.full_df["clnt_id"] == int(client_id)) &
            (self.full_df["cat"] == category)
        ]

