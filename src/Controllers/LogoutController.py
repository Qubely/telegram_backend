from flask import request, jsonify
from src.Classes.Remote import Remote
from src.Classes.Database import Database
import asyncio
class LogoutController: 

    db_instance = Database()
    db = db_instance.get_db()
    
    def logout():
        phone = request.form.get("phone") or (request.json.get("phone") if request.is_json else None)
        if not phone:
            return jsonify({"status": "error", "detail": "phone missing"}), 400
        result = asyncio.run(LogoutController.do_logout(phone))
        print("Logout result:", result)
        return jsonify(result)
       
    async def do_logout(phone):
        client = await Remote.tg_client(phone)
        await client.connect()
        try:
            if await client.is_user_authorized():
                await client.log_out()
            await client.disconnect()
            LogoutController.db.sessions.delete_one({"phone": phone.strip().replace("+", "").replace(" ", "")})
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
