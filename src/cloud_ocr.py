"""
Qwen Cloud API를 사용한 OCR 처리 (개선된 버전)
"""

import dashscope
import base64
import os
from PIL import Image
from tqdm import tqdm
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils import create_output_directory, draw_text_on_image, save_text_result, measure_time
from network_utils import configure_ssl, create_robust_session
from network_advanced import create_permissive_session, configure_advanced_ssl
from endpoint_config import configure_international_endpoint
from response_utils import extract_text_from_response, debug_response_structure

class CloudOCRProcessor:
    def __init__(self, api_key, model_name="qwen-vl-plus"):
        self.api_key = api_key
        self.model_name = model_name
        
        # 국제 엔드포인트 설정 먼저
        configure_international_endpoint()
        
        # dashscope API 키 설정
        dashscope.api_key = api_key
        
        # SSL 및 네트워크 설정 (관대한 모드)
        configure_advanced_ssl()
        self.session = create_permissive_session()
        
        # OCR 모드 설정 (shape_detection, general, hybrid)
        self.ocr_mode = "shape_detection"
    
    def set_ocr_mode(self, mode):
        """추출 모드 설정"""
        if mode in ["shape_detection", "general", "hybrid"]:
            self.ocr_mode = mode
            print(f"🔄 OCR 모드 변경: {mode}")
        else:
            print(f"⚠️  지원되지 않는 모드: {mode}. shape_detection, general, hybrid만 가능합니다.")

        
    def _encode_image(self, image_path):
        """이미지를 base64로 인코딩"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"이미지 인코딩 오류: {e}")
            return None
    
    def _get_prompt_for_mode(self, mode="shape_detection"):
        """OCR 모드에 따른 프롬프트 반환 - 수기 도형 텍스트 최적화"""
        if mode == "shape_detection":
            return """이 스캔 문서에서 수기로 그어진 도형(원, 타원) 안에 작성된 텍스트를 정확히 읽어주세요.

🎯 핵심 작업:
1. 손으로 그린 도형들을 식별하세요 (완전하지 않거나 불규칙한 모양 포함)
2. 각 도형 내부에 있는 손글씨나 인쇄된 텍스트를 정확히 읽어주세요
3. 도형으로 둘러싸인 모든 텍스트를 빠짐없이 추출해주세요

⚠️ 주의사항:
- 손그림 도형은 불완전하고 찌그러져 있을 수 있습니다
- 원형, 타원형 형태가 있습니다
- 도형이 겹치거나 붙어있을 수 있습니다
- 도형 크기는 매우 다양합니다 (작은 것부터 큰 것까지)
- 프린트된 텍스트와 손글씨가 혼재할 수 있습니다
- 도형 경계선과 내부 텍스트를 명확히 구분하세요
- 흐릿하거나 불분명한 글자도 최대한 추측해서 읽어주세요

📝 출력 형식:
각 도형에서 발견된 텍스트를 한 줄씩 출력해주세요.
설명이나 주석 없이 텍스트 내용만 출력해주세요."""
        elif mode == "hybrid":
            return """이 이미지에서 보이는 모든 텍스트를 정확히 읽어주세요. (하이브리드 모드 - 도형 영역 세분화 처리)

🎯 지침:
- 이 이미지는 특정 도형 영역에서 잘라낸 부분입니다
- 모든 글자와 숫자를 정확히 읽어주세요
- 손글씨와 인쇄 텍스트 모두 포함합니다
- 흐릿하거나 부분적으로 잘린 글자도 최대한 추측해서 읽어주세요
- 좌표나 위치 정보가 아닌 실제 텍스트 내용만 출력해주세요

📝 출력 형식:
- 설명이나 주석 없이 텍스트 내용만 출력해주세요
- 한 줄에 하나의 단어나 구문만 작성해주세요

Read all visible text in this cropped region. Focus on handwritten and printed text. Return only the actual text content."""
        else:  # general mode
            return """이미지에서 모든 텍스트를 정확히 읽어서 추출해주세요.

