#!/usr/bin/env python3
"""
영역 분할 시각화 도구
OpenCV가 어떻게 영역을 분리하는지 단계별로 확인
"""

import os
import sys
sys.path.append('src')

def visualize_segmentation_process():
    """영역 분할 과정을 단계별로 시각화"""
    print("👁️  영역 분할 시각화 도구")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
        from hybrid_shape_detector import HybridShapeDetector
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return
        
        print(f"📸 분석 이미지: {test_image}")
        
        # 원본 이미지 로드
        original = cv2.imread(test_image)
        height, width = original.shape[:2]
        
        print(f"📏 이미지 크기: {width} × {height} pixels")
        print(f"📦 총 면적: {width * height:,} pixels²")
        
        # 단계별 처리 시각화
        detector = HybridShapeDetector()
        detector.set_debug_mode(True)
        
        print(f"\n🔬 단계별 전처리 과정:")
        
        # 1단계: 전처리 결과 저장
        original_processed, enhanced, binary_clean = detector.preprocess_image(test_image)
        
        # 2단계: 모든 윤곽선 찾기
        contours, _ = cv2.findContours(binary_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"   📊 전체 윤곽선 개수: {len(contours)}개")
        
        # 3단계: 크기별 분류
        small_contours = []
        medium_contours = []
        large_contours = []
        valid_contours = []
        
        for contour in contours:
            try:
                area = cv2.contourArea(contour)
                if area > 0:
                    # 크기별 분류
                    if area < 500:
                        small_contours.append(contour)
                    elif area < 5000:
                        medium_contours.append(contour)
                    else:
                        large_contours.append(contour)
                    
                    # 유효성 검사
                    if detector._is_valid_contour_size(contour, width, height):
                        valid_contours.append(contour)
            except:
                continue
        
        print(f"   📊 크기별 분류:")
        print(f"      작은 영역 (< 500px²): {len(small_contours)}개")
        print(f"      중간 영역 (500-5000px²): {len(medium_contours)}개") 
        print(f"      큰 영역 (> 5000px²): {len(large_contours)}개")
        print(f"      유효 영역: {len(valid_contours)}개")
        
        # 시각화 이미지들 생성
        os.makedirs("output", exist_ok=True)
        
        # 1. 원본 이미지
        cv2.imwrite("output/step1_original.png", original)
        
        # 2. 전처리된 이미지
        cv2.imwrite("output/step2_enhanced.png", enhanced)
        
        # 3. 이진화 이미지
        cv2.imwrite("output/step3_binary.png", binary_clean)
        
        # 4. 모든 윤곽선 표시
        all_contours_img = original.copy()
        cv2.drawContours(all_contours_img, contours, -1, (0, 255, 0), 1)
        cv2.putText(all_contours_img, f"All Contours: {len(contours)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imwrite("output/step4_all_contours.png", all_contours_img)
        
        # 5. 크기별 윤곽선 표시
        size_classified_img = original.copy()
        cv2.drawContours(size_classified_img, small_contours, -1, (0, 0, 255), 1)  # 빨강: 작은 것
        cv2.drawContours(size_classified_img, medium_contours, -1, (0, 255, 255), 2)  # 노랑: 중간
        cv2.drawContours(size_classified_img, large_contours, -1, (0, 255, 0), 3)  # 초록: 큰 것
        
        # 범례 추가
        cv2.putText(size_classified_img, "Red: Small (<500px2)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(size_classified_img, "Yellow: Medium (500-5000px2)", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(size_classified_img, "Green: Large (>5000px2)", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imwrite("output/step5_size_classified.png", size_classified_img)
        
        # 6. 유효한 윤곽선만 표시
        valid_contours_img = original.copy()
        cv2.drawContours(valid_contours_img, valid_contours, -1, (255, 0, 0), 2)
        cv2.putText(valid_contours_img, f"Valid Contours: {len(valid_contours)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.imwrite("output/step6_valid_contours.png", valid_contours_img)
        
        # 7. 바운딩 박스와 번호 표시
        bbox_img = original.copy()
        for i, contour in enumerate(valid_contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # 바운딩 박스 그리기
            cv2.rectangle(bbox_img, (x, y), (x + w, y + h), (255, 0, 255), 2)
            
            # 번호와 면적 표시
            cv2.putText(bbox_img, f"{i+1}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            cv2.putText(bbox_img, f"{area:.0f}px2", (x, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
        
        cv2.imwrite("output/step7_bounding_boxes.png", bbox_img)
        
        # 8. 도형 분석 및 원형/타원형 필터링
        shapes = detector.detect_hand_drawn_shapes(test_image)
        
        circle_ellipse_img = original.copy()
        for i, shape in enumerate(shapes):
            color = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)][i % 5]
            
            # 영역 표시
            cv2.rectangle(circle_ellipse_img, (shape.x, shape.y), 
                         (shape.x + shape.w, shape.y + shape.h), color, 3)
            
            # 정보 표시
            cv2.putText(circle_ellipse_img, f"{i+1}: {shape.shape_type}", 
                       (shape.x, shape.y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        cv2.putText(circle_ellipse_img, f"Circle/Ellipse: {len(shapes)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imwrite("output/step8_final_shapes.png", circle_ellipse_img)
        
        # 결과 요약
        print(f"\n📊 분할 결과 요약:")
        print(f"   전체 윤곽선: {len(contours)}개")
        print(f"   유효 윤곽선: {len(valid_contours)}개") 
        print(f"   원형/타원형: {len(shapes)}개")
        
        print(f"\n💾 시각화 이미지 저장 완료:")
        print(f"   step1_original.png - 원본 이미지")
        print(f"   step2_enhanced.png - 전처리된 이미지")
        print(f"   step3_binary.png - 이진화 이미지")
        print(f"   step4_all_contours.png - 모든 윤곽선")
        print(f"   step5_size_classified.png - 크기별 분류")
        print(f"   step6_valid_contours.png - 유효한 윤곽선")
        print(f"   step7_bounding_boxes.png - 바운딩 박스")
        print(f"   step8_final_shapes.png - 최종 원형/타원형")
        
        # 상세 분석
        print(f"\n🔍 상세 분석:")
        if len(shapes) > 0:
            print(f"   감지된 원형/타원형:")
            for i, shape in enumerate(shapes):
                print(f"   {i+1:2d}. {shape.shape_type:12s} - {shape.w:4d}×{shape.h:4d} pixels - 면적: {shape.area():8,} px²")
        else:
            print(f"   ⚠️  원형/타원형이 감지되지 않음")
            print(f"   가능한 원인:")
            print(f"   - 도형이 너무 작게 분할됨")
            print(f"   - 원형성 기준이 너무 엄격함")
            print(f"   - 이진화가 부적절함")
        
        return len(shapes) > 0
        
    except Exception as e:
        print(f"❌ 시각화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_size_thresholds():
    """크기 임계값 분석"""
    print(f"\n📏 크기 임계값 분석")
    print("=" * 60)
    
    try:
        from hybrid_shape_detector import HybridShapeDetector
        import cv2
        
        test_image = "input/17301.png"
        original = cv2.imread(test_image)
        height, width = original.shape[:2]
        
        detector = HybridShapeDetector()
        
        print(f"현재 설정:")
        print(f"   min_area_ratio: {detector.min_area_ratio} ({detector.min_area_ratio*100:.4f}%)")
        print(f"   max_area_ratio: {detector.max_area_ratio} ({detector.max_area_ratio*100:.1f}%)")
        print(f"   min_absolute_area: {detector.min_absolute_area} pixels²")
        
        total_area = width * height
        min_area = detector.min_area_ratio * total_area
        max_area = detector.max_area_ratio * total_area
        
        print(f"\n절대값 변환:")
        print(f"   최소 면적: {min_area:.0f} pixels² ({detector.min_area_ratio*100:.4f}%)")
        print(f"   최대 면적: {max_area:.0f} pixels² ({detector.max_area_ratio*100:.1f}%)")
        print(f"   절대 최소: {detector.min_absolute_area} pixels²")
        
        # 추천 설정
        print(f"\n💡 추천 설정 (더 큰 영역 감지):")
        print(f"   min_area_ratio: 0.001 (0.1%) = {total_area * 0.001:.0f} pixels²")
        print(f"   min_absolute_area: 1000 pixels² (약 32×32 크기)")
        print(f"   max_area_ratio: 0.3 (30%) = {total_area * 0.3:.0f} pixels²")
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")

def suggest_parameter_adjustments():
    """파라미터 조정 제안"""
    print(f"\n🎛️  파라미터 조정 제안")
    print("=" * 60)
    
    print("너무 작게 분할되는 문제 해결 방안:")
    print()
    print("1. 🔧 최소 크기 증가:")
    print("   min_area_ratio: 0.0001 → 0.001 (10배 증가)")
    print("   min_absolute_area: 50 → 1000 (20배 증가)")
    print()
    print("2. 🧹 노이즈 제거 강화:")
    print("   - 모폴로지 연산 iterations 증가")
    print("   - 가우시안 블러 커널 크기 증가")
    print()
    print("3. 🎯 이진화 방법 조정:")
    print("   - 더 보수적인 threshold 값 사용")
    print("   - Adaptive threshold 블록 크기 증가")
    print()
    print("4. 🔗 윤곽선 병합:")
    print("   - 가까운 윤곽선들을 하나로 병합")
    print("   - 계층적 윤곽선 사용 (RETR_TREE)")

def main():
    """메인 실행 함수"""
    print("👁️  영역 분할 시각화 및 분석 도구")
    print("🎯 목표: OpenCV가 영역을 어떻게 분리하는지 확인")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    # 시각화 실행
    success = visualize_segmentation_process()
    
    # 분석 및 제안
    analyze_size_thresholds()
    suggest_parameter_adjustments()
    
    print(f"\n" + "=" * 60)
    if success:
        print("✅ 영역 분할 시각화 완료!")
        print("📁 output 폴더의 step*.png 파일들을 확인하세요")
        print()
        print("🔍 단계별 이미지 분석:")
        print("   step4_all_contours.png - 전체 윤곽선 (너무 많다면 노이즈)")
        print("   step5_size_classified.png - 크기별 분류 (빨강이 너무 많다면 문제)")
        print("   step6_valid_contours.png - 유효한 윤곽선 (최종 후보)")
        print("   step8_final_shapes.png - 원형/타원형만 (최종 결과)")
    else:
        print("⚠️  영역 분할 문제 발견!")
        print("💡 해결책:")
        print("   1. step*.png 이미지들을 확인")
        print("   2. 파라미터 조정 적용")
        print("   3. 이진화 방법 변경")

if __name__ == "__main__":
    main()
