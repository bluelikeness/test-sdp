#!/usr/bin/env python3
"""
OpenCV 도형 감지 문제 진단 및 디버깅
"""

import os
import sys
sys.path.append('src')

def diagnose_opencv_detection():
    """OpenCV 도형 감지 문제 진단"""
    print("🔍 OpenCV 도형 감지 문제 진단")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
        from hybrid_shape_detector import HybridShapeDetector
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return False
        
        print(f"📸 분석 이미지: {test_image}")
        
        # 이미지 로드 및 기본 정보
        original = cv2.imread(test_image)
        if original is None:
            print("❌ 이미지 로드 실패")
            return False
        
        height, width = original.shape[:2]
        print(f"📏 이미지 크기: {width} × {height} pixels")
        print(f"📦 이미지 면적: {width * height:,} pixels²")
        
        # 단계별 전처리 과정 분석
        print(f"\n🔬 단계별 전처리 분석:")
        
        # 1. 그레이스케일 변환
        gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        print(f"   1️⃣ 그레이스케일 변환 완료")
        
        # 2. 여러 이진화 방법 시도
        print(f"   2️⃣ 이진화 방법별 결과:")
        
        # Adaptive threshold
        binary1 = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        contours1, _ = cv2.findContours(binary1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"      - Adaptive Threshold: {len(contours1)}개 윤곽선")
        
        # Otsu threshold
        _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours2, _ = cv2.findContours(binary2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"      - Otsu Threshold: {len(contours2)}개 윤곽선")
        
        # Custom threshold
        _, binary3 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        contours3, _ = cv2.findContours(binary3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"      - Custom Threshold (127): {len(contours3)}개 윤곽선")
        
        # 더 관대한 threshold 시도
        _, binary4 = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
        contours4, _ = cv2.findContours(binary4, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"      - Custom Threshold (100): {len(contours4)}개 윤곽선")
        
        _, binary5 = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
        contours5, _ = cv2.findContours(binary5, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"      - Custom Threshold (80): {len(contours5)}개 윤곽선")
        
        # 가장 많은 윤곽선을 찾은 방법 선택
        all_results = [
            ("Adaptive", binary1, contours1),
            ("Otsu", binary2, contours2), 
            ("Custom_127", binary3, contours3),
            ("Custom_100", binary4, contours4),
            ("Custom_80", binary5, contours5)
        ]
        
        best_method, best_binary, best_contours = max(all_results, key=lambda x: len(x[2]))
        print(f"   ✅ 최적 방법: {best_method} ({len(best_contours)}개 윤곽선)")
        
        # 3. 크기 필터링 분석
        print(f"\n   3️⃣ 크기 필터링 분석:")
        detector = HybridShapeDetector()
        
        # 현재 필터링 기준
        min_area = detector.min_area_ratio * width * height
        max_area = detector.max_area_ratio * width * height
        print(f"      현재 면적 범위: {min_area:.0f} ~ {max_area:.0f} pixels²")
        print(f"      현재 비율 범위: {detector.min_area_ratio*100:.3f}% ~ {detector.max_area_ratio*100:.1f}%")
        
        valid_count = 0
        area_distribution = []
        
        for contour in best_contours:
            area = cv2.contourArea(contour)
            area_distribution.append(area)
            if detector._is_valid_contour_size(contour, width, height):
                valid_count += 1
        
        print(f"      크기 조건 만족: {valid_count}개")
        
        if area_distribution:
            area_distribution.sort()
            print(f"      윤곽선 면적 분포:")
            print(f"        최소: {min(area_distribution):.0f} pixels²")
            print(f"        최대: {max(area_distribution):.0f} pixels²")
            print(f"        중앙값: {area_distribution[len(area_distribution)//2]:.0f} pixels²")
            
            # 상위 10개 면적 표시
            print(f"        상위 10개 면적:")
            for i, area in enumerate(sorted(area_distribution, reverse=True)[:10]):
                ratio = (area / (width * height)) * 100
                print(f"          {i+1:2d}. {area:8.0f} pixels² ({ratio:.3f}%)")
        
        # 디버그 이미지들 저장
        os.makedirs("output", exist_ok=True)
        
        # 원본과 이진화 이미지들 저장
        cv2.imwrite("output/debug_0_original.png", original)
        cv2.imwrite("output/debug_1_gray.png", gray)
        cv2.imwrite("output/debug_2_adaptive.png", binary1)
        cv2.imwrite("output/debug_3_otsu.png", binary2)
        cv2.imwrite("output/debug_4_custom127.png", binary3)
        cv2.imwrite("output/debug_5_custom100.png", binary4)
        cv2.imwrite("output/debug_6_custom80.png", binary5)
        
        # 윤곽선 그린 이미지 저장
        contour_image = original.copy()
        cv2.drawContours(contour_image, best_contours, -1, (0, 255, 0), 2)
        cv2.imwrite("output/debug_7_all_contours.png", contour_image)
        
        print(f"\n💾 디버그 이미지 저장 완료:")
        print(f"   - output/debug_0_original.png (원본)")
        print(f"   - output/debug_1_gray.png (그레이스케일)")
        print(f"   - output/debug_2_adaptive.png (Adaptive 이진화)")
        print(f"   - output/debug_3_otsu.png (Otsu 이진화)")
        print(f"   - output/debug_4_custom127.png (Custom 127)")
        print(f"   - output/debug_5_custom100.png (Custom 100)")
        print(f"   - output/debug_6_custom80.png (Custom 80)")
        print(f"   - output/debug_7_all_contours.png (모든 윤곽선)")
        
        return len(best_contours) > 0, best_method, len(best_contours), valid_count
        
    except Exception as e:
        print(f"❌ 진단 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, None, 0, 0

def suggest_improvements(has_contours, best_method, total_contours, valid_contours):
    """개선 방안 제안"""
    print(f"\n💡 개선 방안 제안:")
    print("=" * 60)
    
    if not has_contours:
        print("🔥 심각: 윤곽선이 전혀 감지되지 않음")
        print("   해결 방안:")
        print("   1. 이미지 전처리 강화 필요")
        print("   2. 더 관대한 threshold 값 사용")
        print("   3. 블러링/노이즈 제거 추가")
        print("   4. 엣지 감지 알고리즘 병용")
    
    elif valid_contours == 0:
        print("⚠️  윤곽선은 있지만 크기 필터에서 모두 제외됨")
        print("   해결 방안:")
        print("   1. min_area_ratio 축소 (현재 0.0005 → 0.0001)")
        print("   2. max_area_ratio 확대 (현재 0.25 → 0.5)")
        print("   3. 절대 크기 기준 추가")
    
    elif valid_contours < 5:
        print("📈 일부 윤곽선만 통과. 추가 개선 가능")
        print("   개선 방안:")
        print("   1. 필터링 기준 미세 조정")
        print("   2. 복수 방법 조합 사용")
        print("   3. 후처리 최적화")
    
    else:
        print("✅ 적절한 수의 윤곽선 감지됨")
        print("   최적화 방안:")
        print("   1. 도형 분석 정확도 향상")
        print("   2. 원형/타원형 판별 기준 조정")

def main():
    """메인 실행 함수"""
    print("🔬 OpenCV 도형 감지 문제 진단 도구")
    print("🎯 목표: 감지 실패 원인 파악 및 해결책 제시")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    # 진단 실행
    has_contours, best_method, total_contours, valid_contours = diagnose_opencv_detection()
    
    if has_contours is not False:
        # 개선 방안 제안
        suggest_improvements(has_contours, best_method, total_contours, valid_contours)
        
        print(f"\n📊 진단 결과 요약:")
        print(f"   최적 이진화 방법: {best_method}")
        print(f"   총 윤곽선 수: {total_contours}개")
        print(f"   크기 조건 통과: {valid_contours}개")
        
        if valid_contours > 0:
            print(f"\n🔧 다음 단계: 도형 분석 및 원형/타원형 필터링 개선")
        else:
            print(f"\n🔧 다음 단계: 크기 필터링 기준 완화 필요")
    
    print(f"\n📁 디버그 이미지를 확인해서 어떤 부분에서 문제가 있는지 살펴보세요!")

if __name__ == "__main__":
    main()
