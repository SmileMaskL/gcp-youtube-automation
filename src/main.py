    # src/main.py

    import functions_framework
    import os
    import logging
    from google.cloud import storage
    from datetime import datetime
    import json
    import random

    # ❗❗❗ 중요: 아래 모듈들은 당신이 직접 구현하거나 기존 코드를 여기에 맞춰야 합니다. ❗❗❗
    # 이 코드들은 당신의 실제 로직을 대신하는 "예시" 및 "연동점"입니다.
    from config import Config # 설정 정보 로드
    from youtube_uploader import upload_video # YouTube 업로드 함수
    from ai_manager import generate_content_with_gemini, generate_content_with_openai, generate_niche_content # AI 콘텐츠 생성
    from tts_generator import generate_tts_audio # TTS 음성 생성
    from video_creator import create_short_video # 영상 생성
    from video_editor import edit_video_for_shorts # 영상 편집
    from bg_downloader import download_background_video # 배경 영상 다운로드

    # 로깅 설정: Cloud Function 로그에 메시지가 잘 보이도록 합니다.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    @functions_framework.http
    def trigger_youtube_upload(request):
        logger.info("--- Cloud Function 'trigger_youtube_upload' 시작 ---")

        # 1. 환경 변수 및 시크릿 설정 로드
        try:
            project_id = os.environ.get("GCP_PROJECT_ID")
            bucket_name = os.environ.get("GCP_BUCKET_NAME")

            # Config 클래스를 초기화하여 Secret Manager에서 모든 필요한 키를 안전하게 로드합니다.
            config = Config(project_id=project_id, bucket_name=bucket_name)

            # 필요한 API 키들을 로드합니다.
            # OpenAI 키는 로테이션을 위해 openai_utils에서 관리됩니다.
            gemini_api_key = config.get_gemini_api_key()
            elevenlabs_api_key = config.get_elevenlabs_api_key()
            elevenlabs_voice_id = config.elevenlabs_voice_id
            pexels_api_key = config.get_pexels_api_key()
            
            logger.info("API 키 및 설정 로드 완료.")

        except Exception as e:
            logger.error(f"설정 또는 시크릿 로드 실패: {e}", exc_info=True)
            return f"설정 오류: {str(e)}", 500

        # 임시 파일 저장 경로 (Cloud Function은 /tmp 디렉토리에만 쓰기 가능)
        temp_dir = "/tmp"
        os.makedirs(temp_dir, exist_ok=True) # /tmp 디렉토리가 없으면 생성

        # 2. 콘텐츠 생성 (GPT-4o 또는 Gemini 선택적으로 사용)
        # ❗❗❗ 수익화를 위한 핵심 로직 ❗❗❗
        # 여기에 '수익성 높은 주제'를 선정하는 전략을 구현하세요.
        # 예: 인기 뉴스 API 연동(newsapi-python 사용), 트렌딩 키워드 분석, 특정 틈새 시장 (Niche) 콘텐츠 생성 등
        
        # 실전 수익화를 위한 아이디어: 특정 틈새시장에 집중 (예: '환경', '건강', '역사적 사실', 'IT 팁')
        niche_keywords = ["신기한 과학 사실", "역사 속 숨겨진 이야기", "최신 기술 트렌드", "일상 속 꿀팁", "건강 상식"]
        selected_niche = random.choice(niche_keywords)
        
        # AI 모델 선택: 랜덤 또는 특정 모델 우선
        ai_model_preference = random.choice(["gemini", "openai"])
        
        content_topic = ""
        suggested_title = ""

        try:
            logger.info(f"선택된 틈새 키워드: '{selected_niche}', AI 모델 선호: '{ai_model_preference}'")
            
            # generate_niche_content 함수를 사용하여 콘텐츠 생성
            # 이 함수는 내부적으로 OpenAI 키 로테이션을 사용합니다.
            ai_response = generate_niche_content(config, selected_niche, ai_model_preference)
            
            if isinstance(ai_response, dict) and "content" in ai_response and "title" in ai_response:
                content_topic = ai_response.get("content", "생성된 콘텐츠가 없습니다.")
                suggested_title = ai_response.get("title", "흥미로운 쇼츠")
                # 내용이 너무 길면 자르기 (쇼츠 음성 길이에 맞춰야 함)
                if len(content_topic) > 200: 
                    content_topic = content_topic[:200] + "..."
            else:
                logger.warning(f"AI 응답 형식이 예상과 다릅니다: {ai_response}. 기본 콘텐츠 사용.")
                content_topic = "자동 생성된 유튜브 쇼츠 영상입니다. 콘텐츠 생성에 문제가 있었습니다."
                suggested_title = "자동 생성 오류 쇼츠"
            
            logger.info(f"콘텐츠 생성 완료. 제목: '{suggested_title}', 내용: '{content_topic[:50]}...'")

        except Exception as e:
            logger.error(f"AI 콘텐츠 생성 실패: {e}", exc_info=True)
            # AI 콘텐츠 생성 실패 시에도 파이프라인이 멈추지 않도록 기본 콘텐츠 사용
            content_topic = "자동 생성된 유튜브 쇼츠 영상입니다. 콘텐츠 생성 중 오류가 발생했습니다."
            suggested_title = "AI 생성 실패 쇼츠"
            # return f"AI 콘텐츠 생성 오류: {str(e)}", 500 # 오류 시 즉시 종료하려면 주석 해제

        # 3. 음성 생성 (TTS)
        audio_file_path = os.path.join(temp_dir, "generated_audio.mp3")
        try:
            # generate_tts_audio 함수를 호출하여 텍스트를 음성으로 변환합니다.
            generate_tts_audio(elevenlabs_api_key, content_topic, elevenlabs_voice_id, audio_file_path)
            logger.info(f"음성 파일 생성 완료: {audio_file_path}")
        except Exception as e:
            logger.error(f"TTS 음성 생성 실패: {e}", exc_info=True)
            return f"TTS 오류: {str(e)}", 500

        # 4. 배경 영상 다운로드 (Pexels API 등 사용)
        background_video_path = os.path.join(temp_dir, "background_video.mp4")
        # Pexels 검색 쿼리를 AI가 생성한 내용과 연관되게 할 수 있습니다.
        pexels_query = selected_niche.split(' ')[0] if selected_niche else "abstract" # 키워드의 첫 단어 사용
        try:
            download_background_video(pexels_api_key, pexels_query, background_video_path)
            logger.info(f"배경 영상 다운로드 완료: {background_video_path}")
        except Exception as e:
            logger.error(f"배경 영상 다운로드 실패: {e}", exc_info=True)
            # 배경 영상 다운로드 실패 시 더미 영상 사용 또는 에러 처리
            return f"배경 영상 다운로드 오류: {str(e)}", 500


        # 5. 최종 영상 제작 및 편집
        # output 디렉토리는 GitHub Actions에서 아티팩트 업로드에 사용될 것입니다.
        output_dir = "output" # GitHub Actions의 루트 디렉토리에 'output' 폴더 생성 가정
        os.makedirs(output_dir, exist_ok=True) # 폴더 없으면 생성
        final_video_filename = f"youtube_short_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        final_video_file_path = os.path.join(output_dir, final_video_filename)

        try:
            # create_short_video 함수 호출: 배경 영상과 음성을 합쳐 기본 영상을 만듭니다.
            created_video_path = create_short_video(background_video_path, audio_file_path, os.path.join(temp_dir, "temp_created_video.mp4"))
            logger.info(f"기본 영상 생성 완료: {created_video_path}")

            # edit_video_for_shorts 함수 호출: 쇼츠 형식에 맞게 편집 (자막 추가, 제목 오버레이 등)
            # 최종 결과는 final_video_file_path에 저장됩니다.
            edit_video_for_shorts(created_video_path, content_topic, video_title)
            # 편집된 최종 비디오를 output_dir로 이동 또는 복사
            os.rename(created_video_path, final_video_file_path) # temp_created_video.mp4를 최종 경로로 이동
            logger.info(f"최종 쇼츠 영상 편집 완료 및 저장: {final_video_file_path}")

        except Exception as e:
            logger.error(f"영상 제작 또는 편집 실패: {e}", exc_info=True)
            return f"영상 제작 오류: {str(e)}", 500

        # 6. YouTube 업로드
        video_title_for_upload = suggested_title # AI가 추천한 제목 사용
        video_description = (
            f"AI가 자동으로 생성하고 업로드한 유튜브 쇼츠입니다.\n\n"
            f"주제: {selected_niche}\n"
            f"콘텐츠: {content_topic}\n\n"
            f"#AI #유튜브쇼츠 #자동생성 #shorts #viral #{selected_niche.replace(' ', '')}"
        )
        # 태그는 콤마로 구분된 문자열을 리스트로 변환
        video_tags = [tag.strip() for tag in f"shorts,AI,자동화,유튜브,꿀팁,수익화,정보,{selected_niche},{suggested_title.replace(' ', '')}".split(',') if tag.strip()]
        video_category_id = "22" # People & Blogs (YouTube Data API 문서 참고)
        video_privacy_status = "public" # 'public'으로 설정하여 수익화 가능성 높임

        try:
            # upload_video 함수를 호출하여 최종 영상을 YouTube에 업로드합니다.
            response = upload_video(
                final_video_file_path,
                video_title_for_upload,
                video_description,
                video_tags,
                video_category_id,
                video_privacy_status,
                config_instance=config # config 인스턴스 전달
            )
            logger.info(f"영상 업로드 성공! YouTube ID: {response.get('id')}")

            # 업로드 완료 후 임시 파일 삭제 (매우 중요!)
            # /tmp 디렉토리의 파일들을 삭제합니다.
            for f in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"임시 파일 삭제: {file_path}")
            
            logger.info("--- Cloud Function 'trigger_youtube_upload' 완료 ---")
            return f"Video upload successful! ID: {response.get('id')}", 200

        except Exception as e:
            logger.error(f"최종 YouTube 업로드 실패: {e}", exc_info=True)
            return f"YouTube 업로드 오류: {str(e)}", 500
    
