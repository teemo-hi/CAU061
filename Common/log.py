import logging
import datetime
import os
import sys
from pathlib import Path

class Log:
    def __init__(self, exec_dir: str = '', logger_name: str = 'knwrpa'):
        # 로그 디렉토리
        if exec_dir:
            self.log_dir = os.path.join(exec_dir, 'Log')
        else:
            self.log_dir = Path(sys.argv[0]).parent / 'Log'
        os.makedirs(self.log_dir, exist_ok=True)

        # 파일명 구성
        self.log_file = os.path.join(self.log_dir, f'Log_{self._current_date_str()}.log')
        self.target_path = Path(sys.executable).parent / f'{self._current_date_str()}_작업로그.log'

        # === 전용 로거 구성 (루트 상태와 무관하게 항상 내 핸들러 사용) ===
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # 루트로 전파 금지 → 외부 설정/핸들러 영향 배제

        # 이 로거에 이미 붙어있던 핸들러 제거(중복 방지)
        for h in list(self.logger.handlers):
            self.logger.removeHandler(h)

        # 포맷터
        fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                datefmt='%Y/%m/%d %H:%M')

        # 파일 핸들러 (메모장 호환 위해 BOM 포함)
        fh = logging.FileHandler(self.log_file, encoding='euc-kr')
        fh.setFormatter(fmt)
        self.logger.addHandler(fh)

        # 콘솔 핸들러 (원래 print로 화면에 찍던 역할 대체)
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        self.logger.addHandler(sh)

    def _current_date_str(self):
        return datetime.datetime.now().strftime("%Y%m%d")

    def log(self, msg, level='DEBUG', create_log=False):
        """지정된 로그 레벨로 메시지를 기록하고, 필요시 로그 파일을 복사합니다."""
        level = level.upper()
        if level == "ERROR":
            self.logger.error(msg)
        elif level == "INFO":
            self.logger.info(msg)
        elif level == "WARNING":
            self.logger.warning(msg)
        elif level == "DEBUG":
            self.logger.debug(msg)
        else:
            # 알 수 없는 레벨이면 INFO로 처리
            self.logger.info(msg)

        # 기존 코드의 print는 콘솔 핸들러로 대체되므로 생략 가능
        # print(f"{level}: {msg}")

        if create_log:
            self._copy_log()

    def get_log_paths(self) -> str:
        """현재 사용 중인 로그 파일(절대경로)을 반환합니다."""
        return str(self.log_file)
