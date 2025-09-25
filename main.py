# 하위 프로세스 및 패키지 참조 --------------------------------------------------------------------------------------- #
import knw_license

from Common.log import Log
from Common.email_sender import EmailSender
from Service.constants import Constants
from Service.notification_service import NotificationService
from Function.common_utils import CommonUtils
from Function.carib_utils import CaribUtils

from Service.CARIB_content_collector import process_content_collection
from Service.CARIB_content_reviewer import process_content_review, process_creative_hold

import os
import sys
import traceback

try:
    os.chdir(sys._MEIPASS)
except:
    os.chdir(os.getcwd())


# 전역 변수 ------------------------------------------------------------------------------------------------------------ #
constants = Constants()
logging = Log()
email = EmailSender(constants.SMTP_ID, constants.SMTP_PW)

utils = CommonUtils()
noti_service = NotificationService()

g_logFile = logging.get_log_paths()
g_developer = ['teemo.hi@knworks.co.kr']

# 상수 모음 ------------------------------------------------------------------------------------------------------------ #
CARIB_URL = 'https://kad-review.kakaosecure.net/waiting?reviewType=APPIER_BIZBOARD_DYNAMIC'


# main --------------------------------------------------------------------------------------------------------------- #
def run_pipeline(now=None, mailer=None, constants_obj=None, test_mode=False):
    _mailer = mailer or email
    _constants = constants_obj or constants

    logging.log(f'▷ [{_constants.PROCESS_NAME}] 시작', level='INFO')

    case_classify = utils.check_schedule_case(now=now)   # "A" / "B" / None
    carib_id, carib_pw = utils.decrypt_carib_account()

    carib_utils = CaribUtils(
        carib_url=CARIB_URL,
        carib_id=carib_id,
        carib_pw=carib_pw,
        logger=logging,
        download_dir=_constants.DOWNLOAD_DIR
    )

    driver = carib_utils.login()

    if case_classify == "A":
        # CaseA. 여행/숙박 소재 자동 수집 (7:20 ~ 15:40)
        try:
            # TODO: Case A 동작 수행
            process_content_collection(driver, test_mode=test_mode)
        finally:
            carib_utils.logout()
            carib_utils.quit()
    elif case_classify == "B":
        # CaseB. 소재 자동 심사 및 보류 처리 (17:00)
        try:
            # TODO: Case B 동작 수행
            df_work_data = process_content_review(driver, carib_utils, carib_id)

            if df_work_data is not None:
                save_path = os.path.join(constants.DOWNLOAD_DIR, "df_work_data_test.csv")
                df_work_data.to_csv(save_path, index=False, encoding="utf-8-sig")

            process_creative_hold(driver, df_work_data, test_mode=test_mode)
        finally:
            carib_utils.logout()
            carib_utils.quit()
    else:
        logging.log(f'> 해당 없음', level='INFO')

    recipients = NotificationService.get_recipients_from_gsheet(test_mode=test_mode)
    noti_service.send_kakaowork_message(kakaowork_api_key=_constants.WORK_API_KEY, recipients=recipients,
                                 contents=f'[{_constants.PROCESS_ID}], [완료]')

    logging.log(f'□ [{_constants.PROCESS_NAME}] 종료', level='INFO')

    _mailer.send_email(
        mail_subject=f'[{_constants.PROCESS_ID}] {_constants.PROCESS_NAME}, [완료]',
        mail_body='',
        mail_to=g_developer,
        mail_attachments=[g_logFile]
    )

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception:
        logging.log(f'※ [{constants.PROCESS_NAME}] 중 오류 : ' + traceback.format_exc())
        email.send_email(
            mail_subject=f'[{constants.PROCESS_ID}] {constants.PROCESS_NAME}, [실패]',
            mail_body='',
            mail_to=g_developer,
            mail_attachments=[g_logFile]
        )
