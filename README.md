# 외부DSP 심사 숙박/여행상품 소재 자동 분류 RPA (CAU061)

## 개요
- 업무코드: **CAU061**, 업무명: **외부DSP 심사 숙박/여행상품 소재 자동 분류 RPA**
- 기획 아지트: https://knw.agit.in/g/300076237/wall/429158697
- 개발 아지트: https://knw.agit.in/g/300093986/wall/436385134
- CARIB 심사 대기 시스템에 로그인하여 숙박·여행 광고 소재를 자동으로 수집하고 분류한 뒤, 결과를 알림과 이메일로 공유하는 데스크톱 RPA 파이프라인이다.

## 운영툴
- **CARIB**

## 프로세스 설명
1. **스케줄 판별**: `CommonUtils.check_schedule_case`가 현재 시간을 기준으로 Case A(07:20~15:40, 특정 분) 또는 Case B(17:00)를 선택한다.
2. **CARIB 로그인**: 암호화된 계정을 복호화한 뒤 `CaribUtils.login()`으로 CARIB에 접속하고 드라이버 세션을 확보한다.
3. **Case A – 여행/숙박 소재 자동 수집**: 지정된 광고계정별로 검색→체크박스 선택→(실행 모드에서) "내가 처리하기" 클릭까지 수행하여 처리 대상을 수집한다.
4. **Case B – 소재 자동 심사 및 보류**:
   - CSV를 다운로드하여 랜딩 URL과 심사대상 ID를 취합하고, 모텔 관련 문구가 포함된 소재를 "모텔"로 분류한다.
   - "모텔"로 분류된 ID에 대해 심사 보류 팝업을 열어 지정 사유로 입력하거나(실행 모드) 팝업만 닫는다(테스트 모드).
5. **로그아웃 및 종료 처리**: CARIB에서 로그아웃 후 드라이버를 종료하고, 카카오워크 알림 및 이메일로 완료/오류 결과를 전파한다.

## 프로젝트 구조
```
CAU061/
├── Common/                     # 공통 인프라 모듈 (로그, 메일, 구성)
│   ├── config.py
│   ├── email_sender.py          # SMTP 메일 발송 유틸리티
│   └── log.py                   # 파일/콘솔 로그 관리
├── Function/                    # 업무 공통/전용 유틸
│   ├── common_utils.py          # 스케줄 판별, 계정 복호화 등
│   └── carib_utils.py           # CARIB 로그인·CSV 다운로드 래퍼
├── Resource/                    # UI 및 리소스 자원
│   ├── icon.ico
│   └── main.ui
├── Service/                     # 핵심 비즈니스 로직
│   ├── CARIB_content_collector.py  # Case A: 소재 수집
│   ├── CARIB_content_reviewer.py   # Case B: 심사/보류 처리
│   ├── constants.py             # 환경/프로세스 상수 정의
│   └── notification_service.py
├── main.py                      # 파이프라인 진입점
├── main.spec / main.patched.spec
├── main_test.py                 # 유닛 테스트 스켈레톤
└── setup/                       # 배포/빌드 스크립트
```