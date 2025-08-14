#!/usr/bin/env python3
"""
파라미터 조정 도구 - 너무 작은 분할 문제 해결
"""

import os
import sys
sys.path.append('src')

def apply_larger_segmentation():
    """더 큰 영역 감지를 위한 파라미터 적용"""
    print("🔧 더 큰 영역 감지 파라미터 적용")
    print("=" * 60)
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return
        
        # 조정된 파라미터로 감지기 생성
        detector = HybridShapeDetector()
        
        # 더 큰 영역만 감지하도록 조정
        detector.min_area_ratio = 0.001      # 0.0001 → 0.001 (10배 증가)
        detector.min_absolute_area = 1000    # 50 → 1000 (20배 증가)
        detector.max_area_ratio = 0.3        # 0.4 → 0.3 (약간 감소)
        
        detector.set_debug_mode(True)
        
        print(f"📊 조정된 파라미터:")
        print(f"   min_area_ratio: {detector.min_area_ratio} ({detector.min_area_ratio*100:.2f}%)")
        print(f"   min_absolute_area: {detector.min_absolute_area} pixels²")
        print(f"   max_area_ratio: {detector.max_area_ratio} ({detector.max_area_ratio*100:.1f}%)")
        
        print(f"\n🔍 더 큰 영역만 감지 시도...")
        shapes = detector.detect_hand_drawn_shapes(test_image)
        
        print(f"\n📊 결과:")
        print(f"   감지된 원형/타원형: {len(shapes)}개")
        
        if len(shapes) > 0:
            print(f"\n✅ 더 큰 영역 감지 성공!")
            
            # 상세 정보
            for i, shape in enumerate(shapes):
                print(f"   {i+1:2d}. {shape.shape_type:15s} - {shape.w:4d}×{shape.h:4d} pixels - 면적: {shape.area():8,} px²")
            
            # 디버그 이미지 생성
            os.makedirs("output", exist_ok=True)
            debug_path = "output/larger_segments.png"
            detector.create_debug_image(test_image, shapes, debug_path)
            
            print(f"\n💾 결과 이미지: {debug_path}")
            return True
        else:
            print(f"\n⚠️  여전히 영역이 감지되지 않음")
            print(f"   더 극단적인 조정이 필요할 수 있습니다")
            return False
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def test_extreme_parameters():
    """극단적인 파라미터로 테스트"""
    print(f"\n🚀 극단적 파라미터 테스트")
    print("=" * 60)
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        
        test_image = "input/17301.png"
        
        # 매우 관대한 설정
        detector = HybridShapeDetector()
        detector.min_area_ratio = 0.005      # 0.5%
        detector.min_absolute_area = 2000    # 2000px² (약 45×45)
        detector.max_area_ratio = 0.2        # 20%
        detector.set_debug_mode(False)
        
        print(f"극단적 설정:")
        print(f"   min_area_ratio: {detector.min_area_ratio} ({detector.min_area_ratio*100:.1f}%)")
        print(f"   min_absolute_area: {detector.min_absolute_area} pixels²")
        
        shapes = detector.detect_hand_drawn_shapes(test_image)
        
        print(f"결과: {len(shapes)}개 원형/타원형")
        
        if len(shapes) > 0:
            # 큰 영역들만 표시
            os.makedirs("output", exist_ok=True)
            debug_path = "output/extreme_large_segments.png"
            detector.create_debug_image(test_image, shapes, debug_path)
            print(f"극단적 결과 저장: {debug_path}")
        
        return len(shapes)
        
    except Exception as e:
        print(f"❌ 극단적 테스트 실패: {e}")
        return 0

def main():
    """메인 실행 함수"""
    print("⚙️  파라미터 조정 도구")
    print("🎯 목표: 너무 작은 분할 문제 해결")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    # 1단계: 일반 조정
    success = apply_larger_segmentation()
    
    # 2단계: 극단적 조정 (일반 조정이 실패한 경우)
    if not success:
        print(f"\n🔄 극단적 파라미터로 재시도...")
        extreme_count = test_extreme_parameters()
        
        if extreme_count > 0:
            print(f"✅ 극단적 설정으로 {extreme_count}개 감지됨")
        else:
            print(f"❌ 극단적 설정으로도 감지 실패")
    
    print(f"\n" + "=" * 60)
    print("💡 파라미터 조정 완료!")
    print()
    print("🔍 추천 워크플로우:")
    print("   1. visualize_segmentation.py 실행으로 문제 진단")
    print("   2. 이 스크립트로 파라미터 조정")
    print("   3. main.py에서 하이브리드 모드 사용")
    print()
    print("📁 생성된 파일들:")
    print("   output/larger_segments.png - 조정 후 결과")
    print("   output/extreme_large_segments.png - 극단적 조정 결과")

if __name__ == "__main__":
    main()
