# get_youtube_token.py
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# YouTube API 스코프
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube"
]

def get_initial_credentials():
    # GCP에서 다운로드한 '데스크톱 앱' 유형의 OAuth 클라이언트 JSON 파일 경로
    # 이 파일을 get_youtube_token.py와 같은 위치에 두거나 경로를 정확히 지정하세요.
    client_secrets_file_path = 'youtube_client_secrets.json' # 다운로드한 파일 이름을 정확히 입력

    if not os.path.exists(client_secrets_file_path):
        print(f"Error: {client_secrets_file_path} not found.")
        print("Please download your OAuth 2.0 Client ID JSON file from GCP 'API 및 서비스 > 사용자 인증 정보'")
        print("그리고 파일명을 'youtube_client_secrets.json'으로 변경하여 이 스크립트와 같은 폴더에 저장해주세요.")
        return

    # --- 다음 줄이 수정되었습니다 ---
    # client_secrets.json 파일에 "redirect_uris": ["http://localhost"]가 있으므로 이를 사용합니다.
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file_path, SCOPES, redirect_uri='http://localhost'
    )
    # --- 수정 끝 ---

    # 브라우저를 열고 인증 URL을 표시
    auth_url, _ = flow.authorization_url(prompt='consent')
    print(f'Please go to this URL and authorize your YouTube account: {auth_url}')

    # 사용자로부터 인증 코드 입력 받기 (이 부분은 localhost 리디렉션을 사용하므로 필요 없습니다)
    # 대신, flow.run_local_server()를 사용하여 자동으로 처리합니다.
    # Codespaces 환경에서는 여전히 문제가 될 수 있으므로,
    # 아래의 '대안: 수동 OOB 흐름 유지' 섹션을 참고하세요.
    
    # 임시로 로컬 서버를 실행하여 인증 코드를 자동으로 처리합니다.
    # Codespaces 환경에서는 이 부분이 여전히 ERR_CONNECTION_REFUSED를 발생시킬 수 있습니다.
    # 이 문제가 발생하면 아래 '대안: 수동 OOB 흐름 유지' 섹션을 따르세요.
    print("Waiting for authentication in your browser...")
    flow.run_local_server(port=0) # 사용 가능한 포트를 자동으로 할당하고 브라우저 리디렉션을 처리

    creds = flow.credentials

    print("\n--- Your YouTube OAuth Credentials (for Secret Manager) ---")
    # refresh_token을 포함한 JSON 문자열 출력
    creds_json_string = creds.to_json()
    print(creds_json_string) 

    # 이 JSON 문자열을 복사하여 Google Cloud Secret Manager의 YOUTUBE_OAUTH_CREDENTIALS에 붙여넣으세요.
    # 이 파일은 일회성으로 사용되므로, 굳이 로컬에 token.json을 저장할 필요는 없습니다.

if __name__ == '__main__':
    get_initial_credentials()
