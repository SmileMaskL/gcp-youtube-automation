    # src/video_creator.py

    import logging
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips, CompositeVideoClip, ColorClip
    import os

    logger = logging.getLogger(__name__)

    def create_short_video(background_video_path, audio_file_path, output_video_path):
        """
        배경 영상과 음성 파일을 결합하여 최종 쇼츠 비디오를 생성합니다.
        
        Args:
            background_video_path (str): 배경 비디오 파일 경로.
            audio_file_path (str): 음성 오디오 파일 경로.
            output_video_path (str): 생성될 최종 비디오 파일 경로.
        """
        try:
            logger.info("영상 제작 시작.")

            # 배경 비디오 로드
            background_clip = VideoFileClip(background_video_path)
            logger.info(f"배경 영상 로드 완료. 길이: {background_clip.duration:.2f}초")

            # 오디오 파일 로드
            audio_clip = AudioFileClip(audio_file_path)
            logger.info(f"오디오 파일 로드 완료. 길이: {audio_clip.duration:.2f}초")

            # 오디오 길이에 맞춰 비디오 클립 조정
            # 1. 배경 영상이 오디오보다 길면 오디오 길이에 맞춰 자릅니다.
            # 2. 배경 영상이 오디오보다 짧으면 배경 영상을 반복하거나 (loop=True),
            #    여기서는 단순히 오디오 길이까지만 재생되도록 합니다.
            #    쇼츠는 최대 60초이므로, 오디오가 너무 길면 잘라야 합니다.
            final_duration = min(background_clip.duration, audio_clip.duration, 60) # 최대 60초 제한

            if audio_clip.duration > background_clip.duration:
                # 배경 영상이 오디오보다 짧으면, 배경 영상을 루프시킵니다.
                background_clip = background_clip.loop(duration=audio_clip.duration)
                logger.info(f"배경 영상이 오디오 길이({audio_clip.duration:.2f}초)에 맞춰 루프됩니다.")
            
            # 최종 길이에 맞춰 클립 조정
            background_clip = background_clip.subclip(0, final_duration)
            audio_clip = audio_clip.subclip(0, final_duration)
            
            # 비디오 클립에 오디오를 설정
            final_clip = background_clip.set_audio(audio_clip)

            # 쇼츠에 적합한 해상도 (세로형)로 조정
            # 1080x1920 (9:16 비율)을 목표로 합니다.
            target_width = 1080
            target_height = 1920

            # 비율을 유지하며 리사이즈 (가장자리에 검은색 바가 생길 수 있음)
            # 또는 중앙을 기준으로 크롭할 수 있습니다. 여기서는 리사이즈 후 중앙 크롭을 고려합니다.
            if final_clip.w * target_height > final_clip.h * target_width: # 원본이 가로로 더 넓으면
                # 높이를 맞추고 폭을 크롭
                final_clip = final_clip.resize(height=target_height)
                # 중앙 크롭
                x_center = final_clip.w / 2
                y_center = final_clip.h / 2
                final_clip = final_clip.crop(
                    x_center - target_width / 2, y_center - target_height / 2,
                    x_center + target_width / 2, y_center + target_height / 2
                )
            else: # 원본이 세로로 더 길거나 비율이 비슷하면
                # 폭을 맞추고 높이를 크롭
                final_clip = final_clip.resize(width=target_width)
                # 중앙 크롭
                x_center = final_clip.w / 2
                y_center = final_clip.h / 2
                final_clip = final_clip.crop(
                    x_center - target_width / 2, y_center - target_height / 2,
                    x_center + target_width / 2, y_center + target_height / 2
                )

            # 최종 비디오 파일 쓰기
            # codec="libx264"는 일반적인 MP4 코덱입니다.
            # fps는 비디오 프레임 속도입니다.
            final_clip.write_videofile(
                output_video_path,
                codec="libx264",
                audio_codec="aac",
                fps=24, # 프레임 속도
                temp_audiofile=f"{os.path.splitext(output_video_path)[0]}_audio.m4a", # 임시 오디오 파일 경로
                remove_temp=True, # 임시 파일 삭제
                logger=None # MoviePy 내부 로거 비활성화 (우리 로거 사용)
            )
            logger.info(f"최종 비디오 생성 성공: {output_video_path}")
            return output_video_path

        except Exception as e:
            logger.error(f"비디오 생성 중 오류 발생: {e}", exc_info=True)
            raise # 오류를 다시 발생시켜 main.py에서 처리하도록 합니다.
    
