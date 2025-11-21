import base64
import os
from datetime import datetime
class Helper : 
    def make_json_safe(obj):
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                key = "type" if k == "_" else k
                new_dict[key] = Helper.make_json_safe(v)
            return new_dict
        elif isinstance(obj, list):
            return [Helper.make_json_safe(v) for v in obj]
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode("utf-8")
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    async def fetch_avatar_url(client,me):
        photos = await client.get_profile_photos(me.id, limit=1)
        folder_path = "public/avatars"
        os.makedirs(folder_path, exist_ok=True)
        if photos:
            file_path = f"{folder_path}/{me.id}.jpg"
            await client.download_media(photos[0], file=file_path)
            base_url = os.getenv("APP_URL", "http://localhost:8000")
            avatar_path = os.getenv("AVATAR_PATH", "/avatars")  # should match folder served by web server
            avatar_url = f"{base_url}{avatar_path}/{me.id}.jpg"
            return avatar_url
        else:
            return 'https://telegram.org/img/t_logo.png'
        
    def short_text(text, max_len=30):
        return text if len(text) <= max_len else text[:max_len] + "..."

