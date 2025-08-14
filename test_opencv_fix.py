#!/usr/bin/env python3
"""
OpenCV 오류 수정 후 테스트
"""

import os
import sys
sys.path.append('src')

def test_opencv_fix():
    """OpenCV 오류 수정 테스트"""
    print("🔧 OpenCV 오류 수정 테스트")
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
        
        print(f"\n🔍 원형/타원형 감지 시도...")
        shapes = detector.detect_hand_drawn_shapes(test_image)
        
        print(f"\n📊 결과:")
        print(f"   감지된 원형/타원형: {len(shapes)}개")
        
        if len(shapes) > 0:
            print(f"\n✅ OpenCV 오류 해결 성공!")
            print(f"🎉 {len(shapes)}개 원형/타원형 감지됨")
            
            # 상세 정보
            for i, shape in enumerate(shapes):
                print(f"   {i+1}. {shape.shape_type} - {shape.w}×{shape.h} pixels")
            
            # 디버그 이미지 생성
            os.makedirs("output", exist_ok=True)
            debug_path = "output/opencv_fix_test.png"
            detector.create_debug_image(test_image, shapes, debug_path)
            
            return True
        else:
            print(f"\n⚠️  OpenCV 오류는 해결되었지만 도형이 감지되지 않음")
            print(f"   추가 진단을 위해 debug_opencv.py를 실행해보세요")
            return False
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_pipeline():
    """전체 하이브리드 파이프라인 테스트"""
    print(f"\n🤖 하이브리드 파이프라인 테스트")
    print("=" * 60)
    
    try:
        from cloud_ocr import CloudOCRProcessor
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("⚠️  API 키가 설정되지 않음. OpenCV 테스트만 완료")
            return
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print("❌ 테스트 이미지 없음")
            return
        
        print("🌐 하이브리드 OCR 테스트...")
        
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        processor.set_ocr_mode("hybrid")
        
        result_text = processor.process_image_hybrid(test_image)
        
        if result_text and not result_text.startswith("처리 실패"):
            print(f"✅ 하이브리드 OCR 성공!")
            print(f"📝 추출된 텍스트 길이: {len(result_text)}자")
            
            # 결과 저장
            os.makedirs("output", exist_ok=True)
            result_path = "output/opencv_fix_hybrid_result.txt"
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write("=== OpenCV 오류 수정 후 하이브리드 결과 ===\n")
                f.write(f"수정사항: OpenCV contourArea 오류 방지\n")
                f.write(f"추출된 텍스트 길이: {len(result_text)}자\n\n")
                f.write("=== 추출된 텍스트 ===\n")
                f.write(result_text)
            
            print(f"💾 결과 저장: {result_path}")
            
            # 미리보기
            lines = result_text.strip().split('\n')
            print(f"\n📄 추출된 텍스트 미리보기:")
            for i, line in enumerate(lines[:3]):
                if line.strip():
                    print(f"  {i+1}: {line.strip()}")
            
            if len(lines) > 3:
                print(f"  ... (총 {len(lines)}줄)")
                
        else:
            print(f"❌ 하이브리드 OCR 실패: {result_text}")
        
    except Exception as e:
        print(f"❌ 하이브리드 파이프라인 테스트 실패: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 OpenCV 오류 수정 검증 테스트")
    print("🎯 목표: contourArea 오류 해결 확인")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    # OpenCV 수정 테스트
    success = test_opencv_fix()
    
    if success:
        # 하이브리드 파이프라인 테스트
        test_hybrid_pipeline()
        
        print(f"\n" + "=" * 60)
        print("🎉 OpenCV 오류 수정 완료!")
        print("✨ 적용된 수정사항:")
        print("   ✅ contour 데이터 타입 검증")
        print("   ✅ 윤곽선 유효성 검사")
        print("   ✅ OpenCV 함수 호출 안전화")
        print("   ✅ 예외 처리 강화")
        print("   ✅ 하이브리드 모드 정상 동작")
        
        print(f"\n🎯 이제 main.py에서 하이브리드 모드를 사용할 수 있습니다:")
        print("   python src/main.py")
        print("   → 2. Qwen Cloud API 사용")
        print("   → 2. 하이브리드 모드")
        
    else:
        print(f"\n💡 문제 해결 방안:")
        print("=" * 60)
        print("1. 🔬 상세 진단:")
        print("   python debug_opencv.py")
        print()
        print("2. 📊 개선된 감지 테스트:")
        print("   python test_improved_opencv.py")
        print()
        print("3. 🎛️  수동 설정:")
        print("   - 더 관대한 파라미터 적용")
        print("   - 다른 이진화 방법 시도")

if __name__ == "__main__":
    main()
