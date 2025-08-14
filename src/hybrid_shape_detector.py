"""
하이브리드 도형 감지 및 텍스트 추출
OpenCV로 도형 위치 찾기 + AI로 텍스트 추출
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import json
from typing import List, Dict, Tuple, Optional
import tempfile

class ShapeRegion:
    """도형 영역 정보를 담는 클래스"""
    def __init__(self, x, y, w, h, contour=None, shape_type="unknown"):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.contour = contour
        self.shape_type = shape_type
        self.text = ""
        self.confidence = 0.0
        
    def get_bbox(self):
        """바운딩 박스 반환"""
        return (self.x, self.y, self.x + self.w, self.y + self.h)
    
    def get_center(self):
        """중심점 반환"""
        return (self.x + self.w // 2, self.y + self.y // 2)
    
    def area(self):
        """영역 크기 반환"""
        return self.w * self.h

class HybridShapeDetector:
    """OpenCV + AI 하이브리드 도형 감지기"""
    
    def __init__(self):
        self.debug_mode = False
        # 수기 도형 감지를 위한 더 관대한 크기 필터링
        self.min_area_ratio = 0.0001   # 전체 이미지의 0.01% (더 작은 도형까지)
        self.max_area_ratio = 0.4      # 전체 이미지의 40% (더 큰 도형까지)
        self.min_absolute_area = 50    # 절대 최소 면적 (pixels²)
        
    def set_debug_mode(self, debug=True):
        """디버그 모드 설정"""
        self.debug_mode = debug
        
    def preprocess_image(self, image_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """이미지 전처리 - 강화된 버전"""
        # 원본 이미지 로드
        original = cv2.imread(image_path)
        if original is None:
            raise ValueError(f"이미지 로드 실패: {image_path}")
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        # 노이즈 제거 및 대비 향상
        # 1. 가우시안 블러 적용
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization) 적용
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(blurred)
        
        # 여러 이진화 방법 시도 (더 많은 옵션)
        binaries = []
        
        # 1. Adaptive threshold (여러 변형)
        for block_size in [11, 15, 21]:
            for c_value in [2, 5, 8]:
                binary = cv2.adaptiveThreshold(
                    enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY_INV, block_size, c_value
                )
                binaries.append((f"Adaptive_{block_size}_{c_value}", binary))
        
        # 2. Otsu threshold
        _, binary_otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        binaries.append(("Otsu", binary_otsu))
        
        # 3. 다양한 고정 threshold 값
        for thresh_val in [60, 80, 100, 120, 140]:
            _, binary = cv2.threshold(enhanced, thresh_val, 255, cv2.THRESH_BINARY_INV)
            binaries.append((f"Fixed_{thresh_val}", binary))
        
        # 4. 역방향 이진화도 시도 (배경이 어두운 경우)
        for thresh_val in [80, 120]:
            _, binary = cv2.threshold(enhanced, thresh_val, 255, cv2.THRESH_BINARY)
            binaries.append((f"Normal_{thresh_val}", binary))
        
        # 가장 많은 유효한 윤곽선을 찾은 이진화 선택
        best_binary = None
        best_count = 0
        best_name = ""
        
        for name, binary in binaries:
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # 적절한 크기의 윤곽선만 카운트
            valid_contours = [c for c in contours if self._is_valid_contour_size(c, width, height)]
            
            if len(valid_contours) > best_count:
                best_count = len(valid_contours)
                best_binary = binary.copy()
                best_name = name
        
        # 아무것도 찾지 못했으면 기본값 사용
        if best_binary is None:
            if self.debug_mode:
                print("⚠️  유효한 윤곽선을 찾지 못함. 기본 Otsu 사용")
            best_binary = binary_otsu
            best_name = "Otsu_fallback"
        
        # 노이즈 제거 후처리
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary_clean = cv2.morphologyEx(best_binary, cv2.MORPH_OPEN, kernel, iterations=1)
        binary_clean = cv2.morphologyEx(binary_clean, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        if self.debug_mode:
            print(f"선택된 이진화: {best_name}, 유효 윤곽선: {best_count}개")
        
        return original, enhanced, binary_clean
    
    def _is_valid_contour_size(self, contour, img_width, img_height):
        """윤곽선이 적절한 크기인지 확인 - 관대한 기준 + OpenCV 오류 방지"""
        try:
            # OpenCV 오류 방지를 위한 윤곽선 검증
            if contour is None or len(contour) < 3:
                return False
            
            # 윤곽선 데이터 타입 확인 및 변환
            if contour.dtype != np.int32 and contour.dtype != np.float32:
                contour = contour.astype(np.int32)
            
            # 윤곽선 모양 검증
            if contour.ndim != 3 or contour.shape[2] != 2:
                return False
            
            area = cv2.contourArea(contour)
            
            # 비정상적인 면적값 처리
            if area <= 0 or not np.isfinite(area):
                return False
            
            total_area = img_width * img_height
            if total_area <= 0:
                return False
                
            area_ratio = area / total_area
            
            # 1차 검사: 비율 기반 필터링
            ratio_check = self.min_area_ratio <= area_ratio <= self.max_area_ratio
            
            # 2차 검사: 절대 크기 기반 필터링
            absolute_check = area >= self.min_absolute_area
            
            # 3차 검사: 너무 작은 점 제거 (넘이 작으면 노이즈)
            min_dimension = min(img_width, img_height) * 0.005  # 이미지 최소 치수의 0.5%
            dimension_check = area >= (min_dimension ** 2)
            
            # 모든 조건을 만족해야 통과
            is_valid = ratio_check and absolute_check and dimension_check
            
            if self.debug_mode and not is_valid:
                print(f"    거부된 윤곽선: 면적={area:.0f}, 비율={area_ratio*100:.4f}%, 비율검사={ratio_check}, 절대검사={absolute_check}, 차원검사={dimension_check}")
            
            return is_valid
            
        except Exception as e:
            if self.debug_mode:
                print(f"    윤곽선 크기 검증 오류: {e}")
            return False
    
    def detect_hand_drawn_shapes(self, image_path: str) -> List[ShapeRegion]:
        """손그림 도형들을 감지하여 영역 리스트 반환 - 원형/타원형만 필터링"""
        original, gray, binary = self.preprocess_image(image_path)
        height, width = binary.shape
        
        # 윤곽선 찾기
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_shapes = []
        
        for i, contour in enumerate(contours):
            # 크기 필터링
            if not self._is_valid_contour_size(contour, width, height):
                continue
            
            # 도형 분석
            shape_info = self._analyze_shape(contour)
            if shape_info is None:
                continue
            
            # ⭐ 원형/타원형만 필터링 - 주요 수정 부분
            if not self._is_circle_or_ellipse(shape_info):
                if self.debug_mode:
                    print(f"도형 {i+1} 제외: {shape_info['type']} (원형/탄원형 아님)")
                continue
                
            # 바운딩 박스 계산
            x, y, w, h = cv2.boundingRect(contour)
            
            # 수기 도형을 위한 더 많은 마진 추가 (텍스트가 도형 경계 근처에 있을 수 있음)
            margin = max(8, min(w, h) // 8)  # 5 -> 8, //10 -> //8
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(width - x, w + 2 * margin)
            h = min(height - y, h + 2 * margin)
            
            # ShapeRegion 객체 생성
            region = ShapeRegion(x, y, w, h, contour, shape_info['type'])
            detected_shapes.append(region)
            
            if self.debug_mode:
                print(f"원형/타원형 {i+1}: {shape_info['type']}, 위치: ({x},{y}), 크기: {w}x{h}, 원형성: {shape_info['circularity']:.3f}")
        
        # 크기순으로 정렬 (큰 것부터)
        detected_shapes.sort(key=lambda r: r.area(), reverse=True)
        
        print(f"🔍 OpenCV가 감지한 원형/타원형: {len(detected_shapes)}개")
        
        return detected_shapes
    
    def _analyze_shape(self, contour) -> Optional[Dict]:
        """윤곽선을 분석하여 도형 타입 판단 - 수기 도형에 최적화 + OpenCV 오류 방지"""
        try:
            # OpenCV 오류 방지를 위한 윤곽선 검증
            if contour is None or len(contour) < 3:
                return None
            
            # 윤곽선 데이터 타입 확인 및 변환
            if contour.dtype != np.int32 and contour.dtype != np.float32:
                contour = contour.astype(np.int32)
            
            area = cv2.contourArea(contour)
            if area < 25:  # 더 작은 영역도 고려 (50 -> 25)
                return None
            
            # 둘레 계산
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                return None
            
            # 원형성 계산 (4π × 면적 / 둘레²)
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            # 수기 도형을 위한 다양한 epsilon 값 시도 (더 많은 옵션)
            epsilons = [0.005 * perimeter, 0.01 * perimeter, 0.02 * perimeter, 0.03 * perimeter, 0.05 * perimeter]
            best_approx = None
            best_vertices = float('inf')
            
            for epsilon in epsilons:
                try:
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    if len(approx) < best_vertices and len(approx) >= 3:
                        best_approx = approx
                        best_vertices = len(approx)
                except:
                    continue
            
            if best_approx is None:
                return None
            
            # 더 관대한 수기 도형 타입 판단
            shape_type = "unknown"
            
            # 원형성이 높으면 꼭지점 수에 관계없이 원형으로 분류
            if circularity > 0.7:
                shape_type = "circle_like"
            elif circularity > 0.4:
                shape_type = "ellipse_like"
            elif len(best_approx) <= 6 and circularity > 0.3:
                shape_type = "circle_like"  # 적은 꼭지점 + 어느정도 원형성
            elif len(best_approx) <= 10 and circularity > 0.2:
                shape_type = "ellipse_like"  # 중간 꼭지점 + 약간의 원형성
            elif len(best_approx) <= 12:
                shape_type = "polygon_like"
            else:
                shape_type = "complex_shape"
            
            # 종횡비 계산
            try:
                rect = cv2.minAreaRect(contour)
                (_, _), (w, h), _ = rect
                aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 1
            except:
                aspect_ratio = 1
            
            # 컴팩트니스 계산 (도형의 정규성 측정)
            try:
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                compactness = area / hull_area if hull_area > 0 else 0
            except:
                compactness = 0
            
            # 연장도 계산 (원형성 보조 지표)
            try:
                bbox_area = cv2.contourArea(cv2.boundingRect(contour))
                extent = area / bbox_area if bbox_area > 0 else 0
            except:
                extent = 0
            
            return {
                'type': shape_type,
                'circularity': circularity,
                'vertices': len(best_approx),
                'aspect_ratio': aspect_ratio,
                'area': area,
                'perimeter': perimeter,
                'compactness': compactness,
                'extent': extent
            }
            
        except Exception as e:
            if self.debug_mode:
                print(f"    도형 분석 오류: {e}")
            return None
    
    def _is_circle_or_ellipse(self, shape_info: Dict) -> bool:
        """도형이 원형 또는 타원형인지 판단 - 더 관대한 기준"""
        shape_type = shape_info['type']
        circularity = shape_info['circularity']
        vertices = shape_info['vertices']
        aspect_ratio = shape_info.get('aspect_ratio', 1)
        compactness = shape_info.get('compactness', 0)
        extent = shape_info.get('extent', 0)
        
        # 1차 필터: 도형 타입으로 기본 필터링
        if shape_type in ['circle_like', 'ellipse_like']:
            return True
        
        # 2차 필터: 원형성 기반 필터링 (더 관대한 기준)
        if circularity > 0.25:  # 0.3 -> 0.25
            return True
        
        # 3차 필터: 꼭지점 수와 컴팩트니스 조합
        if vertices <= 8 and compactness > 0.75:  # 6 -> 8, 0.8 -> 0.75
            return True
        
        # 4차 필터: 연장도 기반 (원형에 가까운 모양)
        if extent > 0.6 and vertices <= 10:  # 높은 연장도 + 적절한 꼭지점
            return True
        
        # 5차 필터: 원형에 가까운 다각형 (수기 도형 고려) - 더 관대
        if (vertices <= 12 and circularity > 0.15 and aspect_ratio < 4 and 
            compactness > 0.6):  # 8->12, 0.25->0.15, 3->4, 0.8->0.6
            return True
        
        # 6차 필터: 종횡비가 원형에 가까운 도형 (정원 제외)
        if aspect_ratio < 2.5 and circularity > 0.2 and vertices <= 10:
            return True
        
        return False
    
    def create_debug_image(self, image_path: str, shapes: List[ShapeRegion], output_path: str):
        """디버그용 이미지 생성 (감지된 도형들 시각화)"""
        original = cv2.imread(image_path)
        if original is None:
            return False
        
        # 각 도형에 번호와 박스 그리기
        colors = [
            (0, 255, 0),    # 초록
            (255, 0, 0),    # 빨강  
            (0, 0, 255),    # 파랑
            (255, 255, 0),  # 노랑
            (255, 0, 255),  # 마젠타
            (0, 255, 255),  # 시안
            (255, 128, 0),  # 주황
            (128, 0, 255),  # 보라
        ]
        
        for i, shape in enumerate(shapes):
            color = colors[i % len(colors)]
            
            # 바운딩 박스 그리기
            cv2.rectangle(original, (shape.x, shape.y), 
                         (shape.x + shape.w, shape.y + shape.h), color, 2)
            
            # 번호 표시
            cv2.putText(original, f"{i+1}", (shape.x, shape.y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # 윤곽선도 그리기 (있는 경우)
            if shape.contour is not None:
                cv2.drawContours(original, [shape.contour], -1, color, 1)
        
        # 정보 텍스트 추가
        info_text = f"Detected Shapes: {len(shapes)}"
        cv2.putText(original, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # 저장
        success = cv2.imwrite(output_path, original)
        if success:
            print(f"🎯 디버그 이미지 저장: {os.path.basename(output_path)}")
        
        return success
    
    def save_regions_as_separate_images(self, image_path: str, shapes: List[ShapeRegion], output_dir: str):
        """각 도형 영역을 개별 이미지로 저장"""
        original = cv2.imread(image_path)
        if original is None:
            return []
        
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = []
        
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        for i, shape in enumerate(shapes):
            # 영역 크롭
            cropped = original[shape.y:shape.y+shape.h, shape.x:shape.x+shape.w]
            
            # 저장
            crop_filename = f"{base_name}_region_{i+1:02d}.png"
            crop_path = os.path.join(output_dir, crop_filename)
            
            success = cv2.imwrite(crop_path, cropped)
            if success:
                saved_paths.append(crop_path)
                print(f"💾 영역 {i+1} 저장: {crop_filename}")
        
        return saved_paths


def test_hybrid_detector():
    """하이브리드 감지기 테스트"""
    print("🧪 하이브리드 도형 감지기 테스트")
    
    detector = HybridShapeDetector()
    detector.set_debug_mode(True)
    
    # 테스트 이미지 경로
    test_image = "\\wsl.localhost\\Udev\\home\\kckang\\work\\test-sdp\\input\\17301.png"
    
    if not os.path.exists(test_image):
        print(f"❌ 테스트 이미지를 찾을 수 없습니다: {test_image}")
        return
    
    try:
        # 도형 감지
        shapes = detector.detect_hand_drawn_shapes(test_image)
        print(f"✅ 감지된 도형 수: {len(shapes)}개")
        
        # 디버그 이미지 생성
        debug_output = "\\wsl.localhost\\Udev\\home\\kckang\\work\\test-sdp\\output\\debug_shapes.png"
        detector.create_debug_image(test_image, shapes, debug_output)
        
        # 각 영역별 상세 정보
        for i, shape in enumerate(shapes):
            print(f"도형 {i+1}: {shape.shape_type}, 크기: {shape.w}x{shape.h}, 위치: ({shape.x},{shape.y})")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_hybrid_detector()
