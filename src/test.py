import os
from flask import Flask, request, jsonify
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel

app = Flask(__name__)

# Cloud Run 환경에서 PORT 환경 변수 가져오기, 기본값은 8080
PORT = int(os.environ.get("PORT", 8080))

# Vertex AI 초기화 (Cloud Run 서비스 계정 권한으로 자동 인증)
# 프로젝트 ID와 리전은 현재 사용 중인 것에 맞춰 정확히 기입
# us-central1은 Gemini 1.5 Flash가 지원되는 리전 중 하나입니다.
init(project="youtube-fully-automated", location="us-central1")
model = GenerativeModel("gemini-1.5-flash")

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Cloud Run은 HTTP 요청을 처리해야 하므로,
    기본 경로("/")에 대한 응답을 정의합니다.
    """
    if request.method == "POST":
        # POST 요청 본문에서 메시지를 가져와 AI 모델에 전달
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "No 'message' provided in request body."}), 400
        user_message = data["message"]
        prompt = f"Say hello to the world in Korean: {user_message}" # 사용자 메시지를 포함하도록 프롬프트 수정
    else:
        # GET 요청 시 기본 메시지
        prompt = "Say hello to the world in Korean"

    try:
        response = model.generate_content(prompt)
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Gunicorn을 사용하므로, 이 부분은 Dockerfile의 CMD에서 실행되지 않습니다.
    # 로컬 테스트용으로만 유효합니다.
    app.run(debug=True, host="0.0.0.0", port=8080)
