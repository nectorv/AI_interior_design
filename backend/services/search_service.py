"""Furniture search service using a remote Lambda CLIP inference service."""
import logging
import os
import numpy as np
import pandas as pd
from PIL import Image
from backend.core.config import Config
from backend.services.lambda_search_service import LambdaCLIPService

logger = logging.getLogger(__name__)


class FurnitureSearcher:
    """Service for searching furniture using image similarity via Lambda CLIP."""

    def __init__(self):
        logger.info("Initializing Search Engine...")

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
            self.df_data["clean_id"] = self.df_data["clean_id"].astype(str)

            # Create a lookup dictionary for fast access by ID
            self.product_lookup = self.df_data.set_index("clean_id").to_dict("index")
            logger.info("Loaded %d products from CSV", len(self.df_data))

            # 2. Load Embeddings (PKL) - Expecting a DataFrame
            logger.info("Loading embeddings from: %s", Config.EMBEDDINGS_FILE)
            self.df_embeddings = pd.read_pickle(Config.EMBEDDINGS_FILE)

            # Ensure the ID column is string (just like the CSV)
            if "clean_id" in self.df_embeddings.columns:
                self.df_embeddings["clean_id"] = self.df_embeddings["clean_id"].astype(str)

            # 3. Extract the Embedding Matrix
            logger.info("Stacking embeddings...")
            raw_embeddings = np.vstack(self.df_embeddings["embedding"].values)

            # Convert to numpy array (for compatibility with similarity calculations)
            self.dataset_embeddings = raw_embeddings.astype(np.float32)
            logger.info("Created embedding matrix with shape: %s", self.dataset_embeddings.shape)

            # 4. Initialize Lambda CLIP Service
            logger.info("Initializing Lambda CLIP service... (remote)")
            self.clip_service = LambdaCLIPService()
            logger.info("Search Engine Loaded successfully.")

        except Exception as e:
            logger.exception("CRITICAL ERROR loading search database: %s", str(e))
            self.df_data = None
            self.df_embeddings = None
            self.clip_service = None
            self.dataset_embeddings = None

    def search(self, query_image, top_k=5):
        """Search for similar furniture items.

        Args:
            query_image: PIL Image or path to image file
            top_k: Number of top results to return

        Returns:
            List of dictionaries containing product information
        """
        if self.df_data is None:
            logger.warning("Search service: Product database not loaded. Cannot perform search.")
            return []

        if self.clip_service is None:
            logger.warning("Search service: CLIP service not initialized. Ensure LAMBDA_CLIP_URL is configured.")
            return []

        try:
            # 1. Convert to PIL Image if needed
            if isinstance(query_image, str):
                image = Image.open(query_image).convert("RGB")
            else:
                image = query_image.convert("RGB")

            # 2. Generate embedding using remote Lambda CLIP
            logger.info("Generating CLIP embedding via Lambda CLIP")
            query_embedding = self.clip_service.get_image_embedding(image)

            # Convert to numpy array and normalize
            query_embedding = np.array(query_embedding, dtype=np.float32)
            query_embedding = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)

            # 3. Compute cosine similarity with all embeddings
            dataset_embeddings_normalized = self.dataset_embeddings / (
                np.linalg.norm(self.dataset_embeddings, axis=1, keepdims=True) + 1e-8
            )

            # Cosine similarity: dot product of normalized vectors
            similarity_scores = np.dot(dataset_embeddings_normalized, query_embedding)

            # 4. Get top K indices
            top_indices = np.argsort(similarity_scores)[::-1][:top_k]

            # 5. Build results
            results = []
            for idx in top_indices:
                try:
                    clean_id = self.df_embeddings.iloc[int(idx)]["clean_id"]
                    item = self.product_lookup.get(clean_id)
                    score = float(similarity_scores[idx])

                    if item:
                        search_query = f"{item.get('title', '')} {item.get('source', '')}"
                        results.append({
                            "score": score,
                            "title": item.get('title', 'Unknown Item'),
                            "price": str(item.get('price', 'N/A')),
                            "source": item.get('source', ''),
                            "image_url": item.get('image_url', ''),
                            "search_query": search_query
                        })
                except Exception:
                    logger.exception("Error retrieving item at index %s", idx)
                    continue

            logger.info("Found %d results for furniture search", len(results))
            return results

        except Exception as e:
            logger.exception("Error during furniture search: %s", str(e))
            return []

