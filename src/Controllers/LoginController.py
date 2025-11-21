from flask import Flask, redirect, send_file, has_request_context,request,jsonify
from telethon.errors import ( PhoneNumberInvalidError)
from telethon import TelegramClient, events
import asyncio
from src.Classes.Remote import Remote
from src.Classes.Database import Database
from datetime import datetime, timezone
class LoginController:
    
    db_instance = Database()
    db = db_instance.get_db()
    
    def login():
        phone = request.form.get("phone") or (request.json.get("phone") if request.is_json else None)
        if not phone:
            return jsonify({"status": "error", "detail": "phone missing"}), 400

        async def send_code():
            client = await  Remote.tg_client(phone)
            await client.connect()
            try:
                if await client.is_user_authorized():
                    await client.disconnect()
                    return {"status": "already_authorized"}
                sent = await client.send_code_request(phone)
                await LoginController.save_login(phone, client)
                await client.disconnect()
                return {"status": "code_sent", "phone_code_hash": sent.phone_code_hash}
            except PhoneNumberInvalidError:
                return {"status": "error", "detail": "Invalid phone number"}
            except Exception as e:
                return {"status": "error", "detail": str(e)}

        result = asyncio.run(send_code())
        print("Login result:", result)
        return jsonify(result) 
    
    async def save_login(phone: str, client: TelegramClient):
        session_str = client.session.save()
        safe_phone = phone.strip().replace("+", "").replace(" ", "")
        LoginController.db.sessions.update_one(
            {"phone": safe_phone},
            {"$set": {"session_string": session_str, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        print(f"Session saved for {phone}")