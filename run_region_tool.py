#!/usr/bin/env python3
"""
영역 선택 도구 간단 실행기
"""

import os
import sys

def main():
    """메인 함수"""
    print("🖼️  영역 선택 도구 실행기")
    print("=" * 40)
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    if not current_dir.endswith('test-sdp'):
        test_sdp_path = '\\\\wsl.localhost\\Udev\\home\\kckang\\work\\test-sdp'
        if os.path.exists(test_sdp_path):
            os.chdir(test_sdp_path)
            print(f"📁 디렉토리 변경: test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    # 기본 이미지 확인
    test_image = "input/17301.png"
    if not os.path.exists(test_image):
        print(f"❌ 테스트 이미지 없음: {test_image}")
        return
    
    print(f"✅ 테스트 이미지 확인: {test_image}")
    
    # 선택 메뉴
    print("\n🛠️  사용할 도구를 선택하세요:")
    print("1. 영역 선택만 (UI)")
    print("2. 영역 선택 + OCR 통합")
    print("3. 종료")
    
    while True:
        choice = input("\n선택 (1-3): ").strip()
        
        if choice == "1":
            print("\n🖼️  영역 선택 UI 실행...")
            try:
                from region_selector_ui import main as ui_main
                ui_main()
            except ImportError as e:
                print(f"❌ 모듈 import 오류: {e}")
            except Exception as e:
                print(f"❌ 실행 오류: {e}")
            break
            
        elif choice == "2":
            print("\n🖼️🤖 영역 선택 + OCR 통합 실행...")
            try:
                from region_ocr_integrated import main as integrated_main
                integrated_main()
            except ImportError as e:
                print(f"❌ 모듈 import 오류: {e}")
            except Exception as e:
                print(f"❌ 실행 오류: {e}")
            break
            
        elif choice == "3":
            print("👋 종료합니다.")
            break
            
        else:
            print("❌ 1, 2, 또는 3을 입력해주세요.")

if __name__ == "__main__":
    main()
