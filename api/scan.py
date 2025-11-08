import os
import requests
from flask import Flask, request, jsonify
from clerk_sdk import Clerk

# --- NAYA: Clerk Backend Setup ---
# Ye key aapko Clerk Dashboard -> API Keys -> "Secret Key" mein milegi
# Ye 'sk_test_...' se shuru hoti hai.
CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY")
clerk_client = Clerk(secret_key=CLERK_SECRET_KEY)
# --- END NAYA SETUP ---

HF_TOKEN = os.environ.get("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/ludovick/Deepfake-Audio-Detection"

app = Flask(__name__)

@app.route('/api/scan', methods=['POST'])
def scan_audio():
    # --- NAYA: Authentication Check ---
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing authorization"}), 401
    
    try:
        token = auth_header.split(' ')[1]
        # Clerk se verify karo ki token asli hai
        session = clerk_client.sessions.verify_token(token=token)
        if not session:
            raise Exception("Invalid session")
    except Exception as e:
        return jsonify({"error": f"Unauthorized: {str(e)}"}), 401
    # --- END NAYA CHECK ---

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file found"}), 400

    file = request.files['audio']
    audio_data = file.read()

    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(API_URL, headers=headers, data=audio_data)
        
        if response.status_code == 503:
             return jsonify({"error": "AI Model is loading, please try again in ~20 seconds."}), 503

        response_data = response.json()

        if isinstance(response_data, dict) and 'error' in response_data:
            return jsonify({"error": response_data['error']}), 500

        real_score = 0.0
        fake_score = 0.0
        
        for item in response_data:
            if item['label'] == 'real':
                real_score = item['score']
            elif item['label'] == 'fake':
                fake_score = item['score']
                
        return jsonify({
            "real_score": real_score,
            "fake_score": fake_score
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500