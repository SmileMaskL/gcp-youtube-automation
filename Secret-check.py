from dotenv import load_dotenv
import os
load_dotenv()
print(os.environ)  # DEBUG
print(os.getenv("ELEVENLABS_API_KEY"))  # None이면 에러
