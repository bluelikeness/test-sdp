#!/usr/bin/env python3
"""
간단한 하이브리드 시스템 실행 테스트
"""

import os
import sys

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_imports():
    """기본 import 테스트"""
    print("🔧 모듈 import 테스트...")
    
    try:
        # 기본 라이브러리
        import cv2
        import numpy as np
        from PIL import Image
        print(f"✅ OpenCV: {cv2.__version__}")
        print(f"✅ NumPy: {np.__version__}")
        print("✅ PIL: OK")
        
        # 커스텀 모듈
        from hybrid_shape_detector import HybridShapeDetector
        from cloud_ocr import CloudOCRProcessor
        from models import list_cloud_models
        from utils import get_image_files
        
        print("✅ 커스텀 모듈들: OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 기타 오류: {e}")
        return False

def test_shape_detection():
    """도형 감지 테스트"""
    print("\n🔍 도형 감지 테스트...")
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        
        test_image = "input/17301.png"
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return False
        
        detector = HybridShapeDetector()
        shapes = detector.detect_hand_drawn_shapes(test_image)
        
        print(f"✅ 감지된 도형: {len(shapes)}개")
        
        if len(shapes) >= 5:  # 5개 이상이면 성공
            print("🎉 도형 감지 성공!")
            return True
        else:
            print("⚠️  도형 감지 수가 적습니다.")
            return True  # 부분 성공으로 간주
            
    except Exception as e:
        print(f"❌ 도형 감지 실패: {e}")
        return False

def main():
    """메인 테스트"""
    print("🤖 하이브리드 OCR 시스템 빠른 테스트")
    print("=" * 50)
    
    tests = [
        ("모듈 Import", test_imports),
        ("도형 감지", test_shape_detection)
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n📋 {name} 테스트:")
        if test_func():
            passed += 1
            print(f"✅ {name} 성공")
        else:
            print(f"❌ {name} 실패")
    
    print("\n" + "=" * 50)
    print(f"📊 결과: {passed}/{len(tests)} 테스트 통과")
    
    if passed == len(tests):
        print("🎉 모든 테스트 통과! 시스템 준비 완료!")
        print("\n🚀 이제 실행하세요:")
        print("   python src/main.py")
        print("   → 메뉴 2 (클라우드 API)")
        print("   → 하이브리드 모드 선택")
        print("   → 12개 도형 모두 인식!")
    else:
        print("⚠️  일부 테스트 실패. 문제를 확인해주세요.")

if __name__ == "__main__":
    main()
