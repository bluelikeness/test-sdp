#!/usr/bin/env python3
"""
웹 기반 영역 선택 도구 실행기 (OpenCV GUI 대체)
"""

import os
import sys
import subprocess

def check_dependencies():
    """필요한 의존성 확인"""
    print("🔍 의존성 확인 중...")
    
    required_packages = {
        'flask': 'Flask',
        'PIL': 'Pillow', 
        'cv2': 'opencv-python',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 설치 필요한 패키지:")
        for package in missing_packages:
            print(f"   pip install {package}")
        
        install_choice = input("\n자동으로 설치하시겠습니까? (y/n): ").lower()
        if install_choice in ['y', 'yes']:
            for package in missing_packages:
                print(f"📦 {package} 설치 중...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', package])
        else:
            print("의존성을 먼저 설치해주세요.")
            return False
    
    return True

def main():
    """메인 함수"""
    print("🌐 웹 기반 영역 선택 도구 실행기")
    print("=" * 50)
    
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
    
    # 의존성 확인
    if not check_dependencies():
        return
    
    # 기본 이미지 확인
    test_image = "input/17301.png"
    if not os.path.exists(test_image):
        print(f"❌ 테스트 이미지 없음: {test_image}")
        return
    
    print(f"✅ 테스트 이미지 확인: {test_image}")
    
    # 선택 메뉴
    print("\n🛠️  사용할 웹 도구를 선택하세요:")
    print("1. 웹 영역 선택만")
    print("2. 웹 영역 선택 + OCR 통합")
    print("3. 종료")
    
    while True:
        choice = input("\n선택 (1-3): ").strip()
        
        if choice == "1":
            print("\n🌐 웹 영역 선택 도구 실행...")
            try:
                from web_region_selector import main as web_main
                web_main()
            except ImportError as e:
                print(f"❌ 모듈 import 오류: {e}")
            except Exception as e:
                print(f"❌ 실행 오류: {e}")
            break
            
        elif choice == "2":
            print("\n🌐🤖 웹 영역 선택 + OCR 통합 실행...")
            try:
                from web_region_ocr_integrated import main as integrated_main
                integrated_main()
            except ImportError as e:
                print(f"❌ 모듈 import 오류: {e}")
                print("💡 필요한 모듈들을 확인하고 다시 시도해주세요.")
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
