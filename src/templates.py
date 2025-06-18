# src/templates.py
class VideoTemplates:
    SHORTS_TEMPLATE = {
        "intro_duration": 10,
        "main_duration": 40,
        "outro_duration": 10,
        "resolution": (1080, 1920),
        "fps": 30  # 양쪽 환경에서 동일한 프레임률 보장
    }
