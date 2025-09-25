# template
## 프로젝트 템플릿

### project_name/
### │
### ├── Common/             # 공통 모듈
### │   ├── config.py		# 설정(ini)
### │   ├── email.py		# 메일
### │   └── log.py			# 로그
### │
### ├── Function/           # 개인 유틸
### │   └── util.py			# 유틸 함수 모음
### │
### ├── Service/            # 비즈니스 로직
### │   └── constants.py	# 상수
### │
### ├── Res/                # 리소스 파일
### │   ├── *.json  	    # json 파일
### │   ├── icon.ico	    # 아이콘 파일
### │   └── main.ui  	    # UI 파일
### │
### ├── tests/              # 테스트 코드
### │ 	└── test_main.py	# 메인 테스트
### │
### ├── main.py             # 진입점 스크립트
### ├── .gitignore          # Git 무시 파일 설정
### ├── requirements.txt    # 의존성 파일
### └── README.md           # 프로젝트 설명