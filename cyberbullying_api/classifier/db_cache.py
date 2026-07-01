import hashlib
import json
import logging

from classifier.db_config import get_redis

logger = logging.getLogger("bullyguard")


async def get_cached_response(text: str) -> dict | None:
    r = await get_redis()
    if r:
        try:
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            res = await r.get(f"cloud_llm:{text_hash}")
            if res:
                return json.loads(res)
        except Exception as e:
            logger.warning("Redis error on get_cached_response", extra={"error": str(e)})
    return None


async def save_cached_response(text: str, response_dict: dict):
    r = await get_redis()
    if r:
        try:
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            await r.set(f"cloud_llm:{text_hash}", json.dumps(response_dict), ex=604800)  # Cache 7 hari
        except Exception as e:
            logger.warning("Redis error on save_cached_response", extra={"error": str(e)})
