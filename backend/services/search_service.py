"""Furniture search service using CLIP model."""
import logging
import os
import torch
import numpy as np
import pandas as pd
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from backend.core.config import Config

logger = logging.getLogger(__name__)


class FurnitureSearcher:
    """Service for searching furniture using image similarity."""
    
    def __init__(self):
        """Initialize the search service with CLIP model and dataset."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading Search Engine on %s...", self.device)
        
        # Check if required files exist
        if not os.path.exists(Config.CSV_FILE):
            logger.error("CSV file not found: %s", Config.CSV_FILE)
            self.df_data = None
            return
            
        if not os.path.exists(Config.EMBEDDINGS_FILE):
            logger.error("Embeddings file not found: %s", Config.EMBEDDINGS_FILE)
            self.df_data = None
            return
        
        try:
            # 1. Load Metadata (CSV)
            logger.info("Loading CSV data from: %s", Config.CSV_FILE)
            self.df_data = pd.read_csv(Config.CSV_FILE)
            self.df_data['clean_id'] = self.df_data['clean_id'].astype(str)
            
            # Create a lookup dictionary for fast access by ID
            self.product_lookup = self.df_data.set_index('clean_id').to_dict('index')
            logger.info("Loaded %d products from CSV", len(self.df_data))

            # 2. Load Embeddings (PKL) - Expecting a DataFrame
            logger.info("Loading embeddings from: %s", Config.EMBEDDINGS_FILE)
            self.df_embeddings = pd.read_pickle(Config.EMBEDDINGS_FILE)
            
            # Ensure the ID column is string (just like the CSV)
            if 'clean_id' in self.df_embeddings.columns:
                self.df_embeddings['clean_id'] = self.df_embeddings['clean_id'].astype(str)
            
            # 3. Extract the Embedding Matrix
            logger.info("Stacking embeddings...")
            raw_embeddings = np.vstack(self.df_embeddings['embedding'].values)
            
            # Convert to Tensor
            self.dataset_tensor = torch.from_numpy(raw_embeddings).float().to(self.device)
            logger.info("Created embedding tensor with shape: %s", self.dataset_tensor.shape)
            
            # 4. Load Model
            logger.info("Loading CLIP model: %s", Config.MODEL_ID)
            self.model = CLIPModel.from_pretrained(Config.MODEL_ID).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(Config.MODEL_ID)
            logger.info("Search Engine Loaded successfully.")
            
        except Exception as e:
            logger.exception("CRITICAL ERROR loading search database: %s", str(e))
            self.df_data = None
            self.df_embeddings = None
            self.model = None
            self.processor = None

    def search(self, query_image, top_k=5):
        """Search for similar furniture items.
        
        Args:
            query_image: PIL Image or path to image file
            top_k: Number of top results to return
        
        Returns:
            List of dictionaries containing product information
        """
        if self.df_data is None or self.model is None:
            logger.warning("Search service not properly initialized. Cannot perform search.")
            return []

        # 1. Process Image
        if isinstance(query_image, str):
            image = Image.open(query_image).convert("RGB")
        else:
            image = query_image.convert("RGB")

        inputs = self.processor(images=image, return_tensors="pt").to(self.device)

        # 2. Embedding & Similarity
        with torch.no_grad():
            query_feature = self.model.get_image_features(**inputs)
            # Normalize (Same as working code)
            query_feature = query_feature / query_feature.norm(p=2, dim=-1, keepdim=True)

        # Matrix Mult (Equivalent to Cosine Similarity on normalized vectors)
        similarity_scores = (query_feature @ self.dataset_tensor.T).squeeze(0)
        
        # 3. Top K
        values, indices = similarity_scores.topk(top_k)
        
        results = []
        for score, idx in zip(values, indices):
            idx = idx.item()  # This is the index in the EMBEDDINGS file
            
            # 4. Retrieve ID from Embedding DF, then lookup in CSV
            try:
                clean_id = self.df_embeddings.iloc[idx]['clean_id']
                item = self.product_lookup.get(clean_id)
                
                if item:
                    search_query = f"{item.get('title', '')} {item.get('source', '')}"

                    results.append({
                        "score": float(score.item()),
                        "title": item.get('title', 'Unknown Item'),
                        "price": str(item.get('price', 'N/A')),
                        "source": item.get('source', ''),
                        "image_url": item.get('image_url', ''),
                        "search_query": search_query
                    })
            except Exception:
                logger.exception("Error retrieving item at index %s", idx)
                continue
        
        return results

