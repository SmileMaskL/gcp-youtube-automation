import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# YouTube Data API에 필요한 스코프 (권한)
# 필요한 스코프를 여기에 추가하세요.
# https://developers.google.com/youtube/v3/guides/auth/scopes
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube'
]

# 다운로드한 클라이언트 시크릿 JSON 파일의 경로
# 이 파일은 Google Cloud Console에서 '데스크톱 앱' 유형으로 다운로드한 파일입니다.
# Codespaces의 src 디렉토리에 저장했다고 가정합니다.
CLIENT_SECRETS_FILE = 'youtube_client_secrets.json' # 다운로드한 파일 이름에 맞게 변경하세요!

def get_authenticated_credentials():
    credentials = None
    # 토큰 파일이 이미 존재하면 로드합니다.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # 유효한 자격 증명이 없거나 만료된 경우 새로고침하거나 다시 인증합니다.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Access token expired, attempting to refresh...")
            try:
                credentials.refresh(Request())
                print("Access token refreshed successfully.")
            except Exception as e:
                print(f"Error refreshing token: {e}. Re-authenticating...")
                credentials = None # 새로고침 실패 시 재인증 필요
        else:
            print("No valid credentials found, initiating new authentication flow...")
            # InstalledAppFlow를 사용하여 데스크톱 앱 OAuth 흐름을 시작합니다.
            # 이 과정에서 브라우저가 열리고 인증을 요청할 것입니다.
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0) # port=0은 사용 가능한 포트를 자동으로 할당합니다.
            print("Authentication successful.")

        # 새로 얻은 자격 증명을 파일에 저장합니다.
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
            print("Credentials saved to token.pickle")
    
    return credentials

if __name__ == '__main__':
    creds = get_authenticated_credentials()
    if creds and creds.refresh_token:
        print("\n--- Successfully obtained Refresh Token ---")
        print(f"Refresh Token: {creds.refresh_token}")
        print("\n--- Please update this Refresh Token in Google Cloud Secret Manager for YOUTUBE_REFRESH_TOKEN ---")
        print(f"Also ensure YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in Secret Manager match the ones in {CLIENT_SECRETS_FILE}")
    else:
        print("\n--- Failed to obtain Refresh Token. Please check your client secrets file and try again. ---")

