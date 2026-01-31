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
        self._warm_interval = 20  # 20 seconds
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

            # Unwrap single-item nested list: [[...]] -> [...]
            if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], (list, tuple)):
                embedding = embedding[0]

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
    """Adapter implementing furniture search using Qdrant vector database.

    Loads image embeddings and metadata from a remote Qdrant instance
    to support similarity search via the remote `LambdaCLIPService`.
    """

    def __init__(self, lambda_service: LambdaCLIPService | None = None):
        logger.info("Initializing Search Engine (Qdrant adapter)...")
        self.clip_service = lambda_service or LambdaCLIPService()

        # Defaults if initialization fails
        self.qdrant_client = None
        self.is_initialized = False

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            # Validate configuration
            if not Config.QDRANT_URL:
                logger.error("QDRANT_URL not configured")
                return

            if not Config.QDRANT_API_KEY:
                logger.error("QDRANT_API_KEY not configured")
                return

            # Initialize Qdrant client
            logger.info("Connecting to Qdrant at: %s", Config.QDRANT_URL)
            self.qdrant_client = QdrantClient(
                url=Config.QDRANT_URL,
                api_key=Config.QDRANT_API_KEY,
                timeout=30,
                prefer_grpc=False
                
            )

            # Verify connection and collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if Config.QDRANT_COLLECTION_NAME not in collection_names:
                logger.error(
                    "Collection '%s' not found in Qdrant. Available collections: %s",
                    Config.QDRANT_COLLECTION_NAME,
                    collection_names
                )
                return

            # Get collection info to verify it has embeddings
            collection_info = self.qdrant_client.get_collection(Config.QDRANT_COLLECTION_NAME)
            logger.info(
                "Successfully connected to collection '%s' with %d points",
                Config.QDRANT_COLLECTION_NAME,
                collection_info.points_count
            )

            self.is_initialized = True
            logger.info("Search Engine initialized successfully with Qdrant.")

        except Exception as e:
            logger.exception("CRITICAL ERROR initializing Qdrant search: %s", str(e))
            self.qdrant_client = None
            self.is_initialized = False

    def search(self, image_input, top_k: int = 4):
        """Search for similar furniture items using remote CLIP embedding and Qdrant.
        
        Args:
            image_input: PIL Image or file path
            top_k: Number of results to return
            
        Returns:
            list: Array of furniture items with metadata
        """
        logger.info("DEBUG : innit search for furniture items...")
        if not self.is_initialized or self.qdrant_client is None:
            logger.warning("Search service: Qdrant not initialized. Cannot perform search.")
            raise RuntimeError("Qdrant search service not initialized")

        if self.clip_service is None:
            logger.warning("Search service: CLIP service not initialized. Ensure LAMBDA_CLIP_URL is configured.")
            raise RuntimeError("CLIP service not initialized")

        try:
            # Normalize input to PIL Image
            if isinstance(image_input, str):
                image = Image.open(image_input).convert('RGB')
            else:
                image = image_input.convert('RGB')

            # Generate embedding via Lambda CLIP
            logger.info("Generating CLIP embedding via Lambda CLIP")
            query_embedding = self.clip_service.get_image_embedding(image)

            import numpy as _np

            query_embedding = _np.array(query_embedding, dtype=_np.float32)
            query_embedding = query_embedding / (_np.linalg.norm(query_embedding) + 1e-8)
            query_embedding = query_embedding.tolist()

            # Search in Qdrant
            logger.info("Searching Qdrant for similar furniture")
            search_results = self.qdrant_client.query_points(
                collection_name=Config.QDRANT_COLLECTION_NAME,
                query=query_embedding,
                limit=top_k,
                with_payload=True
            )

            results = []
            for hit in search_results.points:
                try:
                    payload = hit.payload or {}
                    score = hit.score

                    # Extract metadata from payload
                    title = payload.get('title') or payload.get('name', 'Unknown Item')
                    result_item = {
                        'score': float(score),
                        'title': title,
                        'price': str(payload.get('price', 'N/A')),
                        'source': payload.get('source', ''),
                        'image_url': payload.get('image_url', ''),
                        'search_query': f"{title} {payload.get('source', '')}"
                    }
                    results.append(result_item)

                except Exception as e:
                    logger.exception("Error processing search result: %s", str(e))
                    continue

            logger.info("Found %d results for furniture search", len(results))
            return results

        except Exception as e:
            logger.exception("Error during furniture search: %s", str(e))
            return []
