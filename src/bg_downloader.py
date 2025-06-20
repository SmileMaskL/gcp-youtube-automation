import logging
from pexels_api import API
from src.config import get_secret

logger = logging.getLogger(__name__)

def download_pexels_videos(api_key: str, query: str, max_videos: int = 1):
    """
    Pexels API에서 동영상 URL을 가져옵니다 (수정된 버전).
    
    Args:
        api_key: Pexels API 키
        query: 검색 쿼리
        max_videos: 최대 동영상 수
        
    Returns:
        str: 동영상 URL 또는 None
    """
    try:
        pexel = API(api_key)
        search_results = pexel.search_video(
            query=query,
            page=1,
            results_per_page=max_videos
        )
        
        if not search_results.get('videos'):
            logger.warning(f"No videos found for query: {query}")
            return None
            
        best_video = max(
            search_results['videos'],
            key=lambda x: x['width'] * x['height']
        )
        video_url = best_video['video_files'][0]['link']
        logger.info(f"Found Pexels video: {video_url}")
        return video_url
        
    except Exception as e:
        logger.error(f"Pexels API error: {e}")
        return None
