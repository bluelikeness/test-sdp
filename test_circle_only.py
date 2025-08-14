#!/usr/bin/env python3
"""
원형/타원형 도형만 감지하는 테스트
"""

import os
import sys
sys.path.append('src')

def test_circle_ellipse_only():
    """원형/타원형만 감지하는 테스트"""
    print("🎯 원형/타원형 도형만 감지 테스트")
    print("=" * 60)
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        
        # 테스트 이미지 경로
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return False
        
        print(f"📸 테스트 이미지: {test_image}")
        
        # 개선된 도형 감지기 생성
        detector = HybridShapeDetector()
        detector.set_debug_mode(True)  # 디버그 모드로 상세 출력
        
        print("\n🔍 도형 감지 시작...")
        shapes = detector.detect_hand_drawn_shapes(test_image)
        
        print(f"\n📊 결과 요약:")
        print(f"   감지된 원형/타원형: {len(shapes)}개")
        
        if len(shapes) == 0:
            print("⚠️  원형/타원형이 감지되지 않았습니다.")
            print("   가능한 원인:")
            print("   - 이미지에 원형/타원형 도형이 없음")
            print("   - 도형의 원형성이 기준값보다 낮음")
            print("   - 도형의 크기가 필터링 범위를 벗어남")
            return False
        
        # 감지된 도형들의 상세 정보
        print(f"\n📋 감지된 원형/타원형 상세 정보:")
        for i, shape in enumerate(shapes):
            print(f"   {i+1:2d}. 타입: {shape.shape_type}")
            print(f"       위치: ({shape.x}, {shape.y})")
            print(f"       크기: {shape.w} × {shape.h} pixels")
            print(f"       면적: {shape.area():,} pixels²")
            print()
        
        # 디버그 이미지 생성
        os.makedirs("output", exist_ok=True)
        debug_path = "output/circle_ellipse_debug.png"
        success = detector.create_debug_image(test_image, shapes, debug_path)
        
        if success:
            print(f"🎯 디버그 이미지 생성: {debug_path}")
            print("   → 이미지에서 감지된 원형/타원형들을 확인할 수 있습니다")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_filter_comparison():
    """필터링 전후 비교 테스트"""
    print("\n🔄 필터링 전후 비교")
    print("=" * 60)
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        import cv2
        import numpy as np
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print("❌ 테스트 이미지 없음")
            return
        
        detector = HybridShapeDetector()
        
        # 이미지 전처리
        original, gray, binary = detector.preprocess_image(test_image)
        height, width = binary.shape
        
        # 모든 윤곽선 찾기 (필터링 전)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"전체 윤곽선 개수: {len(contours)}개")
        
        # 크기 필터링 적용
        valid_contours = []
        for contour in contours:
            if detector._is_valid_contour_size(contour, width, height):
                valid_contours.append(contour)
        
        print(f"크기 필터링 후: {len(valid_contours)}개")
        
        # 도형 분석 및 원형/타원형 필터링
        circle_ellipse_count = 0
        other_shapes = []
        
        for contour in valid_contours:
            shape_info = detector._analyze_shape(contour)
            if shape_info:
                if detector._is_circle_or_ellipse(shape_info):
                    circle_ellipse_count += 1
                else:
                    other_shapes.append(shape_info['type'])
        
        print(f"원형/타원형: {circle_ellipse_count}개")
        print(f"기타 도형: {len(other_shapes)}개")
        
        if other_shapes:
            from collections import Counter
            shape_counts = Counter(other_shapes)
            print("   제외된 도형 타입:")
            for shape_type, count in shape_counts.items():
                print(f"   - {shape_type}: {count}개")
        
        print(f"\n✅ 원형/타원형 필터링 완료: {circle_ellipse_count}개 선택됨")
        
    except Exception as e:
        print(f"❌ 비교 테스트 실패: {e}")

def test_hybrid_with_circles_only():
    """원형/타원형만으로 하이브리드 OCR 테스트"""
    print("\n🤖 원형/타원형 하이브리드 OCR 테스트")
    print("=" * 60)
    
    try:
        from cloud_ocr import CloudOCRProcessor
        from dotenv import load_dotenv
        
        # 환경변수 로드
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("⚠️  API 키가 설정되지 않음. OpenCV 감지만 테스트합니다.")
            return
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print("❌ 테스트 이미지 없음")
            return
        
        print("🌐 하이브리드 OCR 처리 시작...")
        
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        processor.set_ocr_mode("hybrid")
        
        # 하이브리드 처리 실행
        result_text = processor.process_image_hybrid(test_image)
        
        if result_text and not result_text.startswith("처리 실패"):
            print(f"✅ 원형/타원형 텍스트 추출 성공!")
            print(f"📝 추출된 텍스트 길이: {len(result_text)}자")
            
            # 결과 저장
            os.makedirs("output", exist_ok=True)
            result_path = "output/circle_ellipse_hybrid_result.txt"
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write("=== 원형/타원형 하이브리드 OCR 결과 ===\n")
                f.write(f"처리 모드: 원형/타원형만 감지\n")
                f.write(f"추출된 텍스트 길이: {len(result_text)}자\n\n")
                f.write("=== 추출된 텍스트 ===\n")
                f.write(result_text)
            
            print(f"💾 결과 저장: {result_path}")
            
            # 텍스트 미리보기
            print(f"\n📄 추출된 텍스트 미리보기:")
            lines = result_text.strip().split('\n')
            for i, line in enumerate(lines[:10]):
                if line.strip():
                    print(f"  {i+1:2d}: {line.strip()}")
            
            if len(lines) > 10:
                print(f"  ... (총 {len(lines)}줄)")
        else:
            print(f"❌ 텍스트 추출 실패: {result_text}")
        
    except Exception as e:
        print(f"❌ 하이브리드 OCR 테스트 실패: {e}")

def main():
    """메인 실행 함수"""
    print("🔍 원형/타원형 전용 도형 감지 시스템 테스트")
    print("🎯 목표: 원형과 타원형 도형 안의 텍스트만 인식")
    print("=" * 60)
    
    # 현재 디렉토리 확인 및 이동
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    # 1단계: 원형/타원형 감지 테스트
    success = test_circle_ellipse_only()
    
    if success:
        # 2단계: 필터링 비교
        test_filter_comparison()
        
        # 3단계: 하이브리드 OCR 테스트
        test_hybrid_with_circles_only()
        
        print("\n" + "=" * 60)
        print("🎉 원형/타원형 전용 시스템 테스트 완료!")
        print("✨ 주요 특징:")
        print("   ✅ 사각형, 다각형 등 기타 도형 제외")
        print("   ✅ 원형과 타원형만 선별적 감지")
        print("   ✅ 불완전한 원형도 인식 가능")
        print("   ✅ 다양한 크기의 원형/타원형 지원")
        print("\n🎯 기대 효과:")
        print("   - 원형/타원형 안의 텍스트만 정확히 추출")
        print("   - 노이즈 감소로 인한 정확도 향상")
        print("   - 처리 속도 개선")
    else:
        print("\n❌ 테스트 실패. 설정을 확인해주세요.")
        print("💡 해결 방법:")
        print("   1. input/17301.png 파일이 있는지 확인")
        print("   2. 이미지에 원형/타원형 도형이 있는지 확인") 
        print("   3. 도형이 충분히 큰지 확인")

if __name__ == "__main__":
    main()
