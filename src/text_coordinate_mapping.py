"""
텍스트 위치 매핑 및 시각화 도구
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional

def get_text_coordinates_from_api(api_key, model_name, image_path):
    """
    API에서 텍스트와 좌표 정보를 함께 요청
    """
    try:
        import dashscope
        import base64
        from endpoint_config import configure_international_endpoint
        
        # 국제 엔드포인트 설정
        configure_international_endpoint()
        dashscope.api_key = api_key
        
        # 이미지 인코딩
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 좌표 정보를 포함한 요청
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{base64_image}"},
                    {"text": "이미지에서 모든 텍스트를 추출하고, 각 텍스트의 대략적인 위치(상단/중단/하단, 좌측/중앙/우측)도 함께 알려주세요. 형식: [텍스트] - 위치: [위치정보]"}
                ]
            }
        ]
        
        response = dashscope.MultiModalConversation.call(
            model=model_name,
            messages=messages
        )
        
        from response_utils import extract_text_from_response
        result = extract_text_from_response(response)
        
        return result
        
    except Exception as e:
        print(f"❌ 좌표 정보 요청 실패: {e}")
        return None

def estimate_text_regions(image_path, extracted_text):
    """
    추출된 텍스트를 기반으로 텍스트 영역을 추정
    """
    try:
        # OpenCV로 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        height, width = image.shape[:2]
        
        # 텍스트를 라인별로 분할
        lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
        
        # 각 라인에 대해 대략적인 위치 추정
        regions = []
        line_height = height // max(len(lines), 1)
        
        for i, line in enumerate(lines):
            # 수직 위치 계산
            y_start = i * line_height
            y_end = min((i + 1) * line_height, height)
            
            # 수평 위치는 텍스트 길이에 따라 추정
            text_width = min(len(line) * 10, width - 40)  # 대략적인 추정
            x_start = 20
            x_end = x_start + text_width
            
            regions.append({
                'text': line,
                'bbox': (x_start, y_start, x_end, y_end),
                'confidence': 0.8  # 추정값이므로 낮은 신뢰도
            })
        
        return regions
        
    except Exception as e:
        print(f"❌ 텍스트 영역 추정 실패: {e}")
        return None

def use_easyocr_for_coordinates(image_path):
    """
    EasyOCR을 사용하여 텍스트와 좌표 정보 추출
    """
    try:
        import easyocr
        
        # EasyOCR 리더 초기화 (한국어, 영어)
        reader = easyocr.Reader(['ko', 'en'], gpu=True)
        
        # 텍스트 인식
        results = reader.readtext(image_path)
        
        # 결과 파싱
        text_regions = []
        full_text_parts = []
        
        for (bbox, text, confidence) in results:
            # bbox는 4개 점의 좌표 [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
            # 이를 (x_min, y_min, x_max, y_max) 형식으로 변환
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            
            x_min, x_max = int(min(x_coords)), int(max(x_coords))
            y_min, y_max = int(min(y_coords)), int(max(y_coords))
            
            text_regions.append({
                'text': text,
                'bbox': (x_min, y_min, x_max, y_max),
                'confidence': confidence,
                'original_bbox': bbox
            })
            
            full_text_parts.append(text)
        
        # 전체 텍스트 결합
        full_text = '\n'.join(full_text_parts)
        
        return text_regions, full_text
        
    except ImportError:
        print("⚠️  EasyOCR이 설치되지 않았습니다. 추정 방법을 사용합니다.")
        return None, None
    except Exception as e:
        print(f"❌ EasyOCR 실행 실패: {e}")
        return None, None

def draw_text_boxes_on_image(image_path, text_regions, output_path, method_name="OCR"):
    """
    이미지에 텍스트 박스와 내용을 그려서 저장
    """
    try:
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ 이미지 로드 실패: {image_path}")
            return False
        
        # PIL로 변환 (한글 폰트 지원)
        image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(image_pil)
        
        # 폰트 설정
        font_size = max(12, min(24, image.shape[1] // 50))
        try:
            # Linux/WSL
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            try:
                # Windows
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    # 한글 폰트
                    font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", font_size)
                except:
                    font = ImageFont.load_default()
        
        # 색상 설정
        colors = [
            (255, 0, 0),    # 빨강
            (0, 255, 0),    # 초록
            (0, 0, 255),    # 파랑
            (255, 255, 0),  # 노랑
            (255, 0, 255),  # 마젠타
            (0, 255, 255),  # 시안
            (255, 128, 0),  # 주황
            (128, 0, 255),  # 보라
        ]
        
        print(f"📍 {len(text_regions)}개의 텍스트 영역을 그립니다...")
        
        for i, region in enumerate(text_regions):
            bbox = region['bbox']
            text = region['text']
            confidence = region.get('confidence', 0.0)
            
            x_min, y_min, x_max, y_max = bbox
            color = colors[i % len(colors)]
            
            # 박스 그리기
            draw.rectangle([x_min, y_min, x_max, y_max], outline=color, width=2)
            
            # 신뢰도에 따른 배경색 설정
            alpha = int(confidence * 100) if confidence > 0.5 else 50
            
            # 텍스트 배경 박스
            text_bbox = draw.textbbox((x_min, y_min - font_size - 5), f"{i+1}", font=font)
            draw.rectangle([
                text_bbox[0] - 2, text_bbox[1] - 2,
                text_bbox[2] + 2, text_bbox[3] + 2
            ], fill=(*color, alpha))
            
            # 텍스트 번호 표시
            draw.text((x_min, y_min - font_size - 5), f"{i+1}", fill=(255, 255, 255), font=font)
            
            # 신뢰도 표시 (있는 경우)
            if confidence > 0:
                conf_text = f"{confidence:.2f}"
                draw.text((x_max - 30, y_min - font_size - 5), conf_text, fill=color, font=font)
        
        # 범례 추가
        legend_y = 10
        draw.text((10, legend_y), f"{method_name} 결과 ({len(text_regions)}개 영역)", 
                 fill=(0, 0, 0), font=font)
        
        # 텍스트 목록 추가 (이미지 하단)
        text_list_y = image.shape[0] - (len(text_regions) + 2) * (font_size + 5)
        text_list_y = max(text_list_y, image.shape[0] // 2)  # 최소 중간 위치
        
        draw.text((10, text_list_y), "인식된 텍스트:", fill=(0, 0, 0), font=font)
        
        for i, region in enumerate(text_regions):
            text_line = f"{i+1}. {region['text']}"
            if region.get('confidence', 0) > 0:
                text_line += f" ({region['confidence']:.2f})"
            
            y_pos = text_list_y + (i + 1) * (font_size + 5)
            color = colors[i % len(colors)]
            draw.text((20, y_pos), text_line, fill=color, font=font)
        
        # 다시 OpenCV 형식으로 변환
        result_image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
        
        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 저장
        success = cv2.imwrite(output_path, result_image)
        
        if success:
            print(f"✅ 텍스트 매핑 이미지 저장: {os.path.basename(output_path)}")
            return True
        else:
            print(f"❌ 이미지 저장 실패: {output_path}")
            return False
        
    except Exception as e:
        print(f"❌ 텍스트 박스 그리기 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_text_coordinate_mapping(image_path, extracted_text, output_dir, method="auto"):
    """
    메인 함수: 텍스트 좌표 매핑 이미지 생성
    """
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    print(f"\n🎯 텍스트 좌표 매핑 시작: {os.path.basename(image_path)}")
    
    text_regions = None
    ocr_text = None
    method_used = "Unknown"
    
    # 방법 1: EasyOCR 사용 (가장 정확함)
    if method in ["auto", "easyocr"]:
        print("🔍 EasyOCR로 좌표 정보 추출 시도...")
        text_regions, ocr_text = use_easyocr_for_coordinates(image_path)
        if text_regions:
            method_used = "EasyOCR"
            print(f"✅ EasyOCR로 {len(text_regions)}개 영역 검출")
    
    # 방법 2: 추정 방법 (EasyOCR 실패 시 또는 직접 선택)
    if not text_regions:
        print("🔍 추정 방법으로 텍스트 영역 계산...")
        text_regions = estimate_text_regions(image_path, extracted_text)
        method_used = "추정방법"
        if text_regions:
            print(f"✅ 추정으로 {len(text_regions)}개 영역 생성")
    
    if not text_regions:
        print("❌ 텍스트 영역을 찾을 수 없습니다.")
        return False
    
    # 결과 이미지 생성
    output_path = os.path.join(output_dir, f"{base_name}_coordinates_{method_used.lower()}.png")
    success = draw_text_boxes_on_image(image_path, text_regions, output_path, method_used)
    
    # 텍스트 비교 정보 저장
    if success:
        comparison_file = os.path.join(output_dir, f"{base_name}_text_comparison.txt")
        with open(comparison_file, 'w', encoding='utf-8') as f:
            f.write(f"=== 텍스트 좌표 매핑 결과 ===\n")
            f.write(f"방법: {method_used}\n")
            f.write(f"검출된 영역 수: {len(text_regions)}\n")
            f.write(f"처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("=== 원본 추출 텍스트 ===\n")
            f.write(extracted_text)
            f.write("\n\n")
            
            if ocr_text:
                f.write("=== OCR 라이브러리 추출 텍스트 ===\n")
                f.write(ocr_text)
                f.write("\n\n")
            
            f.write("=== 영역별 상세 정보 ===\n")
            for i, region in enumerate(text_regions):
                bbox = region['bbox']
                f.write(f"{i+1}. 텍스트: {region['text']}\n")
                f.write(f"   좌표: ({bbox[0]}, {bbox[1]}) - ({bbox[2]}, {bbox[3]})\n")
                if region.get('confidence'):
                    f.write(f"   신뢰도: {region['confidence']:.3f}\n")
                f.write("\n")
        
        print(f"📄 비교 정보 저장: {os.path.basename(comparison_file)}")
    
    return success

if __name__ == "__main__":
    # 테스트용
    print("🎯 텍스트 좌표 매핑 도구 테스트")
    
    # 사용 가능한 OCR 라이브러리 확인
    try:
        import easyocr
        print("✅ EasyOCR 사용 가능")
    except ImportError:
        print("❌ EasyOCR 설치되지 않음")
