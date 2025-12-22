# main_test.py

from datetime import datetime
import main


class MockEmailSender:
    def send_email(self, mail_subject, mail_body, mail_to, mail_attachments=None):
        print(f"[MOCK-EMAIL] {mail_subject}")

class MockConstants:
    PROCESS_ID = "CAU061 (테스트)"
    PROCESS_NAME = "CARIB 파이프라인 (테스트)"

    DOWNLOAD_DIR = r"C:\kakao\work\knwrpa\python\CAU061\download"

    WORK_API_KEY = '9a08d322.9267c88fd5b44504a6724c0d018b236a'

if __name__ == "__main__":
    main.run_pipeline(
        now=datetime(2025, 11, 21, 7, 34),
        mailer=MockEmailSender(),
        constants_obj=MockConstants,
        test_mode=True   # 테스트 모드 켜기(True)
    )
