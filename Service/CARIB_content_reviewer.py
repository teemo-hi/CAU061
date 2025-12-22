from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, JavascriptException)
import pandas as pd

import time

from Common.log import Log
from Service.constants import Constants

# 상수 모음 ============================================================================================================ #
DEFAULT_WAIT = 320
HOLD_REASON = '[공통] 제한업종_모텔 업종'  # 보류 사유

# 클래스 초기화 ======================================================================================================== #
logging = Log()
constants = Constants()

# ==================================================================================================================== #
def _setup_reviewer_option(driver, mode, carib_id=None):
    """
    심사자/검색대상 콤보박스를 모드에 맞게 설정하고 조회를 수행한다.

    - mode="reviewer":
        상단 콤보박스를 클릭하고 심사자 입력창(#complex-form_reviewerId)에
        전달받은 carib_id 계정을 'id(id)' 형식으로 입력 후 Enter로 확정한다.
    - mode="target":
        '.ant-select-selector'를 클릭하여 드롭다운을 연 뒤,
        드롭다운 패널(body 하단에 렌더링됨)에서 '심사대상ID' 항목을 직접 클릭해 선택한다.

    - 이후 공통으로 조회 버튼(#complex-form > button[type="submit"])을 클릭하고,
      결과 테이블의 첫 행이 나타날 때까지 대기한다.
    - 설정 과정은 상수(RETRY_COUNT, RETRY_DELAY)에 따라 재시도한다.
      모든 재시도에도 실패하면 TimeoutException을 발생시킨다.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver 인스턴스
        mode (str): 설정 모드. "reviewer" 또는 "target"을 지원
        carib_id (str, optional): mode="reviewer"일 때 사용할 CARIB 로그인 계정

    Returns:
        None

    Raises:
        TimeoutException: 모든 재시도에도 옵션 설정이 완료되지 않은 경우
        WebDriverException: 드라이버 실행 중 오류가 발생한 경우
        JavascriptException: JS 실행 중 오류가 발생한 경우
    """
    logging.log("▷ 심사자/검색대상 옵션 설정 → 시작", level="INFO")

    max_retries = constants.RETRY_COUNT
    wait_secs = getattr(constants, "RETRY_DELAY", 5)

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            time.sleep(5)

            if mode == 'reviewer':
                driver.find_element(By.CSS_SELECTOR, 'span[title="전체"][class="ant-select-selection-item"]').click()
                driver.find_element(By.CSS_SELECTOR, 'input[type="search"][id="complex-form_reviewerId"]').send_keys(f'{carib_id}({carib_id})', Keys.ENTER)
            elif mode == 'target':
                # 1) 셀렉트 열기
                driver.find_element(By.CSS_SELECTOR, '.ant-select-selector').click()
                time.sleep(1)

                # 2) 드롭다운이 body 하단에 렌더됨 → 드롭다운 등장 대기
                WebDriverWait(driver, DEFAULT_WAIT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.ant-select-dropdown:not([aria-hidden="true"])')))

                # 3) 옵션 클릭 (title 또는 텍스트 매칭)
                driver.find_element(
                    By.XPATH,
                    '//div[contains(@class,"ant-select-dropdown") and not(@aria-hidden="true")]'
                    '//*[(@title="심사대상ID") or normalize-space(text())="심사대상ID"]'
                ).click()

            time.sleep(5)
            driver.find_element(By.CSS_SELECTOR, '#complex-form > button[type="submit"]').click()  # 조회 버튼

            WebDriverWait(driver, DEFAULT_WAIT).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                      "#mainContent > div > div.ant-card.ant-card-bordered > div > "
                      "div > div > div > div > div > div > div > table > tbody > tr")))

            logging.log("▷ 심사자/검색대상 옵션 설정 → 완료", level="INFO")
            return  # 성공 시 종료
        except (TimeoutException, WebDriverException, JavascriptException) as e:
            last_err = e
            logging.log(f"> 심사자/검색대상 옵션 설정 실패 ({type(e).__name__}) / 재시도 {attempt}/{max_retries}", level="WARNING")

            time.sleep(wait_secs)

    logging.log("> 심사자/검색대상 옵션 설정 실패 : 최대 재시도 초과", level="ERROR")
    raise TimeoutException("> 심사자/검색대상 옵션 설정 실패. 마지막 오류 : " + (str(last_err) if last_err else "unknown"))

