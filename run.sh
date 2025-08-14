#!/bin/bash

# 실행 스크립트
echo "🚀 OCR 성능 테스트 도구 시작..."

# 가상환경 활성화 확인
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다. install.sh를 먼저 실행해주세요."
    exit 1
fi

# 가상환경 활성화
source venv/bin/activate

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다. install.sh를 먼저 실행해주세요."
    exit 1
fi

# 메인 프로그램 실행
python src/main.py
