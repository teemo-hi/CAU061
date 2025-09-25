import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os


class EmailSender:
    def __init__(self, smtp_id, smtp_pw, smtp_server='smtp.kakaowork.com', smtp_port=465):
        """
        이메일 전송 클래스 초기화
        :param smtp_id: SMTP 서버 로그인 ID
        :param smtp_pw: SMTP 서버 로그인 패스워드
        :param smtp_server: SMTP 서버 주소 (기본값: 'smtp.kakaowork.com')
        :param smtp_port: SMTP 서버 포트 (기본값: 465)
        """
        self.smtp_id = smtp_id
        self.smtp_pw = smtp_pw
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_email(self, mail_subject, mail_body, mail_to, mail_cc='knw.rpa@knworks.co.kr', mail_bcc='', mail_attachments=None):
        """
        이메일 전송 메서드
        :param mail_subject: 이메일 제목
        :param mail_body: 이메일 본문 (텍스트 형식)
        :param mail_to: 수신자 이메일 주소 (문자열 또는 리스트)
        :param mail_cc: 참조자 이메일 주소 (문자열 또는 리스트, 기본값: None)
        :param mail_bcc: 비밀 참조자 이메일 주소 (문자열 또는 리스트, 기본값: None)
        :param mail_attachments: 첨부파일 경로 리스트 (기본값: None)
        :return: 이메일 전송 성공 여부 (True: 성공, False: 실패)
        """
        try:
            # 이메일 메시지 초기화
            message = MIMEMultipart()
            message['From'] = self.smtp_id

            # 수신자, 참조자, 비밀참조자를 문자열로 변환
            if isinstance(mail_to, list):
                mail_to = ', '.join(mail_to)
            if isinstance(mail_cc, list):
                mail_cc = ', '.join(mail_cc)
            if isinstance(mail_bcc, list):
                mail_bcc = ', '.join(mail_bcc)

            message['To'] = mail_to if mail_to else ''
            if mail_cc:
                message['Cc'] = mail_cc
            if mail_bcc:
                message['Bcc'] = mail_bcc

            message['Subject'] = mail_subject

            # 메일 본문 추가
            if mail_body != '':
                message.attach(MIMEText(mail_body, 'html'))  # 텍스트 본문

            # 첨부파일 추가 (있을 경우)
            if mail_attachments:
                for attachment in mail_attachments:
                    attachment_result = self.add_attachment(message, attachment)
                    if not attachment_result:  # 첨부파일 추가가 실패하면 예외 발생
                        raise Exception(f"첨부파일 {attachment} 추가에 실패했습니다.")

            # SMTP 서버에 연결 및 이메일 전송
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.smtp_id, self.smtp_pw)
                server.send_message(message)

            return True  # 이메일 전송 성공
        except Exception as e:
            raise Exception(f"이메일 전송에 실패했습니다: {e}")

    def add_attachment(self, message, file_path):
        """
        이메일에 첨부파일을 추가하는 함수
        :param message: 이메일 메시지 객체
        :param file_path: 첨부파일 경로
        :return: 첨부파일 처리 결과 (True: 성공, False: 실패)
        """
        try:
            # 첨부파일을 바이너리 형식으로 읽어 MIMEBase 객체 생성
            with open(file_path, 'rb') as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
                encoders.encode_base64(part)  # Base64로 인코딩

                # 파일 이름 추출 및 첨부 헤더 설정
                file_name = os.path.basename(file_path)
                part.add_header('Content-Disposition', f'attachment; filename={file_name}')

                # 메시지에 첨부파일 추가
                message.attach(part)
            return True  # 첨부파일 추가 성공
        except Exception as e:
            return False  # 첨부파일 추가 실패
