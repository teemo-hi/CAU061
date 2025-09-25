# common_utils.py
from datetime import datetime, time
from cryptography.fernet import Fernet

import traceback

from Common.log import Log

# 클래스 초기화
logging = Log()


class CommonUtils:
    """
    공통 유틸리티 클래스

    - 스케줄 판별(케이스 A/B)을 포함한 범용 유틸 메서드를 제공한다.
    - 스케줄 기준 시간은 클래스 속성으로 관리하여 손쉽게 조정할 수 있다.

    Attributes:
        CASE_A_START (time): 케이스 A 시작 시각 (기본 07:20)
        CASE_A_END (time): 케이스 A 종료 시각 (기본 15:40)
        CASE_A_MINUTES (tuple[int, ...]): 케이스 A 실행 분 (기본 5, 20, 40분)
        CASE_B_TIME (time): 케이스 B 실행 시각 (기본 17:00)
    """

    # --- 스케줄 규칙(필요 시 값만 수정해서 사용) ---
    CASE_A_START = time(7, 20)  # 케이스 A 시작 시각
    CASE_A_END = time(15, 40)  # 케이스 A 종료 시각
    CASE_A_MINUTES = (5, 20, 40)  # 케이스 A 실행 분

    CASE_B_TIME = time(17, 0)  # 케이스 B 실행 시각

    @classmethod
    def check_schedule_case(cls, now=None):
        """
        현재 시간이 케이스 A 또는 케이스 B 실행 시간인지 판별한다.

        Parameters:
            now (datetime): 기준 시간 (기본값은 현재 시간)

        Returns:
            "A" → 케이스 A 실행 시간
            "B" → 케이스 B 실행 시간
            None → 해당 없음
        """
        current = now or datetime.now()
        current_t = current.time()

        # Case A 판별
        if cls.CASE_A_START <= current_t <= cls.CASE_A_END:
            if current.minute in cls.CASE_A_MINUTES:
                return "A"

        # Case B 판별
        if current_t.hour == cls.CASE_B_TIME.hour and current_t.minute == cls.CASE_B_TIME.minute:
            return "B"

        return None

    @staticmethod
    def decrypt_carib_account():
        """
        카리브 계정(아이디, 비밀번호)을 복호화하는 함수

        미리 정의된 Fernet 암호화 키를 사용하여 저장된 카리브 계정 정보를 복호화.
        복호화에 실패할 경우 오류 로그를 남기고 None을 반환.

        return:
            tuple : (carib_id, carib_pw) 복화화 성공 시
            None : 복호화 실패 시
        """
        try:
            logging.log(f'▷ [CommonUtils] Carib 계정 복호화 → 시작', level="INFO")

            encrypt_key = b'QQkA27VdTmO0U1K0EEK_vU9wcvQOQJGY3C6M_uxQxBs='
            encrypt_id = 'gAAAAABoor4N9o1SHRq7V37IzV1H_P4F-pghGX9WV4JXYROOQvpMnwPXexjNKc7EcdlM2nhZKBODwF2sHJDZH8VMXp7PvF47ng=='
            encrypt_pw = 'gAAAAABoor4NuKshifaWjXklGyEJCkfZlmhmnSaTU1cMqoPQsKmdDihNLBnK-FIsGjJFRswI_lxbDMlGEys3W8k47GirRcAwXQ=='

            cipher_suite = Fernet(encrypt_key)

            carib_id = cipher_suite.decrypt(encrypt_id.encode()).decode()
            carib_pw = cipher_suite.decrypt(encrypt_pw.encode()).decode()

            logging.log(f'▷ [CommonUtils] Carib 계정 복호화 → 완료', level="INFO")
            return carib_id, carib_pw

        except Exception:
            logging.log(f"▷ [CommonUtils] Carib 계정 복호화 → 실패 : {traceback.format_exc()}", level="ERROR")
            return None
