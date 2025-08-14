@echo off
REM Windows 실행 스크립트

echo 🚀 OCR 성능 테스트 도구 시작...

REM 가상환경 확인
if not exist venv (
    echo ❌ 가상환경이 없습니다. install.bat을 먼저 실행해주세요.
    pause
    exit /b 1
)

REM .env 파일 확인
if not exist .env (
    echo ❌ .env 파일이 없습니다. install.bat을 먼저 실행해주세요.
    pause
    exit /b 1
)

REM 가상환경 활성화
call venv\Scripts\activate

REM 메인 프로그램 실행
python src\main.py

pause
