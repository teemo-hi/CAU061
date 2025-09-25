import configparser
import os


class Config:
    def __init__(self, file_name):
        self.file_name = file_name
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        """Config 파일을 읽어들입니다. 파일이 없으면 기본 설정을 생성합니다."""
        if os.path.exists(self.file_name):
            self.config.read(self.file_name)
        else:
            self.save()  # 파일이 없으면 기본 설정을 저장

    def get(self, section, option, default=''):
        """설정 파일에서 값을 가져옵니다. 없으면 기본값을 반환합니다."""
        return self.config.get(section, option, fallback=default)

    def set(self, section, option, value):
        """설정 파일에 값을 저장합니다. 섹션이 없으면 새로 추가합니다."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)

    def save(self):
        """설정 파일을 저장합니다."""
        with open(self.file_name, 'w') as configfile:
            self.config.write(configfile)
