import os
import sys
import json, time, os, asyncio, threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask
from src.Controllers.ApiTestController import ApiTestController
from src.Controllers.LoginController import LoginController
from src.Controllers.VerifyUserController import VerifyUserController
from src.Controllers.ChatListController import ChatListController
from src.Controllers.LogoutController import LogoutController
from src.Controllers.QrLoginController import QrLoginController
from src.Controllers.QrVerification import QrVerification

from flask_sock import Sock
from telethon import events

app = Flask(__name__)
sock = Sock(app)
connected_clients = set()

bg_loop = asyncio.new_event_loop()
def start_loop():
    asyncio.set_event_loop(bg_loop)
    bg_loop.run_forever()
threading.Thread(target=start_loop, daemon=True).start()

def schedule_coro(coro):
    return asyncio.run_coroutine_threadsafe(coro, bg_loop)

@app.route("/test", methods=["POST"])
def test_route():
    return ApiTestController.test_api()

@app.route("/login", methods=["POST"])
def login():
    return LoginController.login()

@app.route("/verify", methods=["POST"])
def verify():
    return VerifyUserController.verify()

@app.route("/chat-list", methods=["GET"])
def chat_list():
    return ChatListController.chat_list()

@app.route("/logout", methods=["POST"])
def logout():
    return LogoutController.logout()

@app.route("/qr-login", methods=["POST"])
def qr_login():
    return QrLoginController.do_qr_login()

@app.route("/qr-verification", methods=["GET"])
def qr_verification():
    return QrVerification.qr_verification()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