지침:
- 이미지에 보이는 모든 글자와 숫자를 정확히 읽어주세요
- 좌표나 위치 정보가 아닌 실제 텍스트 내용만 출력해주세요
- 읽는 순서대로 한 줄씩 출력해주세요
- 설명 없이 텍스트 내용만 출력해주세요

Extract all visible text from this image. Return only the actual text content, not coordinates."""
    
    def _crop_image_intelligently(self, image_path, target_size=(1024, 1024)):
        """이미지를 지능적으로 크롭하여 OCR 성능 향상"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # 이미지가 너무 크면 중앙 부분을 크롭
                if width > target_size[0] * 2 or height > target_size[1] * 2:
                    # 중앙에서 target_size 크기로 크롭
                    left = (width - target_size[0]) // 2
                    top = (height - target_size[1]) // 2
                    right = left + target_size[0]
                    bottom = top + target_size[1]
                    
                    # 경계 체크
                    left = max(0, left)
                    top = max(0, top)
                    right = min(width, right)
                    bottom = min(height, bottom)
                    
                    cropped = img.crop((left, top, right, bottom))
                    
                    # 임시 파일로 저장
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, f"cropped_{os.path.basename(image_path)}")
                    cropped.save(temp_path)
                    
                    print(f"🔍 이미지 크롭됨: {width}x{height} → {cropped.size[0]}x{cropped.size[1]}")
                    return temp_path
                    
            return image_path  # 크롭이 필요없으면 원본 경로 반환
            
        except Exception as e:
            print(f"⚠️  이미지 크롭 실패: {e}")
            return image_path
    
    def process_image_hybrid(self, image_path):
        """하이브리드 방식: 그리드 기반 영역 분할 + AI 처리"""
        try:
            print(f"🤖 하이브리드 모드 시작: {os.path.basename(image_path)}")
            print(f"📝 방식: 그리드 기반 영역 분할 (OpenCV 대체)")
            
            # 그리드 기반 처리를 위한 모듈 import
            from PIL import Image
            import math
            
            # 이미지 로드 및 기본 정보
            img = Image.open(image_path)
            width, height = img.size
            
            # 적응적 그리드 크기 결정 (12개 영역 목표)
            target_regions = 12
            aspect_ratio = width / height
            cols = math.ceil(math.sqrt(target_regions * aspect_ratio))
            rows = math.ceil(target_regions / cols)
            
            print(f"🔍 이미지 분할: {cols}×{rows} 그리드 ({cols*rows}개 영역)")
            
            # 그리드 영역 생성
            grid_width = width // cols
            grid_height = height // rows
            overlap_ratio = 0.1
            overlap_w = int(grid_width * overlap_ratio)
            overlap_h = int(grid_height * overlap_ratio)
            
            all_texts = []
            successful_regions = 0
            
            # 각 영역 처리
            for row in range(rows):
                for col in range(cols):
                    try:
                        # 영역 좌표 계산
                        start_x = max(0, col * grid_width - overlap_w)
                        start_y = max(0, row * grid_height - overlap_h)
                        end_x = min(width, (col + 1) * grid_width + overlap_w)
                        end_y = min(height, (row + 1) * grid_height + overlap_h)
                        
                        # 영역 크롭
                        region = img.crop((start_x, start_y, end_x, end_y))
                        
                        print(f"🤖 영역 ({row},{col}) 처리 중...")
                        
                        # AI로 영역 처리
                        region_text = self._process_grid_region(region, row, col)
                        
                        if region_text and region_text.strip() and not region_text.startswith("이미지 처리 중 오류"):
                            # "없음" 같은 응답 필터링
                            if region_text.lower() not in ['없음', 'none', 'no text', 'no circles', '원형 없음']:
                                all_texts.append(region_text.strip())
                                successful_regions += 1
                                print(f"✅ 영역 ({row},{col}): '{region_text.strip()[:30]}...'")
                            else:
                                print(f"❌ 영역 ({row},{col}): 원형 텍스트 없음")
                        else:
                            print(f"❌ 영역 ({row},{col}): 텍스트 추출 실패")
                            
                    except Exception as e:
                        print(f"❌ 영역 ({row},{col}) 처리 오류: {e}")
                        continue
            
            # 결과 정리
            if all_texts:
                final_result = "\n".join(all_texts)
                print(f"🎉 그리드 처리 완료: {successful_regions}/{cols*rows}개 영역 성공")
                print(f"📝 총 추출 텍스트 길이: {len(final_result)}자")
                return final_result
            else:
                print(f"⚠️  모든 영역에서 원형 텍스트 추출 실패. 일반 모드로 대체")
                return self._process_single_image_fallback(image_path, "general")
                
        except Exception as e:
            print(f"❌ 그리드 처리 오류: {e}")
            return self._process_single_image_fallback(image_path, "general")
    
    def _process_grid_region(self, region_image, row, col):
        """그리드 영역 개별 처리"""
        try:
            import base64
            import io
            
            # 이미지를 base64로 인코딩
            img_buffer = io.BytesIO()
            region_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            base64_image = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            # 원형/타원형 감지에 특화된 프롬프트
            prompt_text = """이 이미지 영역에서 수기로 그어진 원형이나 타원형 도형 안에 있는 텍스트만 찾아 추출해주세요.

🎯 찾아야 할 것:
- 손으로 그린 원, 타원, 동그라미 안의 텍스트
- 완전하지 않은 원형도 포함 (찌그러진 원, 타원)
- 작은 원부터 큰 원까지 모든 크기
- 손글씨나 인쇄 텍스트 모두

⚠️ 무시할 것:
- 사각형, 삼각형, 직선으로 둘러싸인 텍스트
- 원형 밖에 있는 일반 텍스트
- 표나 선으로만 구분된 텍스트

📝 출력 형식:
원형/타원형 안에 텍스트가 있으면 그 텍스트만 한 줄씩 출력하고,
없으면 "없음"이라고 출력해주세요.

Find text inside hand-drawn circles or ellipses only. Ignore rectangular boxes and plain text."""
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": f"data:image/png;base64,{base64_image}"},
                        {"text": prompt_text}
                    ]
                }
            ]
            
            response = dashscope.MultiModalConversation.call(
                model=self.model_name,
                messages=messages
            )
            
            # 새로운 응답 처리 유틸리티 사용
            from response_utils import extract_text_from_response
            result = extract_text_from_response(response)
            return result if result else "없음"
            
        except Exception as e:
            return f"이미지 처리 중 오류: {e}"
    
    def _process_single_image_fallback(self, image_path, mode="general"):
        """단일 이미지 처리 (하이브리드 대체용)"""
        try:
            # 이미지 인코딩
            base64_image = self._encode_image(image_path)
            if not base64_image:
                return "이미지 인코딩 실패"
            
            # 모드별 프롬프트 선택
            prompt_text = self._get_prompt_for_mode(mode)
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{base64_image}"},
                        {"text": prompt_text}
                    ]
                }
            ]
            
            response = dashscope.MultiModalConversation.call(
                model=self.model_name,
                messages=messages
            )
            
            # 새로운 응답 처리 유틸리티 사용
            result = extract_text_from_response(response)
            return result if result else "텍스트 추출 실패"
            
        except Exception as e:
            return f"이미지 처리 중 오류: {e}"
    
    @measure_time
    def process_image(self, image_path, mode=None):
        """단일 이미지 OCR 처리 - 모드별 및 크롭 지원"""
        if mode is None:
            mode = self.ocr_mode
            
        max_retries = 3
        retry_delay = 2
        
        # 하이브리드 모드인 경우 특별 처리
        if mode == "hybrid":
            return self.process_image_hybrid(image_path)
        
        # 원본과 크롭된 이미지 모두 시도
        image_paths_to_try = [image_path]
        
        # 이미지가 크면 크롭 버전도 시도
        try:
            with Image.open(image_path) as img:
                if img.size[0] > 2048 or img.size[1] > 2048:
                    cropped_path = self._crop_image_intelligently(image_path)
                    if cropped_path != image_path:
                        image_paths_to_try.append(cropped_path)
        except:
            pass
        
        best_result = None
        best_length = 0
        
        for img_path in image_paths_to_try:
            for attempt in range(max_retries):
                try:
                    # 이미지 인코딩
                    base64_image = self._encode_image(img_path)
                    if not base64_image:
                        continue
                    
                    # 모드별 프롬프트 선택
                    prompt_text = self._get_prompt_for_mode(mode)
                    
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"image": f"data:image/jpeg;base64,{base64_image}"},
                                {"text": prompt_text}
                            ]
                        }
                    ]
                    
                    response = dashscope.MultiModalConversation.call(
                        model=self.model_name,
                        messages=messages
                    )
                    
                    # 새로운 응답 처리 유틸리티 사용
                    result = extract_text_from_response(response)
                    
                    # 결과 품질 평가 (텍스트 길이로 간단히 판단)
                    if result and len(result.strip()) > best_length:
                        best_result = result
                        best_length = len(result.strip())
                        
                        # 충분히 좋은 결과면 바로 반환
                        if best_length > 10:  # 10자 이상이면 충분
                            # 임시 파일 정리
                            if img_path != image_path and os.path.exists(img_path):
                                try:
                                    os.remove(img_path)
                                except:
                                    pass
                            
                            # 디버그 모드에서 응답 구조 출력
                            if os.getenv('DEBUG_API_RESPONSE', '').lower() == 'true':
                                debug_response_structure(response)
                                
                            return result
                        
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️  연결 오류 (재시도 {attempt + 1}/{max_retries}): {str(e)[:100]}...")
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        print(f"연결 실패: {str(e)[:100]}...")
                        break
                        
                except Exception as e:
                    print(f"이미지 처리 중 오류: {e}")
                    break
        
        # 임시 파일 정리
        for img_path in image_paths_to_try:
            if img_path != image_path and os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except:
                    pass
        
        # 최고 결과 반환 또는 실패
        if best_result:
            return best_result
        else:
            return "처리 실패: 텍스트를 추출할 수 없습니다"
    
    def process_images(self, image_files, output_base_dir):
        """여러 이미지 배치 처리"""
        # 출력 디렉토리 생성
        output_dir = create_output_directory(output_base_dir, f"cloud_{self.model_name}")
        
        print(f"\n📁 결과 저장 폴더: {output_dir}")
        print(f"📊 처리할 이미지 수: {len(image_files)}")
        print(f"🌐 사용 모델: {self.model_name}")
        
        total_time = 0
        successful_count = 0
        api_calls = 0
        results = []  # 결과 리스트 초기화
        
        # 진행률 표시
        with tqdm(total=len(image_files), desc="이미지 처리중") as pbar:
            for image_path in image_files:
                filename = os.path.basename(image_path)
                pbar.set_postfix({"현재": filename})
                
                try:
                    # OCR 처리
                    result_text, process_time = self.process_image(image_path)
                    total_time += process_time
                    api_calls += 1
                    
                    # 성공 여부 판단
                    is_success = (
                        result_text and 
                        not result_text.startswith("API 호출 실패") and 
                        not result_text.startswith("이미지 처리 중 오류") and
                        not result_text.startswith("연결 실패") and
                        not result_text.startswith("Image encoding failed") and
                        result_text != "처리 실패: 알 수 없는 오류"
                    )
                    
                    if is_success:
                        successful_count += 1
                        
                        # 텍스트 파일 저장
                        text_file = save_text_result(result_text, output_dir, filename)
                        
                        # 결과 이미지 생성
                        base_name = os.path.splitext(filename)[0]
                        output_image_path = os.path.join(output_dir, f"{base_name}_result.png")
                        image_success = draw_text_on_image(image_path, result_text, output_image_path)
                        
                        # 텍스트 좌표 매핑 이미지 생성
                        try:
                            from text_coordinate_mapping import create_text_coordinate_mapping
                            coord_success = create_text_coordinate_mapping(
                                image_path, result_text, output_dir, method="auto"
                            )
                            if coord_success:
                                print(f"🎯 좌표 매핑 이미지 생성 완료")
                        except Exception as coord_error:
                            print(f"⚠️  좌표 매핑 오류: {coord_error}")
                        
                        results.append({
                            'file': filename,
                            'success': True,
                            'text_length': len(result_text),
                            'time': process_time
                        })
                        
                        print(f"✅ {filename}: {len(result_text)}자 추출")
                        
                    else:
                        print(f"⚠️  실패: {filename} - {result_text[:100]}...")
                        results.append({
                            'file': filename,
                            'success': False,
                            'error': result_text[:200] if result_text else "Unknown error",
                            'time': process_time
                        })
                
                except Exception as e:
                    print(f"❌ 처리 오류: {filename} - {str(e)}")
                    results.append({
                        'file': filename,
                        'success': False,
                        'error': str(e)[:200],
                        'time': 0
                    })
                
                # API 레이트 리미트 고려 (약간의 대기)
                time.sleep(0.5)  # SSL 오류 방지를 위해 조금 더 길게
                pbar.update(1)
        
        # 결과 요약 저장
        summary_path = os.path.join(output_dir, "summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 클라우드 API 처리 결과 요약 ===\n")
            f.write(f"모델: {self.model_name}\n")
            f.write(f"성공: {successful_count}/{len(image_files)} 이미지\n")
            f.write(f"총 처리 시간: {total_time:.2f}초\n")
            f.write(f"평균 처리 시간: {total_time/len(image_files):.2f}초/이미지\n")
            f.write(f"API 호출 수: {api_calls}\n\n")
            
            for result in results:
                f.write(f"파일: {result['file']}\n")
                f.write(f"성공: {'예' if result['success'] else '아니오'}\n")
                if result['success']:
                    f.write(f"추출 텍스트 길이: {result['text_length']}자\n")
                else:
                    f.write(f"오류: {result.get('error', 'Unknown')}\n")
                f.write(f"처리 시간: {result['time']:.2f}초\n")
                f.write("-" * 30 + "\n")
        
        # 결과 요약
        print(f"\n=== 처리 완료 ===")
        print(f"성공: {successful_count}/{len(image_files)} 이미지")
        print(f"총 처리 시간: {total_time:.2f}초")
        print(f"평균 처리 시간: {total_time/len(image_files):.2f}초/이미지")
        print(f"API 호출 수: {api_calls}")
        print(f"결과 저장 위치: {output_dir}")
        
        return True


def run_cloud_ocr(api_key, model_name, image_files, output_dir, ocr_mode="shape_detection"):
    """클라우드 OCR 실행 함수 - 모드 지원"""
    if not api_key or api_key == "your_api_key_here":
        print("❌ API 키가 설정되지 않았습니다.")
        print("   .env 파일에서 QWEN_API_KEY를 설정해주세요.")
        return False
    
    processor = CloudOCRProcessor(api_key, model_name)
    
    # OCR 모드 설정
    processor.set_ocr_mode(ocr_mode)
    
    try:
        print(f"🌐 Qwen Cloud API 연결 중...")
        print(f"📡 모델: {model_name}")
        print(f"🎯 OCR 모드: {ocr_mode}")
        print("⚠️  네트워크 연결 문제가 있을 경우 재시도됩니다...")
        
        # 이미지 처리
        success = processor.process_images(image_files, output_dir)
        return success
        
    except Exception as e:
        print(f"❌ Cloud API 처리 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
