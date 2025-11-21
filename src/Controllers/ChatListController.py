from flask import request, jsonify
import asyncio
from src.Classes.Remote import Remote
from src.Classes.Database import Database
from telethon.tl.types import InputPeerEmpty
import base64
from flask import url_for
from src.Classes.Helper import Helper
import os
TELEGRAM_DEFAULT_AVATAR = "https://telegram.org/img/t_logo.png"
UPLOAD_DIR = "static/chat_avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatListController:

    db_instance = Database()
    db = db_instance.get_db()
    users_collection = db["users"]

    @staticmethod
    def chat_list():
        phone = request.args.get("phone")
        if not phone:
            return jsonify({"status": "error", "detail": "phone missing"}), 400

        page_str = request.args.get("page", "1")
        try:
            page = int(page_str)
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        limit = 10
        offset = (page - 1) * limit

        data = asyncio.run(ChatListController._fetch_chats(phone, offset, limit))
        return jsonify(data)

    @staticmethod
    async def _fetch_chats(phone, offset, limit):
        client = await Remote.tg_client(phone)
        await client.connect()

        dialogs = []
        async for dialog in client.iter_dialogs():
            dialogs.append(dialog)
        total_chats = len(dialogs)
        paginated_dialogs = dialogs[offset:offset + limit]
        result = []
        for dialog in paginated_dialogs:
            chat = dialog.entity
            avatar = await ChatListController.chat_avatar(client, chat)
            title = ChatListController.chat_title(chat)
            last_message_data = ChatListController.get_last_message_data(dialog)
            result.append({
                "chat_id": chat.id,
                "chat_title": title,
                "avatar": avatar,
                "last_message_data" : last_message_data
            })

        await client.disconnect()

        return {
            "status": "success",
            "page": (offset // limit) + 1,
            "limit": limit,
            "total_chats": total_chats,
            "last_message": {
                "text": "",
                "time": "",
                "sent": True,
                "seen": False
            },
            "data": result
        }

    async def chat_avatar(client, chat):
        try:
            file_name = f"{chat.id}.jpg"
            file_path = os.path.join(UPLOAD_DIR, file_name)
            if os.path.isfile(file_path):
                return url_for('static', filename=f"chat_avatars/{file_name}", _external=True)
            if getattr(chat, 'photo', None):
                await client.download_profile_photo(chat, file=file_path)
                if os.path.isfile(file_path):
                    return url_for('static', filename=f"chat_avatars/{file_name}", _external=True)
            return TELEGRAM_DEFAULT_AVATAR
        except Exception:
            return TELEGRAM_DEFAULT_AVATAR

        
    @staticmethod
    def chat_title(chat):
        if hasattr(chat, 'title') and chat.title:
            return chat.title
        else:
            first_name = getattr(chat, 'first_name', '') or ''
            last_name = getattr(chat, 'last_name', '') or ''
            return (first_name + ' ' + last_name).strip() or 'Private Chat'
    
    @staticmethod   
    def get_last_message_data(dialog):
        last_msg = dialog.message
        if last_msg:
            try:
                msg_time = last_msg.date.strftime("%I:%M %p")
            except:
                msg_time = ""
            last_message_data = {
                "text": Helper.short_text(getattr(last_msg, 'message', '') or '',120), 
                "time": msg_time,
                "sent": getattr(last_msg, 'out', True),          
                "seen": getattr(last_msg, 'mentioned', False)  
            }
        else:
            last_message_data = {
                "text": "",
                "time": "",
                "sent": True,
                "seen": False
            }
        
        return last_message_data
    
    

    
