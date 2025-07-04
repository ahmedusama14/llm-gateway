import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # السماح بطلبات من تطبيق Flutter

# الحصول على عنوان ngrok من متغير بيئة
NGROK_PUBLIC_URL = os.environ.get("NGROK_PUBLIC_URL")

@app.route("/chat", methods=["POST"])
def proxy_chat():
    if not NGROK_PUBLIC_URL:
        logger.error("NGROK_PUBLIC_URL is not set")
        return jsonify({"error": "NGROK_PUBLIC_URL is not set"}), 500

    try:
        # الحصول على البيانات من طلب Flutter
        data = request.get_json()
        prompt = data.get("prompt")

        if not prompt:
            logger.warning("No prompt provided in request")
            return jsonify({"error": "Prompt is required"}), 400

        # إعادة توجيه الطلب إلى خادم FastAPI عبر ngrok
        target_url = f"{NGROK_PUBLIC_URL}/infer"
        logger.info(f"Forwarding request to: {target_url}")
        response = requests.post(
            target_url,
            json={"prompt": prompt},
            timeout=30
        )
        response.raise_for_status()  # رفع استثناء لأخطاء HTTP

        logger.info(f"Received response from FastAPI: {response.json()}")
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        logger.error(f"Error forwarding request: {str(e)}")
        return jsonify({"error": f"Failed to connect to local model: {str(e)}"}), 503
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    logger.info("Health check requested")
    return jsonify({"status": "Gateway is healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # استخدام منفذ Railway الافتراضي
    app.run(host="0.0.0.0", port=port)
