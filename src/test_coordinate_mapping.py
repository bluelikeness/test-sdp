#!/usr/bin/env python3
"""
텍스트 좌표 매핑 테스트 도구
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

def test_coordinate_mapping():
    """좌표 매핑 기능 테스트"""
    print("🎯 텍스트 좌표 매핑 테스트")
    print("=" * 50)
    
    # 사용 가능한 OCR 라이브러리 확인
    ocr_available = []
    
    try:
        import easyocr
        ocr_available.append("EasyOCR")
        print("✅ EasyOCR 사용 가능")
    except ImportError:
        print("❌ EasyOCR 설치되지 않음")
    
    if not ocr_available:
        print("⚠️  EasyOCR이 설치되지 않았습니다. 추정 방법을 사용합니다.")
        print("   더 정확한 좌표를 원한다면 EasyOCR을 설치하세요:")
        print("   pip install easyocr")
    
    # 테스트 이미지 선택
    from utils import get_image_files
    
    base_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(base_dir)
    input_dir = os.path.join(parent_dir, 'input')
    output_dir = os.path.join(parent_dir, 'output')
    
    image_files = get_image_files(input_dir)
    
    if not image_files:
        print("❌ input 폴더에 테스트할 이미지가 없습니다.")
        return
    
    print(f"\n📁 발견된 이미지: {len(image_files)}개")
    for i, img in enumerate(image_files):
        print(f"  {i+1}. {os.path.basename(img)}")
    
    # 이미지 선택
    if len(image_files) == 1:
        selected_image = image_files[0]
        print(f"\n🖼️  자동 선택: {os.path.basename(selected_image)}")
    else:
        while True:
            try:
                choice = input(f"\n이미지를 선택하세요 (1-{len(image_files)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(image_files):
                    selected_image = image_files[idx]
                    break
                else:
                    print(f"❌ 1-{len(image_files)} 사이의 숫자를 입력해주세요.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
            except KeyboardInterrupt:
                print("\n프로그램을 종료합니다.")
                return
    
    # OCR 방법 선택
    methods = []
    if "EasyOCR" in ocr_available:
        methods.append("easyocr")
    methods.append("estimate")  # 추정 방법은 항상 가능
    
    print("\n🔧 사용할 방법을 선택하세요:")
    method_idx = 1
    if "easyocr" in methods:
        print(f"{method_idx}. EasyOCR (가장 정확, GPU 권장)")
        method_idx += 1
    print(f"{method_idx}. 추정 방법 (EasyOCR 없이)")
    print(f"{method_idx + 1}. 자동 선택 (사용 가능한 최적 방법)")
    
    while True:
        try:
            choice = input(f"\n선택 (1-{method_idx + 1}): ").strip()
            choice_num = int(choice)
            
            if choice_num == method_idx + 1:  # 자동 선택
                method = "auto"
                break
            elif 1 <= choice_num <= method_idx:
                method_map = {}
                idx = 1
                if "easyocr" in methods:
                    method_map[idx] = "easyocr"
                    idx += 1
                method_map[idx] = "estimate"
                
                method = method_map[choice_num]
                break
            else:
                print(f"❌ 1-{method_idx + 1} 사이의 숫자를 입력해주세요.")
        except ValueError:
            print("❌ 숫자를 입력해주세요.")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            return
    
    # Cloud API로 먼저 텍스트 추출
    print("\n📡 Cloud API로 텍스트 추출 중...")
    api_key = os.getenv('QWEN_API_KEY')
    
    extracted_text = None
    if api_key and api_key != "your_api_key_here":
        try:
            from cloud_ocr import CloudOCRProcessor
            processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
            extracted_text, process_time = processor.process_image(selected_image)
            
            if extracted_text and not extracted_text.startswith("연결 실패"):
                print(f"✅ 텍스트 추출 완료 ({process_time:.2f}초)")
                print(f"📝 추출된 텍스트 ({len(extracted_text)}자):")
                print("-" * 30)
                print(extracted_text[:200] + ("..." if len(extracted_text) > 200 else ""))
                print("-" * 30)
            else:
                print(f"❌ Cloud API 실패: {extracted_text}")
                extracted_text = None
                
        except Exception as e:
            print(f"❌ Cloud API 오류: {e}")
            extracted_text = None
    
    # Cloud API 실패 시 더미 텍스트 사용
    if not extracted_text:
        print("⚠️  Cloud API를 사용할 수 없습니다. 더미 텍스트를 사용합니다.")
        extracted_text = "텍스트 추출 테스트\n좌표 매핑 기능 확인\n이미지 분석 결과"
    
    # 좌표 매핑 실행
    print(f"\n🎯 좌표 매핑 시작 (방법: {method})...")
    
    try:
        from text_coordinate_mapping import create_text_coordinate_mapping
        
        # 테스트 출력 디렉토리 생성
        from utils import create_output_directory
        test_output_dir = create_output_directory(output_dir, "coordinate_test")
        
        success = create_text_coordinate_mapping(
            selected_image, extracted_text, test_output_dir, method=method
        )
        
        if success:
            print("\n✅ 좌표 매핑 완료!")
            print(f"📁 결과 위치: {test_output_dir}")
            print("\n📋 생성된 파일들:")
            
            # 생성된 파일 목록 표시
            if os.path.exists(test_output_dir):
                files = os.listdir(test_output_dir)
                for file in sorted(files):
                    if file.endswith(('.png', '.jpg', '.txt')):
                        print(f"  ✓ {file}")
        else:
            print("❌ 좌표 매핑 실패")
            
    except Exception as e:
        print(f"❌ 좌표 매핑 오류: {e}")
        import traceback
        traceback.print_exc()

def install_ocr_libraries():
    """OCR 라이브러리 설치 가이드"""
    print("📦 OCR 라이브러리 설치 가이드")
    print("=" * 40)
    
    print("\n🎯 더 정확한 텍스트 좌표 매핑을 위해 OCR 라이브러리를 설치하세요:")
    
    print("\n1️⃣  EasyOCR (권장):")
    print("   - 가장 정확한 결과")
    print("   - 다양한 언어 지원")
    print("   - GPU 가속 지원")
    print("   설치: pip install easyocr")
    
    print("\n2️⃣  PaddleOCR:")
    print("   - 빠른 처리 속도")
    print("   - 중국어 특화")
    print("   - CPU에서도 빠름")
    print("   설치: pip install paddlepaddle paddleocr")
    
    print("\n💡 설치 후 다시 실행하면 더 정확한 좌표 매핑이 가능합니다!")

def main():
    """메인 함수"""
    while True:
        print("\n🎯 텍스트 좌표 매핑 도구")
        print("=" * 30)
        print("1. 좌표 매핑 테스트 실행")
        print("2. EasyOCR 설치 가이드")
        print("3. 종료")
        
        choice = input("\n선택하세요 (1-3): ").strip()
        
        if choice == "1":
            test_coordinate_mapping()
        elif choice == "2":
            install_ocr_libraries()
        elif choice == "3":
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 1-3 사이의 숫자를 입력해주세요.")

if __name__ == "__main__":
    main()
