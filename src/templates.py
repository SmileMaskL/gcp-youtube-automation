# src/templates.py
class VideoTemplates:
    SHORTS_TEMPLATE = {
        "intro_duration": 10,
        "main_duration": 40,
        "outro_duration": 10,
        "resolution": (1080, 1920),
        "fps": 30  # 양쪽 환경에서 동일한 프레임률 보장
    }

class EnvAwareTemplate(VideoTemplates):
    @classmethod
    def get_optimized_template(cls):
        import os
        base = cls.SHORTS_TEMPLATE.copy()
        
        if os.getenv("K_SERVICE"):  # Cloud Run 환경
            base.update({"watermark": "gcp-logo.png"})
        else:  # GitHub Actions
            base.update({"watermark": "github-logo.png"})
            
        return base
