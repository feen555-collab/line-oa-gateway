from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Line OA Gateway is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    # ตัวอย่าง log ข้อมูล event ที่ได้จาก LINE
    print("Webhook received:", data)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
