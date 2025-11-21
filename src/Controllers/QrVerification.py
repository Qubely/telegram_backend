from flask import request, jsonify
from src.Classes.Database import Database
from datetime import datetime, timezone, timedelta

class QrVerification: 
    
    db_instance = Database()
    db = db_instance.get_db()
    QR_COLLECTION = db.qr_sessions  
    
    @staticmethod
    def qr_verification():
        auth_id = request.args.get("auth_id")
        if not auth_id:
            return jsonify({"status": "error", "detail": "auth_id missing"}), 400

        doc = QrVerification.QR_COLLECTION.find_one({"auth_id": auth_id})
        if not doc:
            return jsonify({"status": "not_found"}), 404
        created_at = doc.get("created_at")
        now_utc = datetime.now(timezone.utc)
        if created_at:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            if now_utc - created_at > timedelta(minutes=15):
                if doc.get("status") not in ("authorized", "error"):
                    QrVerification.QR_COLLECTION.update_one(
                        {"auth_id": auth_id},
                        {"$set": {"status": "expired", "updated_at": now_utc}}
                    )
                    doc["status"] = "expired"
        if doc.get("status") == "authorized":
            return jsonify({
                "status": "authorized",
                "user": doc.get("user", {})
            })
        return jsonify({
            "auth_id": auth_id,
            "qr_url": doc.get("qr_url"),
            "status": doc.get("status", "pending")
        })
