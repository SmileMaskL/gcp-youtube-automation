import os
import logging
from flask import Flask, request, jsonify
# from dotenv import load_dotenv # Cloud Run에서는 필요 없고, 로컬 개발용

# 로깅 설정 (Cloud Run 환경에서 자동으로 통합됨)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 애플리케이션 인스턴스 생성
app = Flask(__name__)

# 환경 변수 로드 (Cloud Run 배포 시 자동 주입됨)
# 여기에 실제 사용될 환경 변수만 명시하고, 초기화에 필요한 값만 포함합니다.
# 나머지 API 키들은 실제 로직에서 필요할 때 불러오도록 합니다.
app.config['GCP_PROJECT_ID'] = os.getenv('GCP_PROJECT_ID')
app.config['GCP_BUCKET_NAME'] = os.getenv('GCP_BUCKET_NAME')
# 주의: 민감한 API 키는 app.config에 직접 넣지 말고, 필요 시 os.getenv()로 직접 호출하거나,
# Vault 또는 Secret Manager와 같은 보안 솔루션을 사용하는 것이 좋습니다.
# 여기서는 예시를 위해 단순화합니다.

# 헬스 체크 엔드포인트 (Cloud Run의 TCP 프로브가 여기로 요청을 보냄)
@app.route('/healthz', methods=['GET'])
def healthz():
    logger.info("Health check received. App is running.")
    return "OK", 200

# YouTube Shorts 업로드 엔드포인트
@app.route('/upload-youtube-shorts', methods=['POST'])
def upload_youtube_shorts_endpoint():
    logger.info("YouTube Shorts 업로드 프로세스 시작 요청 수신.")
    try:
        # 이 부분은 현재 단순한 플레이스홀더입니다.
        # 앱이 성공적으로 시작되는 것을 확인한 후,
        # 여기에 실제 유튜브 쇼츠 생성 및 업로드 로직을 단계적으로 추가할 것입니다.
        # 현재는 어떤 외부 모듈도 임포트하지 않아 잠재적인 임포트 오류를 방지합니다.

        # 실제 로직을 통합할 때는 필요한 모듈을 상단에 임포트하고 호출해야 합니다.
        # 예시:
        # from .your_shorts_generator_module import generate_and_upload_short
        # generate_and_upload_short(
        #    project_id=app.config['GCP_PROJECT_ID'],
        #    bucket_name=app.config['GCP_BUCKET_NAME'],
        #    youtube_client_id=os.getenv('YOUTUBE_CLIENT_ID'),
        #    ...
        # )

        logger.info("YouTube Shorts 업로드 프로세스 완료 (현재는 플레이스홀더).")
        return jsonify({"status": "success", "message": "YouTube Shorts process initiated (placeholder)."}), 200
    except Exception as e:
        logger.error(f"YouTube Shorts 업로드 중 오류 발생: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Cloud Run 환경에서 PORT 환경 변수가 자동으로 주입됨
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Flask app starting on port {port} (for local development or direct execution).")
    # Flask 앱을 0.0.0.0 (모든 인터페이스)에서 수신 대기
    # debug=True는 프로덕션 환경에서는 사용하지 마십시오.
    app.run(host='0.0.0.0', port=port, debug=False)
