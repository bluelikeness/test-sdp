#!/usr/bin/env python3
"""
개선된 하이브리드 시스템 테스트
수기 도형 내 텍스트 인식 최적화 검증
"""

import os
import sys

# src 디렉토리를 경로에 추가
sys.path.append('src')

def test_improved_hybrid():
    """개선된 하이브리드 시스템 테스트"""
    print("🎯 개선된 하이브리드 시스템 테스트")
    print("=" * 60)
    print("📋 개선사항:")
    print("  - 수기 도형 특화 프롬프트")
    print("  - 확장된 도형 크기 감지 범위")
    print("  - 향상된 마진 처리")
    print("  - 다중 epsilon 도형 분석")
    print("=" * 60)
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        from cloud_ocr import CloudOCRProcessor
        from dotenv import load_dotenv
        
        # 환경변수 로드
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("❌ API 키가 설정되지 않음")
            return False
        
        # 테스트 이미지 경로
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return False
        
        print(f"📸 테스트 이미지: {test_image}")
        
        # 1단계: 개선된 도형 감지 테스트
        print("\n🔍 1단계: 개선된 도형 감지 테스트")
        detector = HybridShapeDetector()
        detector.set_debug_mode(True)
        
        shapes = detector.detect_hand_drawn_shapes(test_image)
        print(f"✅ 감지된 도형 수: {len(shapes)}개")
        
        if len(shapes) == 0:
            print("⚠️  도형이 감지되지 않음")
            return False
        
        # 도형별 상세 정보
        for i, shape in enumerate(shapes):
            print(f"  도형 {i+1}: {shape.shape_type}, 크기: {shape.w}x{shape.h}")
        
        # 디버그 이미지 생성
        os.makedirs("output", exist_ok=True)
        debug_path = "output/improved_debug_shapes.png"
        detector.create_debug_image(test_image, shapes, debug_path)
        
        # 2단계: 하이브리드 OCR 테스트
        print(f"\n🤖 2단계: 개선된 하이브리드 OCR 테스트")
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        processor.set_ocr_mode("hybrid")
        
        result_text = processor.process_image_hybrid(test_image)
        
        if result_text and not result_text.startswith("처리 실패"):
            print(f"✅ 텍스트 추출 성공!")
            print(f"📝 추출된 텍스트 길이: {len(result_text)}자")
            print(f"📄 추출된 텍스트 미리보기:")
            print("-" * 40)
            
            # 텍스트를 줄별로 출력 (최대 10줄)
            lines = result_text.strip().split('\n')
            for i, line in enumerate(lines[:10]):
                if line.strip():
                    print(f"  {i+1:2d}: {line.strip()}")
            
            if len(lines) > 10:
                print(f"  ... (총 {len(lines)}줄)")
            
            print("-" * 40)
            
            # 결과 저장
            result_path = "output/improved_hybrid_result.txt"
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write("=== 개선된 하이브리드 시스템 결과 ===\n")
                f.write(f"감지된 도형 수: {len(shapes)}개\n")
                f.write(f"추출된 텍스트 길이: {len(result_text)}자\n")
                f.write(f"처리 모드: hybrid (수기 도형 최적화)\n\n")
                f.write("=== 추출된 텍스트 ===\n")
                f.write(result_text)
            
            print(f"💾 결과 저장: {result_path}")
            return True
            
        else:
            print(f"❌ 텍스트 추출 실패: {result_text}")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_previous():
    """이전 버전과 비교 테스트"""
    print("\n📊 이전 버전과 성능 비교")
    print("=" * 60)
    
    # 이전 결과가 있다면 비교
    previous_result_path = "output/cloud_qwen-vl-plus/17301.txt"
    current_result_path = "output/improved_hybrid_result.txt"
    
    if os.path.exists(previous_result_path) and os.path.exists(current_result_path):
        with open(previous_result_path, 'r', encoding='utf-8') as f:
            previous_text = f.read()
        
        with open(current_result_path, 'r', encoding='utf-8') as f:
            current_text = f.read()
        
        # 텍스트 길이 비교
        prev_length = len(previous_text.strip())
        curr_length = len(current_text.strip().split("=== 추출된 텍스트 ===")[-1])
        
        print(f"이전 결과: {prev_length}자")
        print(f"개선 결과: {curr_length}자")
        
        if curr_length > prev_length:
            improvement = ((curr_length - prev_length) / prev_length) * 100
            print(f"🎉 개선: +{improvement:.1f}% 더 많은 텍스트 추출!")
        elif curr_length == prev_length:
            print("📊 동일: 비슷한 양의 텍스트 추출")
        else:
            print("⚠️  참고: 텍스트 양은 줄었지만 정확도가 향상될 수 있음")
    else:
        print("이전 결과 파일이 없어 비교할 수 없습니다.")

def main():
    """메인 실행 함수"""
    print("🚀 개선된 하이브리드 시스템 종합 테스트")
    print("🎯 목표: 수기 도형 내 텍스트 인식 정확도 향상")
    print("=" * 60)
    
    # 현재 디렉토리 확인 및 이동
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    success = test_improved_hybrid()
    
    if success:
        compare_with_previous()
        
        print("\n" + "=" * 60)
        print("🎉 개선된 하이브리드 시스템 테스트 완료!")
        print("✨ 주요 개선사항:")
        print("   - 수기 도형 특화 프롬프트 적용")
        print("   - 더 넓은 도형 크기 범위 감지")
        print("   - 향상된 영역 마진 처리")
        print("   - 다중 epsilon 분석으로 정확도 향상")
        print("\n🎯 기대 효과:")
        print("   - 기존 7/12 → 목표 10-12/12 도형 인식")
        print("   - 더 정확한 수기 텍스트 추출")
        print("   - 불완전한 도형도 안정적 감지")
    else:
        print("\n❌ 테스트 실패. 설정을 확인해주세요.")

if __name__ == "__main__":
    main()
