from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def index():
    return "LINE OA Gateway is running!"

# ตัวอย่าง route รับ webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    # ประมวลผล data แล้วเก็บใน DB
    return "OK", 200
