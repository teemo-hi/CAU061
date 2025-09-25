from dataclasses import dataclass
import os
import sys
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트 기준)
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

@dataclass(frozen=True)
class Constants:
    RETRY_COUNT: int = 3
    RETRY_DELAY: int = 10
    PROCESS_ID: str = 'CAU061'
    PROCESS_NAME: str = '외부DSP 심사 숙박 / 여행상품 소재 자동 분류'

    WORK_API_KEY: str = os.getenv("WORK_API_KEY", "")

    SMTP_ID: str = os.getenv("SMTP_ID", "")
    SMTP_PW: str = os.getenv("SMTP_PW", "")

    # 실행 경로 기반 BASE_DIR 자동 추출
    script_path = os.path.abspath(sys.argv[0])
    BASE_DIR = os.path.dirname(os.path.dirname(script_path))
    DOWNLOAD_DIR: str = os.path.join(BASE_DIR, PROCESS_ID, "download")

os.makedirs(Constants.DOWNLOAD_DIR, exist_ok=True)
