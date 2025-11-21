import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from src.Classes.Database import Database


class Remote:

    API_ID = int(os.getenv("TG_API_ID", "20767444"))
    API_HASH = os.getenv("TG_API_HASH", "2ca0cb711803e1aae9e45d34eb81e57a")

    db_instance = Database()
    db = db_instance.get_db()
    
    @staticmethod
    async def tg_client(phone: str):
        safe_phone = phone.strip().replace("+", "").replace(" ", "")
        doc = Remote.db.sessions.find_one({"phone": safe_phone})
        if doc and "session_string" in doc and doc["session_string"]:
            session_str = doc["session_string"]
            print(f"Restoring existing session for {phone}")
        else:
            session_str = ""
            print(f"No session found for {phone}, creating new one.")
        client = TelegramClient(
            StringSession(session_str),
            Remote.API_ID,
            Remote.API_HASH,
            auto_reconnect=True,
            connection_retries=None,  
            retry_delay=2,            
            request_retries=5,
            flood_sleep_threshold=600 
        )
        return client

    @staticmethod
    def api():
        print("ok")
