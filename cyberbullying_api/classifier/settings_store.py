import os
import json
import logging

logger = logging.getLogger("bullyguard")
from classifier.db_config import get_redis

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "settings.json")

DEFAULT_SETTINGS = {
    "webhook_url": "",
    "webhook_enabled": False,
    "ensemble_weights": {
        "ml_toxic": 0.5,
        "tr_toxic": 0.5,
        "ml_bully": 0.65,
        "tr_bully": 0.35
    }
}

def get_settings_sync():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            settings = DEFAULT_SETTINGS.copy()
            settings.update(data)
            return settings
    except Exception:
        return DEFAULT_SETTINGS.copy()

async def get_settings():
    # Try Redis first
    r = await get_redis()
    if r:
        try:
            val = await r.get("system_settings")
            if val:
                return json.loads(val)
        except Exception:
            pass
            
    settings = get_settings_sync()
    if r:
        try:
            await r.set("system_settings", json.dumps(settings))
        except Exception:
            pass
    return settings

async def save_settings(settings: dict):
    final_settings = DEFAULT_SETTINGS.copy()
    final_settings.update(settings)
    
    # Save to local file
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(final_settings, f, indent=4)
    except Exception as e:
        logger.error("Error saving settings file", extra={"error": str(e)})
        
    # Sync with Redis
    r = await get_redis()
    if r:
        try:
            await r.set("system_settings", json.dumps(final_settings))
            await r.publish("settings_reload", "reload")
        except Exception:
            pass
    return final_settings
