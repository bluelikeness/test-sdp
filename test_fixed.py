#!/usr/bin/env python3
import subprocess
import sys
import os

# 현재 디렉토리를 test-sdp로 설정
test_sdp_path = r'\\wsl.localhost\Udev\home\kckang\work\test-sdp'
os.chdir(test_sdp_path)

print("🧪 Smart Region OCR 수정 버전 테스트")
print("=" * 50)
print(f"현재 디렉토리: {os.getcwd()}")

try:
    # smart_region_ocr.py 실행
    result = subprocess.run([
        sys.executable, 'smart_region_ocr.py'
    ], capture_output=True, text=True, timeout=120)
    
    print("📤 STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("\n📤 STDERR:")
        print(result.stderr)
    
    print(f"\n📊 Exit Code: {result.returncode}")
    
    if result.returncode == 0:
        print("\n🎉 실행 성공!")
    else:
        print("\n❌ 실행 실패")
        
except subprocess.TimeoutExpired:
    print("⏰ 실행 시간 초과 (120초)")
except Exception as e:
    print(f"❌ 실행 오류: {e}")
