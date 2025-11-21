
from flask import request, jsonify
import asyncio
from src.Classes.Remote import Remote
from src.Classes.Helper import Helper
from datetime import datetime, timezone
from src.Classes.Database import Database
from telethon import TelegramClient, events
from telethon.errors import (
    PhoneCodeInvalidError,
    SessionPasswordNeededError
)


class VerifyUserController:

    db_instance = Database()
    db = db_instance.get_db()

    def verify():
        phone = request.form.get("phone") or (
            request.json.get("phone") if request.is_json else None)
        code = request.form.get("code") or (
            request.json.get("code") if request.is_json else None)
        phone_code_hash = request.form.get("phone_code_hash") or (
            request.json.get("phone_code_hash") if request.is_json else None
        )
        if not all([phone, code, phone_code_hash]):
            return jsonify({"status": "error", "detail": "phone/code/phone_code_hash missing"}), 400
        result = asyncio.run(VerifyUserController.do_verify( phone, code, phone_code_hash))
        print("Verify result:", result)
        return jsonify(result)

    async def do_verify(phone: str, code: int, phone_code_hash: str):
        client = await Remote.tg_client(phone)
        await client.connect()
        try:
            if await client.is_user_authorized():
                me = await client.get_me()
                user_data = Helper.make_json_safe(me.to_dict())
                await VerifyUserController.save_user_if_not_exists(client, user_data,me)
                await client.disconnect()
                return {"status": "already_authorized", "user": user_data}
            user = await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
            if not user:
                await client.disconnect()
                return {"status": "error", "detail": "Invalid OTP or hash"}
            me = await client.get_me()
            user_data = Helper.make_json_safe(me.to_dict())
            await VerifyUserController.save_user_if_not_exists(client, user_data,me)
            await client.send_message("me", "Flask API login successful!")
            await client.disconnect()
            return {"status": "authorized", "user": user_data}
        
        except SessionPasswordNeededError:
            await client.disconnect()
            return {"status": "2fa_required"}

        except PhoneCodeInvalidError:
            await client.disconnect()
            return {"status": "error", "detail": "Invalid OTP"}

        except Exception as e:
            await client.disconnect()
            return {"status": "error", "detail": str(e)}


    async def save_user_if_not_exists(client,user,me):
        avatar_url = await Helper.fetch_avatar_url(client,me)
        telegram_id = user.get("id") 
        users_collection = VerifyUserController.db["users"] 
        existing = users_collection.find_one({"telegram_id": telegram_id})
        if existing:
            return existing
        new_user = {
            "telegram_id": telegram_id,
            "phone": user.get("phone"),
            "username": user.get("username"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "is_bot": user.get("bot", False),
            "avatar_url": avatar_url
        }
        result = users_collection.insert_one(new_user)
        new_user["_id"] = str(result.inserted_id)
    

        
