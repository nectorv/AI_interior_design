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
        self._warm_interval = 20  # 20 seconds default
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
