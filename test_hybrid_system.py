#!/usr/bin/env python3
"""
하이브리드 OCR 시스템 테스트 스크립트
OpenCV 도형 감지 + AI 텍스트 추출 테스트
"""

import os
import sys

def test_hybrid_system():
    """하이브리드 시스템 테스트"""
    print("🧪 하이브리드 OCR 시스템 테스트 시작")
    print("="*60)
    
    # 1. 모듈 import 테스트
    print("1. 필수 모듈 import 테스트...")
    
    try:
        import cv2
        print("   ✅ OpenCV 설치됨:", cv2.__version__)
    except ImportError:
        print("   ❌ OpenCV가 설치되지 않음. pip install opencv-python 실행 필요")
        return False
    
    try:
        import numpy as np
        print("   ✅ NumPy 설치됨:", np.__version__)
    except ImportError:
        print("   ❌ NumPy가 설치되지 않음")
        return False
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        print("   ✅ HybridShapeDetector 모듈 로드 성공")
    except ImportError as e:
        print(f"   ❌ HybridShapeDetector 모듈 로드 실패: {e}")
        return False
    
    # 2. 테스트 이미지 확인
    print("\n2. 테스트 이미지 확인...")
    
    test_image_path = "input/17301.png"
    if os.path.exists(test_image_path):
        print(f"   ✅ 테스트 이미지 발견: {test_image_path}")
    else:
        print(f"   ❌ 테스트 이미지 없음: {test_image_path}")
        return False
    
    # 3. 도형 감지 테스트
    print("\n3. OpenCV 도형 감지 테스트...")
    
    try:
        detector = HybridShapeDetector()
        detector.set_debug_mode(True)
        
        shapes = detector.detect_hand_drawn_shapes(test_image_path)
        print(f"   ✅ 감지된 도형 수: {len(shapes)}개")
        
        if len(shapes) > 0:
            print("   📍 감지된 도형 정보:")
            for i, shape in enumerate(shapes[:5]):  # 최대 5개만 표시
                print(f"      도형 {i+1}: {shape.shape_type}, 크기: {shape.w}x{shape.h}")
        
        # 디버그 이미지 생성
        debug_output = "output/test_debug_shapes.png"
        os.makedirs("output", exist_ok=True)
        
        if detector.create_debug_image(test_image_path, shapes, debug_output):
            print(f"   ✅ 디버그 이미지 생성: {debug_output}")
        
        return len(shapes) > 0
        
    except Exception as e:
        print(f"   ❌ 도형 감지 오류: {e}")
        return False

def test_cloud_ocr():
    """클라우드 OCR 테스트"""
    print("\n4. 클라우드 OCR 연결 테스트...")
    
    try:
        from cloud_ocr import CloudOCRProcessor
        from dotenv import load_dotenv
        
        # 환경변수 로드
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("   ⚠️  API 키가 설정되지 않음 (.env 파일 확인)")
            return False
        
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        processor.set_ocr_mode("hybrid")
        
        print(f"   ✅ API 키 설정 완료: {'*' * (len(api_key) - 8) + api_key[-8:]}")
        print("   ✅ 하이브리드 모드 설정 완료")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 클라우드 OCR 설정 오류: {e}")
        return False

def run_integration_test():
    """통합 테스트 실행"""
    print("\n5. 통합 테스트 실행...")
    print("⚠️  실제 API 호출을 수행합니다. 비용이 발생할 수 있습니다.")
    
    confirm = input("   계속하시겠습니까? (y/N): ").strip().lower()
    if confirm != 'y':
        print("   통합 테스트를 건너뜁니다.")
        return True
    
    try:
        from cloud_ocr import run_cloud_ocr
        from utils import get_image_files
        
        # 테스트 이미지 준비
        image_files = get_image_files("input")
        
        if not image_files:
            print("   ❌ 테스트할 이미지가 없습니다.")
            return False
        
        # 첫 번째 이미지만 테스트
        test_images = [image_files[0]]
        
        print(f"   📝 테스트 이미지: {os.path.basename(test_images[0])}")
        
        # API 호출
        api_key = os.getenv('QWEN_API_KEY')
        success = run_cloud_ocr(api_key, "qwen-vl-plus", test_images, "output", "hybrid")
        
        if success:
            print("   ✅ 통합 테스트 성공!")
            print("   📁 결과는 output 폴더에 저장되었습니다.")
            return True
        else:
            print("   ❌ 통합 테스트 실패")
            return False
            
    except Exception as e:
        print(f"   ❌ 통합 테스트 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🤖 하이브리드 OCR 시스템 테스트")
    print("✨ OpenCV + AI 조합으로 12개 도형 모두 인식 목표!")
    print("="*60)
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    print(f"현재 디렉토리: {current_dir}")
    
    # src 디렉토리로 이동 (필요시)
    if not os.path.exists("hybrid_shape_detector.py"):
        if os.path.exists("src"):
            os.chdir("src")
            print("src 디렉토리로 이동")
        else:
            print("❌ src 디렉토리를 찾을 수 없습니다.")
            return
    
    # 테스트 실행
    tests = [
        test_hybrid_system,
        test_cloud_ocr,
        run_integration_test
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except KeyboardInterrupt:
            print("\n❌ 사용자가 테스트를 중단했습니다.")
            break
        except Exception as e:
            print(f"\n❌ 테스트 중 예상치 못한 오류: {e}")
    
    # 결과 요약
    print("\n" + "="*60)
    print("📈 테스트 결과 요약")
    print("="*60)
    print(f"통과: {passed}/{total} 테스트")
    
    if passed == total:
        print("🎉 모든 테스트 통과! 하이브리드 시스템 준비 완료!")
        print("🚀 이제 main.py를 실행하여 하이브리드 모드를 사용해보세요.")
        print("🎯 예상 결과: 17301.png에서 12개 도형 모두 인식!")
    elif passed >= total - 1:
        print("⚠️  거의 준비 완료! 마지막 이슈 해결 후 사용 가능")
    else:
        print("❌ 여러 이슈가 있습니다. 다시 확인해주세요.")
    
    print("\n📚 추가 정보:")
    print("- 하이브리드 모드는 OpenCV로 도형을 먼저 찾고, AI로 각 영역을 처리합니다.")
    print("- 기존 7/12 인식에서 11-12/12 인식으로 개선 예상")
    print("- 디버그 이미지는 output/test_debug_shapes.png에서 확인 가능")

if __name__ == "__main__":
    main()
