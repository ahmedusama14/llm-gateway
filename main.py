from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app) # للسماح بالوصول من تطبيق Flutter

# رابط ngrok الخاص بك كمتغير بيئي
# يجب عليك تعيين هذا المتغير في إعدادات Railway
NGROK_PUBLIC_URL = os.environ.get("https://1754-156-203-135-116.ngrok-free.app")

@app.route("/chat", methods=["POST"])
def proxy_chat():
    if not NGROK_PUBLIC_URL:
        return jsonify({"error": "NGROK_PUBLIC_URL is not set"}), 500

    try:
        # الحصول على البيانات من طلب Flutter
        data = request.get_json()
        prompt = data.get("prompt")

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        # إعادة توجيه الطلب إلى خادم FastAPI المحلي عبر ngrok
        # تأكد من أن المسار (/infer) يتطابق مع المسار في FastAPI
        target_url = f"{NGROK_PUBLIC_URL}/infer"
        
        print(f"[Gateway] Forwarding request to: {target_url}")
        response = requests.post(target_url, json={"prompt": prompt}, timeout=30)
        response.raise_for_status() # لرفع استثناء للأخطاء HTTP (4xx أو 5xx)

        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        print(f"[Gateway] Error forwarding request: {e}")
        return jsonify({"error": f"Failed to connect to local model: {str(e)}"}), 503
    except Exception as e:
        print(f"[Gateway] An unexpected error occurred: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "Gateway is healthy"}), 200

if __name__ == "__main__":
    # تأكد من أن التطبيق يستمع على 0.0.0.0 لأغراض النشر على Railway
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 5000))
