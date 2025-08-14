@echo off
REM Windows 설치 스크립트

echo 🚀 OCR 성능 테스트 도구 설치 중...

REM 가상환경 생성
echo 📦 가상환경 생성 중...
python -m venv venv

REM 가상환경 활성화
echo 🔧 가상환경 활성화 중...
call venv\Scripts\activate

REM 패키지 설치
echo 📚 패키지 설치 중...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM 환경파일 복사
if not exist .env (
    echo ⚙️ 환경파일 생성 중...
    copy .env.example .env
    echo ✅ .env 파일이 생성되었습니다. API 키를 설정해주세요.
) else (
    echo ℹ️  .env 파일이 이미 존재합니다.
)

echo.
echo ✅ 설치가 완료되었습니다!
echo.
echo 📋 다음 단계:
echo 1. .env 파일을 열어서 QWEN_API_KEY를 설정하세요
echo 2. input 폴더에 테스트할 이미지를 넣으세요  
echo 3. 다음 명령어로 프로그램을 실행하세요:
echo    venv\Scripts\activate
echo    python src\main.py

pause
