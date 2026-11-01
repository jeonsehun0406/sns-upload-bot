"""Instagram / Threads 업로드 (instagrapi — 브라우저 불필요)"""

import time
import logging
from pathlib import Path
from config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

logger = logging.getLogger(__name__)
SESSION_FILE = Path(__file__).parent / "ig_session.json"


def _client():
    try:
        from instagrapi import Client
    except ImportError:
        raise ImportError("pip install instagrapi")

    cl = Client()
    cl.delay_range = [2, 5]

    if SESSION_FILE.exists():
        try:
            cl.load_settings(str(SESSION_FILE))
            cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            logger.info("Instagram 세션 로드 성공")
        except Exception as e:
            logger.warning(f"세션 만료, 재로그인: {e}")
            SESSION_FILE.unlink(missing_ok=True)
            cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    else:
        if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
            raise ValueError("INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD 환경변수 설정 필요")
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

    cl.dump_settings(str(SESSION_FILE))
    return cl


def upload_instagram(image_paths: list, caption: str, hashtags: str) -> str:
    cl          = _client()
    full_caption = f"{caption}\n\n{hashtags}"
    paths        = [Path(p) for p in image_paths]

    if len(paths) == 1:
        media = cl.photo_upload(paths[0], full_caption)
    else:
        media = cl.album_upload(paths, full_caption)

    url = f"https://www.instagram.com/p/{media.code}/"
    logger.info(f"Instagram 완료: {url}")
    return url


def upload_threads(image_paths: list, caption: str, hashtags: str) -> str:
    cl        = _client()
    full_text = f"{caption}\n\n{hashtags}"
    try:
        result = cl.threads_publish(
            thread_type="IMAGE",
            caption=full_text,
            image_path=Path(image_paths[0]),
        )
    except AttributeError:
        result = cl.threads_publish(thread_type="TEXT", caption=full_text)

    url = str(result)
    logger.info(f"Threads 완료: {url}")
    return url


def upload_all(image_paths: list, caption: str, hashtags: str,
               platforms: list = None) -> dict:
    if platforms is None:
        platforms = ["instagram", "threads"]

    results = {}

    if "instagram" in platforms:
        try:
            results["instagram"] = upload_instagram(image_paths, caption, hashtags)
        except Exception as e:
            logger.error(f"Instagram 실패: {e}")
            results["instagram"] = f"ERROR: {e}"
        time.sleep(3)

    if "threads" in platforms:
        try:
            results["threads"] = upload_threads(image_paths, caption, hashtags)
        except Exception as e:
            logger.error(f"Threads 실패: {e}")
            results["threads"] = f"ERROR: {e}"

    return results
