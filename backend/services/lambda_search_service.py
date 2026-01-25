"""Client for remote CLIP inference hosted on an AWS Lambda URL.

This module calls a user-provided Lambda URL which accepts raw image bytes
and returns a JSON payload with an `embedding` key containing a 512-dim list.
"""
import io
import logging
from typing import List

import requests
import threading
import time
from PIL import Image

from backend.core.config import Config

logger = logging.getLogger(__name__)


class LambdaCLIPService:
    """Simple client that posts image bytes to a Lambda endpoint and returns embedding."""

    def __init__(self, url: str | None = None, timeout: int = 30):
        self.url = url or Config.LAMBDA_CLIP_URL
        self.timeout = timeout
        # warm control
        self._last_warm = 0.0
        self._warm_interval = 60  # 1 minute default
        if not self.url:
            logger.warning("Lambda CLIP URL not configured; LambdaCLIPService will be disabled")

    def _image_to_bytes(self, image: Image.Image) -> bytes:
        buf = io.BytesIO()
        image = image.convert("RGB")
        image.save(buf, format="JPEG")
        return buf.getvalue()

    def get_image_embedding(self, image_input) -> List[float]:
        """Send image to Lambda and return 512-d embedding as list of floats.

        Args:
            image_input: PIL Image or file path

        Returns:
            list[float]: 512-d embedding
        """
        if not self.url:
            raise ValueError("Lambda CLIP URL not configured")

        # Normalize input to bytes
        if isinstance(image_input, str):
            with open(image_input, "rb") as f:
                image_bytes = f.read()
        elif isinstance(image_input, Image.Image):
            image_bytes = self._image_to_bytes(image_input)
        else:
            raise ValueError(f"Unsupported image_input type: {type(image_input)}")

        headers = {"Content-Type": "application/octet-stream"}

        try:
            resp = requests.post(self.url, data=image_bytes, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            payload = resp.json()

            if not isinstance(payload, dict) or "embedding" not in payload:
                raise ValueError(f"Unexpected response from Lambda: {payload}")

            embedding = payload["embedding"]

            # Common response shapes: [512], [[512]], or {'embedding': [512]}
            # Unwrap single-item nested list: [[...]] -> [...]
            if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], (list, tuple)):
                embedding = embedding[0]

            # If embedding came wrapped in a dict (rare), extract
            if isinstance(embedding, dict) and "embedding" in embedding:
                embedding = embedding["embedding"]

            # If embedding is a numpy-like object, try to convert
            try:
                import numpy as _np
                if isinstance(embedding, _np.ndarray):
                    embedding = embedding.tolist()
            except Exception:
                pass

            if not isinstance(embedding, list) or len(embedding) != 512:
                raise ValueError(f"Embedding shape unexpected: {type(embedding)} len={len(embedding) if hasattr(embedding, '__len__') else 'n/a'}")

            # Ensure float values
            return [float(x) for x in embedding]

        except requests.RequestException as e:
            logger.exception("HTTP error calling Lambda CLIP: %s", str(e))
            raise

    def warm_async(self, force: bool = False) -> bool:
        """Asynchronously send a small request to the Lambda to reduce cold-start latency.

        Returns True if a warm request was scheduled, False if skipped due to interval.
        """
        now = time.time()
        if not force and (now - self._last_warm) < self._warm_interval:
            return False

        def _warm():
            try:
                # Create a minimal 1x1 JPEG
                img = Image.new("RGB", (1, 1), color=(255, 255, 255))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                data = buf.getvalue()

                headers = {"Content-Type": "application/octet-stream"}
                resp = requests.post(self.url, data=data, headers=headers, timeout=max(5, self.timeout))
                resp.raise_for_status()
                logger.info("Lambda CLIP warm ping successful (status=%s)", resp.status_code)
            except Exception as e:
                logger.debug("Lambda CLIP warm ping failed: %s", str(e))
            finally:
                try:
                    self._last_warm = time.time()
                except Exception:
                    pass

        t = threading.Thread(target=_warm, daemon=True)
        t.start()
        return True


