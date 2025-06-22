    # src/video_editor.py

    import logging
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, ImageClip
    from moviepy.video.tools.subtitles import SubtitlesClip # 자막 추가를 위한 모듈
    import os

    logger = logging.getLogger(__name__)

    def edit_video_for_shorts(video_path, content_text, video_title):
        """
        생성된 비디오에 자막, 제목 오버레이 등의 편집을 추가합니다.
        
        Args:
            video_path (str): 원본 비디오 파일 경로.
            content_text (str): 영상에 들어갈 주된 내용 (자막 생성에 사용될 수 있음).
            video_title (str): 영상 제목 (오버레이로 추가될 수 있음).
        Returns:
            str: 편집된 비디오 파일 경로 (원본 파일을 덮어쓰거나 새 파일로 저장).
        """
        try:
            logger.info(f"영상 편집 시작: {video_path}")

            clip = VideoFileClip(video_path)
            duration = clip.duration
            width, height = clip.size

            # --- 1. 제목 오버레이 추가 (중앙 상단) ---
            # TextClip을 사용하여 제목 텍스트 클립 생성
            title_text_clip = TextClip(
                txt=video_title,
                fontsize=70,
                color='white',
                font='NanumSquare', # 폰트 설정 (fonts/Catfont.ttf 등 로컬 폰트를 사용하려면 설치 필요)
                                    # Cloud Functions 환경에서는 시스템 폰트만 사용 가능하거나,
                                    # 사용자 정의 폰트를 빌드 시 이미지에 포함시켜야 합니다.
                                    # 여기서는 일반적인 시스템 폰트 사용을 가정합니다.
                stroke_color='black',
                stroke_width=2,
                method='caption', # 텍스트가 경계를 넘어가지 않도록 자동 줄바꿈
                size=(width * 0.8, None) # 가로 너비의 80%
            )
            # 제목 클립을 중앙 상단에 위치시킵니다.
            title_text_clip = title_text_clip.set_pos(('center', 'top')).set_duration(duration)

            # --- 2. 간단한 자막 추가 (내용 기반) ---
            # content_text를 기반으로 자막을 생성합니다.
            # 이 부분은 자막 싱크를 맞추는 복잡한 로직이 필요하므로, 여기서는 간단한 예시로만 보여줍니다.
            # 실제로는 음성 파형 분석 또는 AI가 생성한 시간 동기화된 자막 데이터를 사용해야 합니다.
            # 현재는 단순히 전체 영상 길이 동안 콘텐츠 텍스트를 보여주는 방식으로 구현합니다.
            content_subtitle_clip = TextClip(
                txt=content_text,
                fontsize=50,
                color='yellow',
                font='NanumSquare',
                stroke_color='black',
                stroke_width=1.5,
                method='caption',
                size=(width * 0.9, None) # 가로 너비의 90%
            ).set_pos(('center', 'bottom')).set_duration(duration)


            # 모든 클립을 합칩니다.
            final_clip_edited = CompositeVideoClip([
                clip,
                title_text_clip,
                content_subtitle_clip
            ])

            # 편집된 비디오 파일 저장 (원본 파일 덮어쓰기)
            # Cloud Functions는 /tmp에만 쓰기 가능하므로, 원본 video_path도 /tmp에 있어야 합니다.
            final_clip_edited.write_videofile(
                video_path,
                codec="libx264",
                audio_codec="aac",
                fps=clip.fps,
                temp_audiofile=f"{os.path.splitext(video_path)[0]}_edited_audio.m4a",
                remove_temp=True,
                logger=None
            )
            
            logger.info(f"영상 편집 완료: {video_path}")
            return video_path

        except Exception as e:
            logger.error(f"비디오 편집 중 오류 발생: {e}", exc_info=True)
            raise # 오류를 다시 발생시켜 main.py에서 처리하도록 합니다.
    
