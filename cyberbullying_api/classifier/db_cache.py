import os
import json
import hashlib
from typing import Dict, Any
from classifier.db_config import get_redis

async def get_cached_response(text: str) -> Dict[str, Any] | None:
    r = await get_redis()
    if r:
        try:
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            res = await r.get(f"cloud_llm:{text_hash}")
            if res:
                return json.loads(res)
        except Exception as e:
            print(f"Warning: Redis error pada get_cached_response: {e}")
    return None

async def save_cached_response(text: str, response_dict: Dict[str, Any]):
    r = await get_redis()
    if r:
        try:
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            await r.set(f"cloud_llm:{text_hash}", json.dumps(response_dict), ex=604800) # Cache 7 hari
        except Exception as e:
            print(f"Warning: Redis error pada save_cached_response: {e}")
