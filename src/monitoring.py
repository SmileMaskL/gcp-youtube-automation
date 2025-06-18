# src/monitoring.py
import os
import sentry_sdk

def init_monitoring():
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),  # 환경변수로부터 DSN 읽기
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment="production" if os.getenv("K_SERVICE") else "github-actions"  # 환경 구분
    )

def capture_error(context: dict):
    import os
    if os.getenv("K_SERVICE"):
        sentry_sdk.set_tag("gcp_service", os.getenv("K_SERVICE"))
    else:
        sentry_sdk.set_tag("github_workflow", os.getenv("GITHUB_RUN_ID"))
    
    sentry_sdk.capture_message(f"Error in {context['module']}")
