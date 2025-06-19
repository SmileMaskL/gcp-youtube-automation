import os
import json
import random
from openai import OpenAI
from google.cloud import secretmanager

class OpenAIClient:
    def __init__(self):
        self.clients = []
        self.current_index = 0
        self._initialize_clients()

    def _initialize_clients(self):
        # GitHub Secrets에서 키 로드
        keys_json = os.getenv("OPENAI_KEYS_JSON")
        if keys_json:
            try:
                keys = json.loads(keys_json)
                for key in keys.values():
                    self.clients.append(OpenAI(api_key=key))
            except json.JSONDecodeError:
                pass
        
        # GCP Secret Manager에서 키 로드 (백업)
        if not self.clients:
            try:
                client = secretmanager.SecretManagerServiceClient()
                secret_name = "projects/{}/secrets/openai-api-keys/versions/latest".format(
                    os.getenv("GCP_PROJECT_ID"))
                response = client.access_secret_version(name=secret_name)
                keys = json.loads(response.payload.data.decode("UTF-8"))
                for key in keys.values():
                    self.clients.append(OpenAI(api_key=key))
            except Exception as e:
                print(f"Failed to load keys from GCP: {e}")

    def get_client(self):
        if not self.clients:
            raise ValueError("No OpenAI clients available")
        
        # Round-robin 방식으로 클라이언트 선택
        client = self.clients[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.clients)
        return client

    def generate_content(self, prompt, model="gpt-4o", max_tokens=1500):
        client = self.get_client()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
