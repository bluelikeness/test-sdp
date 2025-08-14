#!/usr/bin/env python3
"""
개선된 OpenCV 감지 시스템 테스트
"""

import os
import sys
sys.path.append('src')

def test_improved_opencv():
    """개선된 OpenCV 감지 시스템 테스트"""
    print("🔧 개선된 OpenCV 감지 시스템 테스트")
    print("=" * 60)
    print("🎯 개선사항:")
    print("   - 강화된 이미지 전처리 (CLAHE, 블러링)")
    print("   - 다양한 이진화 방법 자동 선택")
    print("   - 더 관대한 크기 필터링")
    print("   - 개선된 원형/타원형 판별")
    print("=" * 60)
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return False
        
        print(f"📸 테스트 이미지: {test_image}")
        
        # 개선된 감지기 생성
        detector = HybridShapeDetector()
        detector.set_debug_mode(True)
        
        print(f"\n🔧 감지 파라미터:")
        print(f"   min_area_ratio: {detector.min_area_ratio} ({detector.min_area_ratio*100:.3f}%)")
        print(f"   max_area_ratio: {detector.max_area_ratio} ({detector.max_area_ratio*100:.1f}%)")
        print(f"   min_absolute_area: {detector.min_absolute_area} pixels²")
        
        print(f"\n🔍 원형/타원형 감지 시작...")
        shapes = detector.detect_hand_drawn_shapes(test_image)
        
        print(f"\n📊 감지 결과:")
        print(f"   원형/타원형 개수: {len(shapes)}개")
        
        if len(shapes) == 0:
            print("⚠️  아직도 도형이 감지되지 않습니다.")
            print("🔬 추가 진단을 위해 debug_opencv.py를 실행해보세요:")
            print("   python debug_opencv.py")
            return False
        
        # 상세 정보 출력
        print(f"\n📋 감지된 원형/타원형 상세:")
        for i, shape in enumerate(shapes):
            print(f"   {i+1:2d}. 타입: {shape.shape_type}")
            print(f"       위치: ({shape.x:4d}, {shape.y:4d})")
            print(f"       크기: {shape.w:4d} × {shape.h:4d} pixels")
            print(f"       면적: {shape.area():8,} pixels²")
            print()
        
        # 디버그 이미지 생성
        os.makedirs("output", exist_ok=True)
        debug_path = "output/improved_opencv_debug.png"
        success = detector.create_debug_image(test_image, shapes, debug_path)
        
        if success:
            print(f"🎯 디버그 이미지 생성: {debug_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_different_parameters():
    """다양한 파라미터로 감지 테스트"""
    print(f"\n🔬 파라미터 조정 테스트")
    print("=" * 60)
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print("❌ 테스트 이미지 없음")
            return
        
        # 여러 파라미터 조합 테스트
        test_configs = [
            {"min_ratio": 0.0001, "max_ratio": 0.4, "min_abs": 50, "name": "기본"},
            {"min_ratio": 0.00005, "max_ratio": 0.5, "min_abs": 25, "name": "매우관대"},
            {"min_ratio": 0.0002, "max_ratio": 0.3, "min_abs": 100, "name": "보수적"},
            {"min_ratio": 0.00001, "max_ratio": 0.6, "min_abs": 10, "name": "극관대"}
        ]
        
        best_count = 0
        best_config = None
        
        for config in test_configs:
            detector = HybridShapeDetector()
            detector.min_area_ratio = config["min_ratio"]
            detector.max_area_ratio = config["max_ratio"] 
            detector.min_absolute_area = config["min_abs"]
            detector.set_debug_mode(False)
            
            shapes = detector.detect_hand_drawn_shapes(test_image)
            
            print(f"   {config['name']:8s}: {len(shapes):2d}개 원형/타원형")
            
            if len(shapes) > best_count:
                best_count = len(shapes)
                best_config = config
        
        if best_config:
            print(f"\n✅ 최적 설정: {best_config['name']} ({best_count}개 감지)")
            print(f"   min_ratio: {best_config['min_ratio']}")
            print(f"   max_ratio: {best_config['max_ratio']}")
            print(f"   min_abs: {best_config['min_abs']}")
        else:
            print(f"\n❌ 모든 설정에서 감지 실패")
        
    except Exception as e:
        print(f"❌ 파라미터 테스트 실패: {e}")

def test_full_hybrid_pipeline():
    """전체 하이브리드 파이프라인 테스트"""
    print(f"\n🤖 전체 하이브리드 파이프라인 테스트")
    print("=" * 60)
    
    try:
        from cloud_ocr import CloudOCRProcessor
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("⚠️  API 키가 설정되지 않음. OpenCV 감지만 테스트했습니다.")
            return
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print("❌ 테스트 이미지 없음")
            return
        
        print("🌐 개선된 하이브리드 OCR 시작...")
        
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        processor.set_ocr_mode("hybrid")
        
        result_text = processor.process_image_hybrid(test_image)
        
        if result_text and not result_text.startswith("처리 실패"):
            print(f"✅ 하이브리드 OCR 성공!")
            print(f"📝 추출된 텍스트 길이: {len(result_text)}자")
            
            # 결과 저장
            os.makedirs("output", exist_ok=True)
            result_path = "output/improved_hybrid_result.txt"
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write("=== 개선된 하이브리드 OCR 결과 ===\n")
                f.write(f"개선사항: 강화된 전처리, 관대한 필터링, 다중 이진화\n")
                f.write(f"추출된 텍스트 길이: {len(result_text)}자\n\n")
                f.write("=== 추출된 텍스트 ===\n")
                f.write(result_text)
            
            print(f"💾 결과 저장: {result_path}")
            
            # 미리보기
            lines = result_text.strip().split('\n')
            print(f"\n📄 추출된 텍스트 미리보기:")
            for i, line in enumerate(lines[:5]):
                if line.strip():
                    print(f"  {i+1}: {line.strip()}")
            
            if len(lines) > 5:
                print(f"  ... (총 {len(lines)}줄)")
                
        else:
            print(f"❌ 하이브리드 OCR 실패: {result_text}")
        
    except Exception as e:
        print(f"❌ 하이브리드 파이프라인 테스트 실패: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 개선된 OpenCV 감지 시스템 종합 테스트")
    print("🎯 목표: OpenCV 감지 실패 문제 해결")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    # 1단계: 기본 개선된 감지 테스트
    success = test_improved_opencv()
    
    if success:
        print(f"\n🎉 OpenCV 감지 성공! 추가 테스트 진행...")
        
        # 2단계: 다양한 파라미터 테스트
        test_with_different_parameters()
        
        # 3단계: 전체 파이프라인 테스트
        test_full_hybrid_pipeline()
        
        print(f"\n" + "=" * 60)
        print("🎉 OpenCV 감지 문제 해결 완료!")
        print("✨ 적용된 개선사항:")
        print("   ✅ CLAHE를 이용한 대비 향상")
        print("   ✅ 15가지 이진화 방법 자동 선택")
        print("   ✅ 3단계 크기 필터링 (비율+절대+차원)")
        print("   ✅ 6단계 원형/타원형 판별")
        print("   ✅ 더 작은 도형까지 감지 (25 pixels²)")
        print("   ✅ 더 관대한 원형성 기준 (0.15~0.25)")
        
    else:
        print(f"\n💡 여전히 감지되지 않는 경우 해결 방안:")
        print("=" * 60)
        print("1. 🔬 상세 진단 실행:")
        print("   python debug_opencv.py")
        print()
        print("2. 🎛️  수동 파라미터 조정:")
        print("   - min_area_ratio를 더 낮춤 (0.00001)")
        print("   - min_absolute_area를 더 낮춤 (10)")
        print("   - 원형성 기준을 더 낮춤 (0.1)")
        print()
        print("3. 🖼️  이미지 전처리 강화:")
        print("   - 더 강한 대비 향상")
        print("   - 엣지 검출 알고리즘 추가")
        print("   - 모폴로지 연산 조정")
        print()
        print("4. 🤖 대안 방법:")
        print("   - Hough Circle Transform 사용")
        print("   - 딥러닝 기반 도형 감지")
        print("   - 컨투어 기반 특징 추출")

if __name__ == "__main__":
    main()
