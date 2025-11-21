import uuid
import concurrent.futures
import asyncio,threading
from datetime import datetime, timezone
from src.Classes.Remote import Remote
from telethon import TelegramClient, events
import traceback, base64, asyncio
from flask import request, jsonify
from src.Classes.Helper import Helper
from src.Classes.Database import Database
class QrLoginController:
    
    db_instance = Database()
    db = db_instance.get_db()
    QR_CACHE = {}
    QR_COLLECTION = db.qr_sessions
    def do_qr_login():
        try:
            auth_id = str(uuid.uuid4())
            future = Helper.schedule_coro(QrLoginController.do_qr_create(auth_id))
            result = future.result(timeout=15)
            return jsonify(result)
        except concurrent.futures.TimeoutError:
            return jsonify({"status": "error", "detail": "QR creation timeout"}), 500
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"status": "error", "detail": str(e)}), 500
        
    async def do_qr_create(auth_id):
        client = Remote.qr_client(auth_id)
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            await client.disconnect()
            return {"status": "already_authorized", "user": me.to_dict()}

        qr = await client.qr_login()
        QrLoginController.QR_CACHE[auth_id] = {"client": client, "qr": qr}
        QrLoginController.QR_COLLECTION.update_one(
            {"auth_id": auth_id},
            {"$set": {
                "auth_id": auth_id,
                "qr_url": qr.url,
                "status": "pending",
                "created_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
        print(f"QR created: {auth_id}")
        print(f"{qr.url}")
        asyncio.create_task(QrLoginController.wait_for_qr(auth_id))
        return {"status": "ok", "auth_id": auth_id, "qr_url": qr.url}
        
    async def wait_for_qr(auth_id: str):
        
        try:
            cache = QrLoginController.QR_CACHE.get(auth_id)
            if not cache:
                print(f"No cache found for {auth_id}")
                return

            client = cache["client"]
            qr = cache["qr"]

            if not client.is_connected():
                await client.connect()

            print(f"[wait_for_qr] Waiting for Telegram auth for {auth_id}")

            user = None
            for attempt in range(12): 
                try:
                    user = await asyncio.wait_for(qr.wait(), timeout=50)
                    if user:
                        break
                except asyncio.TimeoutError:
                    if not client.is_connected():
                        await client.connect()
                    print(f"waiting... ({attempt + 1}/12)")
                    continue

            if not user:
                print(f"Timeout: No authorization for {auth_id}")
                QrLoginController.QR_COLLECTION.update_one(
                    {"auth_id": auth_id},
                    {"$set": {"status": "expired", "updated_at": datetime.now(timezone.utc)}}
                )
                await client.disconnect()
                return

            phone = getattr(user, "phone", None)
            if not phone:
                phone = f"qr_{auth_id[:8]}"

            print(f"Telegram QR Authorized → {user.first_name} ({phone})")

            await QrLoginController.save_session(phone, client)


            def make_json_safe(obj):
                if isinstance(obj, dict):
                    return {k: make_json_safe(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_json_safe(v) for v in obj]
                elif isinstance(obj, bytes):
                    return base64.b64encode(obj).decode("utf-8")
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                else:
                    return obj

            user_data = make_json_safe(user.to_dict())

            QrLoginController.QR_COLLECTION.update_one(
                {"auth_id": auth_id},
                {"$set": {
                    "status": "authorized",
                    "user": user_data,
                    "phone": phone,
                    "updated_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )

            print(f"MongoDB updated → authorized for {auth_id} ({phone})")
            await client.disconnect()

        except Exception as e:
            print(f"Fatal in wait_for_qr: {e}")
            print(traceback.format_exc())
            try:
                await client.disconnect()
            except:
                pass
            
    async def save_session(phone: str, client: TelegramClient):
        session_str = client.session.save()
        safe_phone = phone.strip().replace("+", "").replace(" ", "")
        QrLoginController.db.sessions.update_one(
            {"phone": safe_phone},
            {"$set": {"session_string": session_str, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        print(f"Session saved for {phone}")



