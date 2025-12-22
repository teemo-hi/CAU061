# carib_utils.py (통합 버전 발췌)
import os
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from knw_Chromedriver_manager import Chromedriver_manager

from Common.log import Log
from Service.constants import Constants


class CaribUtils:
    """
    CARIB(카카오 보안 검수) 사이트 로그인/다운로드 유틸 클래스.

    - Selenium WebDriver를 이용해 로그인 절차를 수행한다.
    - 실패 시 재시도를 지원하며, 지정된 횟수 이상 실패하면 예외를 발생시킨다.
    - logger와 constants 객체를 외부에서 주입할 수 있어 테스트 및 확장에 용이하다.
    - Chrome 다운로드 디렉토리를 옵션으로 설정해 CSV 등 파일 저장을 자동화한다.

    Attributes:
        carib_url (str): 로그인 대상 URL
        carib_id (str): 로그인 계정 ID
        carib_pw (str): 로그인 계정 비밀번호
        download_dir (str | None): Chrome 기본 다운로드 디렉토리
        logging (Log): 로그 기록 객체 (기본값: Common.log.Log)
        constants (Constants): 환경 상수 객체 (기본값: Service.constants.Constants)
        driver (webdriver.Chrome | None): Chrome WebDriver 인스턴스
    """

    DEFAULT_WAIT = 120

    def __init__(self, carib_url, carib_id, carib_pw, logger=None, constants=None, download_dir=None):
        """
        CaribUtils 인스턴스를 초기화한다.

        Args:
            carib_url (str): 로그인 대상 URL
            carib_id (str): 로그인 계정 ID
            carib_pw (str): 로그인 계정 비밀번호
            logger (Log, optional): 로깅 객체 (기본값: Log())
            constants (Constants, optional): 상수 객체 (기본값: Constants())
            download_dir (str | None, optional): Chrome의 기본 다운로드 경로. 지정 시 해당 폴더로 자동 저장.
        """
        self.carib_url = carib_url
        self.carib_id = carib_id
        self.carib_pw = carib_pw
        self.download_dir = download_dir
        self.logging = logger or Log()
        self.constants = constants or Constants()
        self.driver = None

    def _init_driver(self):
        """
        Chrome WebDriver를 초기화한다.
        - download_dir이 지정된 경우 Chrome prefs에 기본 다운로드 경로를 설정한다.

        Returns:
            webdriver.Chrome: 초기화된 Chrome 드라이버
        """
        options = Options()
        # options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument('--blink-settings=imagesEnabled=false')

        # 다운로드 폴더 설정 (선택)
        if self.download_dir:
            os.makedirs(self.download_dir, exist_ok=True)
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            }
            options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(
            service=Service(Chromedriver_manager.install()), options=options
        )
        return self.driver

    def login(self):
        """
        CARIB 사이트에 로그인 절차를 수행한다.

        Returns:
            webdriver.Chrome: 로그인 성공 후의 WebDriver 인스턴스

        Raises:
            TimeoutException: 최대 재시도 횟수 내에 로그인에 실패한 경우
            WebDriverException: 드라이버/브라우저 구동 관련 오류가 발생한 경우
            Exception: 그 외 예기치 못한 오류
        """
        self.logging.log("▷ [CARIB] 로그인 → 시작", level="INFO")
        self._init_driver()

        max_retries = self.constants.RETRY_COUNT
        wait_secs = getattr(self.constants, "RETRY_DELAY", 5)

        for attempt in range(1, max_retries + 1):
            try:
                self.driver.get(self.carib_url)
                self.driver.maximize_window()
                time.sleep(3)

                self.driver.find_element(By.CSS_SELECTOR, "#id").send_keys(self.carib_id)
                self.driver.find_element(By.CSS_SELECTOR, "#password").send_keys(self.carib_pw)
                self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

                WebDriverWait(self.driver, self.DEFAULT_WAIT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#mainContent")))

                self.logging.log("▷ [CARIB] 로그인 → 완료", level="INFO")
                return self.driver

            except (TimeoutException, WebDriverException) as e:
                if attempt == max_retries:
                    self.logging.log(f"▷ [CARIB] 로그인 → 실패 : 최대 재시도 초과\n{traceback.format_exc()}", level="ERROR")
                    self.driver.quit()
                    raise TimeoutException(f"> 사이트 접속 실패 (URL : {self.carib_url})") from e

                self.logging.log(
                    f"> 로그인 실패 : {type(e).__name__} / 재시도 중 - {attempt}/{max_retries}",
                    level="WARNING",
                )
                time.sleep(wait_secs)

            except Exception:
                self.logging.log(f"> 예상치 못한 오류 : {traceback.format_exc()}", level="ERROR")
                self.driver.quit()
                raise

    def logout(self):
        """
        CARIB 사이트에 로그아웃 절차를 수행한다.

        Returns:
            None

        Raises:
            TimeoutException: 최대 재시도 횟수 내에 로그인에 실패한 경우
            WebDriverException: 드라이버/브라우저 구동 관련 오류가 발생한 경우
            Exception: 그 외 예기치 못한 오류
        """
        if self.driver:
            self.logging.log("▷ [CARIB] 로그아웃 → 시작", level="INFO")

            max_retries = self.constants.RETRY_COUNT
            wait_secs = getattr(self.constants, "RETRY_DELAY", 5)

            for attempt in range(1, max_retries + 1):
                try:
                    self.driver.find_element(By.CSS_SELECTOR,    # 로그아웃 버튼
                                             '#ka-review > div > div > header > span:nth-child(2) > span').click()
                    time.sleep(3)

                    WebDriverWait(self.driver, self.DEFAULT_WAIT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span > input#id")))

                    self.logging.log("▷ [CARIB] 로그아웃 → 완료", level="INFO")
                    break
                except (TimeoutException, WebDriverException) as e:
                    if attempt == max_retries:
                        self.logging.log(f"▷ [CARIB] 로그아웃 → 실패 : 최대 재시도 초과\n{traceback.format_exc()}", level="ERROR")
                        self.driver.quit()
                        raise TimeoutException(f"> 정상 로그아웃 실패 (URL : {self.carib_url})") from e

                    self.logging.log(
                        f"> 로그아웃 실패 : {type(e).__name__} / 재시도 중 - {attempt}/{max_retries}",
                        level="WARNING",)
                    time.sleep(wait_secs)

                except Exception:
                    self.logging.log(f"> 예상치 못한 오류 : {traceback.format_exc()}", level="ERROR")
                    self.driver.quit()
                    raise

    def download_csv(self, button_selector, timeout=30):
        """
        CSV 다운로드 버튼을 클릭하여 파일을 저장한다.
        - 생성된 새 파일들 중 .csv 확장자를 탐지하여 경로를 반환한다.
        - download_dir이 설정되어 있어야 동작한다.

        Args:
            button_selector (str): CSV 다운로드 버튼의 CSS Selector
            timeout (int, optional): 다운로드 완료 대기 시간(초). 기본값 30.

        Returns:
            str: 다운로드된 CSV 파일의 절대 경로

        Raises:
            TimeoutException: 제한 시간 내 CSV 파일 생성이 확인되지 않은 경우
            ValueError: download_dir가 미설정인 경우
        """
        self.logging.log("▷ [CARIB] CSV 다운로드 → 시작", level="INFO")

        if not self.download_dir:
            raise ValueError("> download_dir가 설정되지 않았습니다.")

        before_files = set(os.listdir(self.download_dir))

        # 버튼 클릭
        btn = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))
        btn.click()

        # 다운로드 완료 대기
        end_time = time.time() + timeout
        while time.time() < end_time:
            after_files = set(os.listdir(self.download_dir))
            new_files = after_files - before_files
            for f in new_files:
                if f.lower().endswith(".csv"):
                    csv_path = os.path.join(self.download_dir, f)
                    self.logging.log(f"▷ [CARIB] CSV 다운로드 → 완료 : {csv_path}", level="INFO")
                    return csv_path
            time.sleep(1)

        raise TimeoutException("> CSV 파일 다운로드가 제한 시간 내에 완료되지 않았습니다.")

    def quit(self):
        """
        현재 WebDriver 인스턴스를 종료한다.
        """
        if self.driver:
            self.driver.quit()
            self.logging.log("▷ [CARIB] 드라이버 종료", level="INFO")
