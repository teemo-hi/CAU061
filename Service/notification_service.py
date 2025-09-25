import gspread
from gspread_dataframe import get_as_dataframe

from pathlib import Path
import requests
import json
import time

from Common.log import Log


class NotificationService:
    """
    카카오워크 알림 전송 및 구글 스프레드시트 수신자 로딩을 담당하는 서비스 클래스.
    """

    # 클래스 초기화
    logging = Log()

    @staticmethod
    def get_recipients_from_gsheet(test_mode=False):
        """
        구글 스프레드시트에서 수신자 목록을 읽어온다.

        - 특정 문서와 워크시트를 열어 '수신자' 컬럼을 DataFrame으로 변환한다.
        - NaN/빈값을 제거한 뒤 리스트로 변환하여 반환한다.
        - 최대 3회 재시도를 수행한다. 실패 시 예외 발생.
        - test_mode=False인 경우 현업 수신자에게 발송

        Args:
            test_mode (bool, optional): True일 경우 실제 현업 수신자가 아닌 개발자로 발송. 기본값 False.

        Returns:
            list[str]: 수신자 아이디 리스트

        Raises:
            Exception: 스프레드시트 로딩 실패 시
        """
        # 현재 파일의 디렉터리를 기준으로 베이스 디렉터리 설정
        base_dir = Path(__file__).resolve().parent.parent
        json_file_path = base_dir / 'Resource' / 'gspreadAPI_teemo.json'

        google_docs = '[RPA] 외부DSP 숙박/여행상품 자동 심사'
        google_account = gspread.service_account(filename=json_file_path)
        google_sheet = '외부DSP 숙박/여행상품 RPA 알림 수신자'

        # 테스트 모드면 시트명 변경
        if test_mode:
            google_sheet = '(테스트)RPA 알림 수신자'

        NotificationService.logging.log('▷ [Docs] 수신자 확인 → 시작', level="INFO")

        retry_count = 0
        max_retries = 3
        while retry_count <= max_retries:
            try:
                retry_count += 1
                docs_sheet = google_account.open(google_docs).worksheet(google_sheet)

                origin_df = get_as_dataframe(docs_sheet, dtype=str)
                recipients = origin_df['수신자'].dropna().tolist()

                NotificationService.logging.log('▷ [Docs] 수신자 확인 → 완료', level="INFO")
                return recipients
            except Exception as e:
                NotificationService.logging.log(f'> 재시도 중... ({retry_count}/3)', level="WARNING")
                time.sleep(10)

                if retry_count == max_retries:
                    raise Exception(f'> 구글 스프레드시트 불러오기 실패 : {e}')

    @staticmethod
    def send_kakaowork_message(kakaowork_api_key=None, recipients=None, contents=None):
        """
        카카오워크 알림 메시지를 전송한다.

        - recipients 리스트를 순회하면서 각 수신자에게 개별적으로 메시지를 전송한다.
        - 각 수신자 아이디에 '@knworks.co.kr'을 붙여 email 필드에 사용한다.
        - API 응답에서 'success' 값이 True면 전송 성공, False면 실패로 간주한다.
        - 성공/실패 여부는 로그로 남긴다.

        Args:
            kakaowork_api_key (str, optional): 카카오워크 API 키
            recipients (list[str], optional): 수신자 아이디 리스트 (ex: ["teemo.hi", "abc"])
            contents (str, optional): 전송할 메시지 내용

        Returns:
            None
        """
        NotificationService.logging.log(f'▷ [KAKAOWORK] 알림 전송 → 시작', level="INFO")

        for recipient in recipients:
            url = "https://api.kakaowork.com/v1/messages.send_by_email"

            # 필수 값 할당 ------------------------------------------------------------------------------------------- #
            headers = {
                "Authorization": f"Bearer {kakaowork_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "email": f"{recipient}@knworks.co.kr",
                "text": f"{contents}",
            }

            # 호출 --------------------------------------------------------------------------------------------------- #
            response = requests.post(url, headers=headers, json=payload)

            sendResult = json.loads(response.content).get('success')

            if sendResult:
                NotificationService.logging.log(f'> 알림 전송 성공', level="INFO")
            else:
                NotificationService.logging.log(f'> 알림 전송 실패 : {recipient} - {response.text}', level="WARNING")

        NotificationService.logging.log(f'▷ [KAKAOWORK] 알림 전송 → 완료', level="INFO")