def process_content_review(driver, carib_utils, carib_id):
    """
    CARIB 소재 자동 심사를 수행한다.

    - 심사자 옵션을 설정한다. (_setup_reviewer_option 호출)
    - CSV 다운로드 버튼을 클릭하여 소재 심사 데이터를 다운로드한다.
    - CSV 파일을 DataFrame으로 읽고 '랜딩URL', '심사대상ID' 컬럼만 추출한다.
    - 랜딩URL에 'hotel|tour'이 포함된 행을 제거한다.
    - '구분' 컬럼을 추가하여 초기값을 None으로 설정한다.
    - 각 랜딩URL에 대해 새 탭을 열고 접속한다 :
       * interpark : <tr><th>분류</th><td>값</td>에서 텍스트 추출
       * yanolja : 페이지 타이틀 추출
       * 그 외 : 경고 로그 기록
       숙소 분류 텍스트에 '모텔'이 포함된 경우 '구분' 값을 '모텔'로 설정한다.
    - 새 탭은 작업 후 닫고 원래 탭으로 복귀한다.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver 인스턴스
        carib_utils (CaribUtils): CSV 다운로드 기능을 제공하는 CaribUtils 인스턴스

    Returns:
        pandas.DataFrame:
            '랜딩URL', '심사대상ID', '구분' 컬럼으로 구성된 DataFrame.
            - '구분'은 기본 None이며, 분류 결과에 따라 '모텔' 값이 반영될 수 있음.
    """
    logging.log("▷ [CARIB] 소재 자동 심사 → 시작", level="INFO")

    _setup_reviewer_option(driver, 'reviewer', carib_id=carib_id)
    time.sleep(2)

    button_selector = '#mainContent > div > div > div > div > button:nth-child(2)'  # CSV 다운로드 버튼
    csv_path = carib_utils.download_csv(button_selector)

    df_ad_creative = pd.read_csv(csv_path, encoding='utf-8')
    df_work_data = df_ad_creative[['랜딩URL', '심사대상ID']].copy()

    # 랜딩URL에 'hotel'이 포함되지 않은 데이터만 남김
    df_work_data = df_work_data[~df_work_data['랜딩URL'].str.contains("hotel|tour", case=False, na=False)]

    # 소재 구분용 컬럼 추가 (초기값 None)
    df_work_data['구분'] = None

    for idx, current_row in df_work_data.iterrows():
        landing_url = current_row['랜딩URL']

        # 인터파크/야놀자 사이트 작업 ------------------------------------------------------------------------------------- #
        driver.execute_script("window.open('');")
        new_tab = driver.window_handles[-1]
        original_tab = driver.window_handles[0]
        driver.switch_to.window(new_tab)

        elem_txt = None
        try:
            driver.get(landing_url)
            time.sleep(5)

            if 'interpark' in landing_url:
                WebDriverWait(driver, DEFAULT_WAIT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table > tbody")))

                elem_txt = driver.find_element(By.XPATH, "//tr[th[normalize-space(text())='분류']]/td").text

            elif 'yanolja' in landing_url:
                WebDriverWait(driver, DEFAULT_WAIT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div > div > h1")))

                elem_txt = driver.title
            else:
                logging.log(f"> 확인 되지 않은 사이트 (URL={landing_url})", level="WARNING")

            logging.log(f"> {landing_url}-{elem_txt}", level="INFO")
        except Exception as e:
            logging.log(f"> 처리 중 오류 발생 (URL={landing_url}) : {type(e).__name__}", level="ERROR")
            continue
        finally:
            # 새 탭 닫고 원래 탭으로 복귀(오류가 나도 반드시 복귀)
            try:
                driver.close()
            except Exception:
                pass
            driver.switch_to.window(original_tab)

        # 해당 숙소가 '모텔'인지 여부 확인
        if elem_txt and ('모텔' in elem_txt):
            df_work_data.at[idx, '구분'] = '모텔'
        # ------------------------------------------------------------------------------------------------------------ #

    logging.log("▷ [CARIB] 소재 자동 심사 → 완료", level="INFO")
    return df_work_data

def process_creative_hold(driver, df_work_data, test_mode=False):
    """
    모텔로 분류된 소재에 대해 '심사 보류' 처리를 수행한다.

    - 먼저 `_setup_reviewer_option(driver, 'target')`을 호출해 검색대상 모드로 전환한다.
    - df_work_data에서 '구분' 값이 '모텔'인 행만 추출하여 순회한다.
    - 각 심사대상ID를 검색창에 입력 후 조회를 수행하고,
      검색 결과가 없으면 경고 로그를 남기고 다음 항목으로 넘어간다.
    - 검색 결과가 있을 경우:
        * 전체 선택 체크박스를 클릭한다.
        * '심사 보류' 버튼을 클릭하고, 보류 입력 정보 모달(div.react-draggable)이 나타날 때까지 대기한다.
        * 모달 내부에서 보류사유 Select 박스를 열고 '92. [공통] 제한업종' 항목을 선택한다.
        * test_mode=True이면 팝업을 닫고 로그만 남긴다.
        * test_mode=False이면 '입력' 버튼을 눌러 실제 보류 처리를 진행하고,
          처리 완료 후 '데이터가 없습니다' 메시지가 나타날 때까지 대기한다.
    - 개별 심사대상ID 처리 중 오류가 발생하면 로그에 남기고 다음 항목을 계속 처리한다.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver 인스턴스
        df_work_data (pandas.DataFrame): '랜딩URL', '심사대상ID', '구분' 컬럼을 포함하는 DataFrame
        test_mode (bool, optional): True일 경우 실제 보류 처리 대신 팝업 닫기만 수행. 기본값 False.

    Returns:
        None

    Raises:
        None
        (내부적으로 발생하는 Selenium 예외는 개별 항목 처리에서 잡아내고
         로그만 남긴 후 다음 항목으로 넘어간다.)
    """
    logging.log("▷ [CARIB] 소재 심사 보류 → 시작", level="INFO")
    _setup_reviewer_option(driver, 'target')

    max_retries = constants.RETRY_COUNT
    wait_secs = getattr(constants, "RETRY_DELAY", 5)

    df_motel_only = df_work_data[df_work_data['구분'] == '모텔'].copy()

    for idx, current_row in df_motel_only.iterrows():
        review_target_id = current_row['심사대상ID']
        try:
            input_box = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="검색할 내용을 입력하세요."]')
            input_box.send_keys(Keys.CONTROL, 'a')
            input_box.send_keys(Keys.DELETE)
            input_box.send_keys(review_target_id)
            time.sleep(1)
            driver.find_element(By.CSS_SELECTOR, '#complex-form > button[type="submit"]').click()    # 조회 버튼
            time.sleep(3)

            if driver.execute_script('return document.querySelector("div.ant-empty-description")'):
                logging.log(f"> 검색 결과 없음 : {review_target_id}", level="WARNING")
                continue

            WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table > tbody > tr")))
            time.sleep(1)

            # 심사 보류 처리 ------------------------------------------------------------------------------------------- #
            driver.find_element(By.CSS_SELECTOR,  # 체크박스
                                'table > thead > tr > th > div > label > span > input[type="checkbox"]').click()
            time.sleep(1)
            # 버튼 클릭 재시도 로직
            for attempt in range(1, max_retries + 1):
                try:
                    driver.find_element(By.CSS_SELECTOR,  # 심사보류 버튼
                                        'button.ant-btn.css-l9pxc0.ant-btn-primary.ant-btn-dangerous.ant-btn-color-dangerous.ant-btn-variant-solid').click()

                    WebDriverWait(driver, DEFAULT_WAIT).until(  # 보류 입력 정보 창
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.react-draggable")))
                    break  # 성공 시 루프 종료
                except TimeoutException:
                    logging.log(
                        f"> 보류 입력 정보 창 미등장 : 재클릭 시도 {attempt}/{max_retries}", level="WARNING")
                    time.sleep(wait_secs)

            # 0) 모달 등장 대기 (스코프를 모달로 한정)
            modal = WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.react-draggable'))
            )
            time.sleep(1)
            # 1) 모달 내부의 보류사유 Select 박스 열기
            select_box = modal.find_element(By.CSS_SELECTOR, '.ant-select .ant-select-selector')
            try:
                select_box.click()
            except Exception:
                driver.execute_script("arguments[0].click();", select_box)

            # 2) 드롭다운(바디 포털) 등장 대기
            WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.ant-select-dropdown:not([aria-hidden="true"])')))

            # 3) 활성 인풋에 텍스트 입력 → 옵션 리스트 로딩 대기 → Enter로 확정
            driver.switch_to.active_element.send_keys(HOLD_REASON)
            WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.ant-select-item-option')))
            driver.switch_to.active_element.send_keys(Keys.ENTER)

            # 4) 선택 적용 확인 (모달 내부 셀렉트 영역에 원하는 텍스트가 표시될 때까지 대기)
            WebDriverWait(driver, DEFAULT_WAIT).until(EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, 'div.react-draggable .ant-select .ant-select-selector'), HOLD_REASON))
            time.sleep(2)

            # 테스트 모드면 '심사 보류' 처리 건너뜀
            if test_mode:
                driver.find_element(By.CSS_SELECTOR, 'div.popup-handle > button').click()    # (팝업창) 닫기 버튼
                logging.log("> (테스트 모드) '심사 보류' 처리 생략", level="INFO")
                time.sleep(1)
            else:
                for attempt in range(1, max_retries + 1):
                    try:
                        driver.find_element(By.CSS_SELECTOR,  # 입력 버튼
                                            'body > div > div > div > button.ant-btn.css-l9pxc0.ant-btn-primary.ant-btn-color-primary.ant-btn-variant-solid.ant-btn').click()
                        time.sleep(2)
                        WebDriverWait(driver, DEFAULT_WAIT).until(  # '데이터가 없습니다' 텍스트
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ant-empty-description")))

                        # 성공 시 루프 종료
                        break
                    except WebDriverException as e:
                        logging.log(
                            f"> 입력 버튼 클릭 실패({review_target_id}) : {type(e).__name__} 재시도 {attempt}/{max_retries}",level="WARNING"
                        )
                        time.sleep(wait_secs)
            # -------------------------------------------------------------------------------------------------------- #

        except (TimeoutException, WebDriverException, JavascriptException) as e:
            logging.log(f"> 심사대상ID 보류 처리 실패({review_target_id}) : {type(e).__name__}", level="WARNING")
            continue

    logging.log("▷ [CARIB] 소재 심사 보류 → 완료", level="INFO")
