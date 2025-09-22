import os, json, logging, threading, hmac, hashlib, base64
import requests
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")

def reply_text(reply_token: str, text: str):
    """เรียก LINE Reply API เพื่อส่งข้อความกลับหา user"""
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {"type": "text", "text": text}
        ]
    }
    r = requests.post(url, headers=headers, json=payload, timeout=8)
    logger.info("Reply status=%s, body=%s", r.status_code, r.text)

def process_event_async(raw_body: bytes, headers: dict):
    """งานหลักหลังจากตอบ 200 แล้ว: parse event, reply, บันทึก DB ฯลฯ"""
    try:
        data = json.loads(raw_body.decode("utf-8"))
        events = data.get("events", [])
        for ev in events:
            if ev.get("type") == "message" and ev.get("message", {}).get("type") == "text":
                user_text = ev["message"]["text"]
                reply_token = ev.get("replyToken")
                # ตัวอย่าง: echo กลับ
                if reply_token:
                    reply_text(reply_token, f"รับข้อความแล้ว: {user_text}")
                # TODO: ตรงนี้ค่อยแตกแขนงไปบันทึกออเดอร์ลงฐานข้อมูลแบบ async ต่อไป
    except Exception as e:
        logger.exception("process_event_async error: %s", e)

def verify_signature(raw_body: bytes, x_line_signature: str) -> bool:
    """ตรวจลายเซ็นตามสเปค LINE: HMAC-SHA256 + base64 ด้วย Channel Secret"""
    if not LINE_CHANNEL_SECRET:
        return True  # ช่วงทดสอบ ถ้ายังไม่ตั้ง secret ให้ผ่านไปก่อน
    mac = hmac.new(LINE_CHANNEL_SECRET.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(x_line_signature or "", expected)

@app.route("/", methods=["GET"])
def index():
    return "LINE OA Gateway is running!"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/webhook", methods=["POST"])
@app.route("/callback", methods=["POST"])  # กันพลาดเรื่อง path
def webhook():
    raw_body = request.get_data()
    logger.info("Incoming webhook: path=%s, ip=%s, headers=%s",
                request.path, request.remote_addr, dict(request.headers))
    logger.info("Body: %s", raw_body.decode("utf-8", errors="replace"))

    # ตรวจลายเซ็น (แนะนำตามแนวทาง LINE) — ทำให้เร็ว ไม่หน่วงการตอบ 200
    # ลายเซ็นถูกส่งมาที่ header ชื่อ X-Line-Signature และต้องคำนวณจาก raw body + channel secret
    # https://developers.line.biz/.../verify-webhook-signature/
    if not verify_signature(raw_body, request.headers.get("X-Line-Signature", "")):
        abort(401)

    # ตอบ 200 ก่อน เพื่อกัน timeout
    threading.Thread(target=process_event_async, args=(raw_body, dict(request.headers)), daemon=True).start()
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