class LambdaFurnitureSearcher:
    """Adapter implementing the original `FurnitureSearcher` loading logic.

    Loads CSV metadata from `Config.CSV_FILE` and embeddings from
    `Config.EMBEDDINGS_FILE` (pickle) into a stacked numpy matrix to
    support similarity search via the remote `LambdaCLIPService`.
    """

    def __init__(self, lambda_service: LambdaCLIPService | None = None):
        logger.info("Initializing Search Engine (Lambda adapter)...")
        self.clip_service = lambda_service or LambdaCLIPService()

        # Defaults if loading fails
        self.df_data = None
        self.df_embeddings = None
        self.dataset_embeddings = None
        self.product_lookup = {}

        try:
            import os as _os
            import numpy as _np
            import pandas as _pd

            # 1. Check files exist
            if not _os.path.exists(Config.CSV_FILE):
                logger.error("CSV file not found: %s", Config.CSV_FILE)
                self.df_data = None
                return

            if not _os.path.exists(Config.EMBEDDINGS_FILE):
                logger.error("Embeddings file not found: %s", Config.EMBEDDINGS_FILE)
                self.df_data = None
                return

            # 2. Load metadata CSV
            logger.info("Loading CSV data from: %s", Config.CSV_FILE)
            self.df_data = _pd.read_csv(Config.CSV_FILE)
            if 'clean_id' in self.df_data.columns:
                self.df_data['clean_id'] = self.df_data['clean_id'].astype(str)

            # Create lookup by clean_id
            self.product_lookup = self.df_data.set_index('clean_id').to_dict('index')
            logger.info("Loaded %d products from CSV", len(self.df_data))

            # 3. Load embeddings pickle (expected to be a DataFrame with 'embedding' and 'clean_id')
            logger.info("Loading embeddings from: %s", Config.EMBEDDINGS_FILE)
            self.df_embeddings = _pd.read_pickle(Config.EMBEDDINGS_FILE)

            if 'clean_id' in self.df_embeddings.columns:
                self.df_embeddings['clean_id'] = self.df_embeddings['clean_id'].astype(str)

            # Stack embeddings into matrix
            logger.info("Stacking embeddings...")
            raw_embeddings = _np.vstack(self.df_embeddings['embedding'].values)
            self.dataset_embeddings = raw_embeddings.astype(_np.float32)
            logger.info("Created embedding matrix with shape: %s", self.dataset_embeddings.shape)

            # 4. Ensure CLIP service exists
            logger.info("Initializing Lambda CLIP service... (remote)")
            # self.clip_service already set

            logger.info("Search Engine Loaded successfully.")

        except Exception as e:
            logger.exception("CRITICAL ERROR loading search database: %s", str(e))
            self.df_data = None
            self.df_embeddings = None
            self.clip_service = None
            self.dataset_embeddings = None

    def search(self, image_input, top_k: int = 4):
        """Search for similar furniture items using remote CLIP embedding."""
        if self.df_data is None:
            logger.warning("Search service: Product database not loaded. Cannot perform search.")
            raise RuntimeError("Embeddings or dataset not loaded; search unavailable")

        if self.clip_service is None:
            logger.warning("Search service: CLIP service not initialized. Ensure LAMBDA_CLIP_URL is configured.")
            raise RuntimeError("CLIP service not initialized")

        try:
            # Normalize input to PIL Image
            if isinstance(image_input, str):
                image = Image.open(image_input).convert('RGB')
            else:
                image = image_input.convert('RGB')

            # Generate embedding
            logger.info("Generating CLIP embedding via Lambda CLIP")
            query_embedding = self.clip_service.get_image_embedding(image)

            import numpy as _np

            query_embedding = _np.array(query_embedding, dtype=_np.float32)
            query_embedding = query_embedding / (_np.linalg.norm(query_embedding) + 1e-8)

            # Normalize dataset embeddings
            dataset_embeddings_normalized = self.dataset_embeddings / (
                _np.linalg.norm(self.dataset_embeddings, axis=1, keepdims=True) + 1e-8
            )

            similarity_scores = _np.dot(dataset_embeddings_normalized, query_embedding)

            top_indices = _np.argsort(similarity_scores)[::-1][:top_k]

            results = []
            for idx in top_indices:
                try:
                    clean_id = self.df_embeddings.iloc[int(idx)]['clean_id']
                    item = self.product_lookup.get(clean_id)
                    score = float(similarity_scores[idx])

                    if item:
                        search_query = f"{item.get('title', '')} {item.get('source', '')}"
                        results.append({
                            'score': score,
                            'title': item.get('title', 'Unknown Item'),
                            'price': str(item.get('price', 'N/A')),
                            'source': item.get('source', ''),
                            'image_url': item.get('image_url', ''),
                            'search_query': search_query
                        })
                except Exception:
                    logger.exception("Error retrieving item at index %s", idx)
                    continue

            logger.info("Found %d results for furniture search", len(results))
            return results

        except Exception as e:
            logger.exception("Error during furniture search: %s", str(e))
            return []
