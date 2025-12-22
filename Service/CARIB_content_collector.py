from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, JavascriptException)

import time

from Common.log import Log
from Service.constants import Constants

# 상수 모음 ============================================================================================================ #
DEFAULT_WAIT = 120
AD_ACCOUNT_IDS = [
    "*interpark.tour*",
    "*yanolja*"
]

# 클래스 초기화 ======================================================================================================== #
logging = Log()
constants = Constants()

# ==================================================================================================================== #
def _setup_page_option(driver):
    """
    페이지네이션 옵션을 '1000 / 페이지'로 설정하고 테이블 로우가 표시될 때까지 대기한다.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver 인스턴스

    Returns:
        None

    Raises:
        TimeoutException: 모든 재시도에도 옵션 설정이 완료되지 않은 경우
        WebDriverException: 드라이버 실행 중 오류가 발생한 경우
        JavascriptException: JS 실행 중 오류가 발생한 경우
    """
    logging.log("▷ 페이지 옵션 설정 → 시작", level="INFO")

    max_retries = constants.RETRY_COUNT
    wait_secs = getattr(constants, "RETRY_DELAY", 5)

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            time.sleep(5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")     # 스크롤 맨 아래로
            time.sleep(10)

            driver.find_element(By.CSS_SELECTOR,     # 페이지 콤보 박스
                                'ul > li > div > div.ant-select-selector').click()
            time.sleep(3)
            driver.find_element(By.CSS_SELECTOR,     # 1000 / 페이지
                                'div[role="option"][id="rc_select_2_list_3"][title="1000 / 페이지"]').click()

            WebDriverWait(driver, DEFAULT_WAIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table > tbody")))

            logging.log("▷ 페이지 옵션 설정 → 완료", level="INFO")
            return  # 성공 시 종료

        except (TimeoutException, WebDriverException, JavascriptException) as e:
            last_err = e
            logging.log(f"> 페이지 옵션 설정 실패 ({type(e).__name__}) / 재시도 {attempt}/{max_retries}", level="WARNING")

            time.sleep(wait_secs)

    logging.log("> 페이지 옵션 설정 실패 : 최대 재시도 초과", level="ERROR")
    raise TimeoutException("> 페이지 옵션 설정 실패(1000 / 쪽). 마지막 오류: " + (str(last_err) if last_err else "unknown"))

def process_content_collection(driver, test_mode=False):
    """
    광고계정별 심사 데이터 수집을 수행한다.

    - 각 광고계정 ID를 검색 입력창에 넣고 조회 버튼을 클릭한다.
    - 결과가 없으면 스킵한다.
    - 결과 테이블이 로드되면 체크박스를 선택한다.
    - test_mode=False 인 경우에만 '내가 처리하기' 버튼을 클릭한다.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver 인스턴스
        test_mode (bool, optional): True일 경우 '내가 처리하기' 버튼 클릭을 생략. 기본값 False.

    Returns:
        None

    Raises:
        TimeoutException: 조회 또는 테이블 로딩이 시간 초과된 경우
        WebDriverException: 드라이버 실행 중 오류가 발생한 경우
        JavascriptException: JS 실행 중 오류가 발생한 경우
    """
    logging.log("▷ [CARIB] 여행/숙박 소재 자동 수집 → 시작", level="INFO")
    _setup_page_option(driver)
    time.sleep(5)

    for ad_account_id in AD_ACCOUNT_IDS:
        try:
            logging.log(f"> 검색 광고계정 ID : {ad_account_id}", level="INFO")
            input_box = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="검색할 내용을 입력하세요."]')
            input_box.send_keys(Keys.CONTROL, 'a')
            input_box.send_keys(Keys.DELETE)
            input_box.send_keys(ad_account_id)
            time.sleep(1)
            driver.find_element(By.CSS_SELECTOR, '#complex-form > button[type="submit"]').click()    # 조회 버튼
            time.sleep(5)

            if driver.execute_script('return document.querySelector("div.ant-empty-description")'):
                logging.log("> 데이터가 없습니다.", level="INFO")
                continue

            WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table > tbody > tr")))
            time.sleep(5)
            driver.find_element(By.CSS_SELECTOR,     # 체크박스
                                'table > thead > tr > th > div > label > span > input[type="checkbox"]').click()

            # 테스트 모드면 '내가 처리하기' 클릭 건너뜀
            if test_mode:
                logging.log("> (테스트 모드) '내가 처리하기' 클릭 생략", level="INFO")
            else:
                driver.find_element(By.CSS_SELECTOR,     # 내가 처리하기 버튼
                                    '#mainContent > div > div > div > div > div > div > div > button:nth-child(11)').click()
                time.sleep(5)
        except (TimeoutException, WebDriverException, JavascriptException) as e:
            logging.log(f"> 계정 처리 실패({ad_account_id}) : {type(e).__name__}", level="WARNING")
            continue

    logging.log("▷ [CARIB] 여행/숙박 소재 자동 수집 → 완료", level="INFO")
