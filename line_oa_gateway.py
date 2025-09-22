# line_oa_gateway.py
import os, json, logging
from flask import Flask, request, jsonify

app = Flask(__name__)

# ตั้งค่าล็อกให้ออก stdout (Render จะเก็บให้เอง)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

@app.route("/")
def index():
    return "LINE OA Gateway is running!"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# รับทั้ง /webhook (ตามที่คุณใช้) และ /callback (เผื่อเผลอตั้งใน LINE)
@app.route("/webhook", methods=["POST"])
@app.route("/callback", methods=["POST"])
def webhook():
    # อ่าน raw body (เพื่อดีบักและรองรับกรณีต้องตรวจลายเซ็นในอนาคต)
    raw_body = request.get_data()
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        data = {}

    # ---- LOG สำคัญ ----
    logger.info("Incoming webhook: path=%s, ip=%s, headers=%s", 
                request.path, request.remote_addr, dict(request.headers))
    logger.info("Body: %s", raw_body.decode("utf-8", errors="replace"))

    # TODO: ประมวลผล data แล้วเก็บ DB ที่นี่ (ควรทำ async เพื่อไม่ให้ช้า)
    # ตัวอย่าง: queue งานไว้ แล้วรีเทิร์น 200 ก่อน

    return "OK", 200

if __name__ == "__main__":
    # ทดสอบ local เท่านั้น; บน Render ใช้ gunicorn ตาม Procfile
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
