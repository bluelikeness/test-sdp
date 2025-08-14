#!/usr/bin/env python3
"""
그리드 기반 영역 분할 OCR 시스템
OpenCV 대신 이미지를 격자로 나누어 각 영역을 AI가 처리
"""

import os
import sys
import math
sys.path.append('src')

class GridBasedOCR:
    """그리드 기반 OCR 처리기"""
    
    def __init__(self, api_key, model_name="qwen-vl-plus"):
        self.api_key = api_key
        self.model_name = model_name
        
        # 네트워크 설정 추가 (cloud_ocr.py와 동일)
        self._setup_network()
        
    def _setup_network(self):
        """네트워크 설정 초기화"""
        try:
            import dashscope
            from network_utils import configure_ssl, create_robust_session
            from network_advanced import create_permissive_session, configure_advanced_ssl
            from endpoint_config import configure_international_endpoint
            
            # 국제 엔드포인트 설정 먼저
            configure_international_endpoint()
            
            # dashscope API 키 설정
            dashscope.api_key = self.api_key
            
            # SSL 및 네트워크 설정 (관대한 모드)
            configure_advanced_ssl()
            self.session = create_permissive_session()
            
            print("\u2705 네트워크 설정 완료")
            
        except Exception as e:
            print(f"\u26a0\ufe0f  네트워크 설정 오류: {e}")
            # 기본 설정으로 대체
            import dashscope
            dashscope.api_key = self.api_key
        
    def split_image_into_grid(self, image_path, grid_size=(3, 4), overlap_ratio=0.1):
        """이미지를 격자로 분할"""
        try:
            from PIL import Image
            import cv2
            
            # 이미지 로드
            img = Image.open(image_path)
            width, height = img.size
            
            print(f"📸 원본 이미지: {width}×{height}")
            print(f"🔲 격자 크기: {grid_size[0]}×{grid_size[1]} = {grid_size[0]*grid_size[1]}개 영역")
            
            # 격자 크기 계산 (오버랩 포함)
            grid_width = width // grid_size[0]
            grid_height = height // grid_size[1]
            
            overlap_w = int(grid_width * overlap_ratio)
            overlap_h = int(grid_height * overlap_ratio)
            
            print(f"📏 각 영역 크기: {grid_width}×{grid_height} (오버랩: {overlap_w}×{overlap_h})")
            
            regions = []
            
            for row in range(grid_size[1]):
                for col in range(grid_size[0]):
                    # 시작점 계산 (오버랩 고려)
                    start_x = max(0, col * grid_width - overlap_w)
                    start_y = max(0, row * grid_height - overlap_h)
                    
                    # 끝점 계산 (오버랩 고려)
                    end_x = min(width, (col + 1) * grid_width + overlap_w)
                    end_y = min(height, (row + 1) * grid_height + overlap_h)
                    
                    # 영역 크롭
                    region = img.crop((start_x, start_y, end_x, end_y))
                    
                    region_info = {
                        'image': region,
                        'position': (row, col),
                        'bbox': (start_x, start_y, end_x, end_y),
                        'size': (end_x - start_x, end_y - start_y)
                    }
                    
                    regions.append(region_info)
                    
                    print(f"   영역 ({row},{col}): ({start_x},{start_y}) → ({end_x},{end_y})")
            
            return regions
            
        except Exception as e:
            print(f"❌ 이미지 분할 실패: {e}")
            return []
    
    def split_image_adaptive(self, image_path, target_regions=12):
        """적응적 이미지 분할 (목표 영역 수에 맞춰)"""
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            width, height = img.size
            aspect_ratio = width / height
            
            # 목표 영역 수에 맞는 격자 크기 계산
            # 가로세로 비율을 고려해서 격자 결정
            cols = math.ceil(math.sqrt(target_regions * aspect_ratio))
            rows = math.ceil(target_regions / cols)
            
            # 실제 영역 수 조정
            actual_regions = cols * rows
            
            print(f"🎯 목표 영역: {target_regions}개")
            print(f"📐 이미지 비율: {aspect_ratio:.2f}")
            print(f"🔲 계산된 격자: {cols}×{rows} = {actual_regions}개")
            
            return self.split_image_into_grid(image_path, (cols, rows))
            
        except Exception as e:
            print(f"❌ 적응적 분할 실패: {e}")
            return []
    
    def process_region_with_ai(self, region_image, region_info):
        """AI로 개별 영역 처리"""
        try:
            import dashscope
            import base64
            import io
            from dotenv import load_dotenv
            
            # 환경변수 로드
            load_dotenv()
            dashscope.api_key = self.api_key
            
            # 이미지를 base64로 인코딩
            img_buffer = io.BytesIO()
            region_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            base64_image = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            # 원형/타원형 감지에 특화된 프롬프트
            prompt = """이 이미지 영역에서 수기로 그어진 원형이나 타원형 도형 안에 있는 텍스트만 찾아 추출해주세요.

🎯 찾아야 할 것:
- 손으로 그린 원, 타원, 동그라미 안의 텍스트
- 완전하지 않은 원형도 포함 (찌그러진 원, 타원)
- 작은 원부터 큰 원까지 모든 크기

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
                        {"text": prompt}
                    ]
                }
            ]
            
            response = dashscope.MultiModalConversation.call(
                model=self.model_name,
                messages=messages
            )
            
            # 응답 처리
            if response and response.status_code == 200:
                content = response.output.choices[0].message.content
                if isinstance(content, list):
                    # 텍스트 부분만 추출
                    text_parts = [item.get('text', '') for item in content if item.get('text')]
                    result = ' '.join(text_parts).strip()
                else:
                    result = str(content).strip()
                
                # "없음" 같은 응답은 필터링
                if result.lower() in ['없음', 'none', 'no text', 'no circles']:
                    return None
                
                return result
            else:
                return None
                
        except Exception as e:
            print(f"   ❌ AI 처리 오류: {e}")
            return None
    
    def save_region_images(self, regions, output_dir, base_name):
        """각 영역을 개별 이미지로 저장 (디버깅용)"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            saved_paths = []
            for i, region_info in enumerate(regions):
                row, col = region_info['position']
                filename = f"{base_name}_grid_{row}_{col}.png"
                filepath = os.path.join(output_dir, filename)
                
                region_info['image'].save(filepath)
                saved_paths.append(filepath)
            
            print(f"💾 {len(saved_paths)}개 영역 이미지 저장: {output_dir}")
            return saved_paths
            
        except Exception as e:
            print(f"❌ 영역 이미지 저장 실패: {e}")
            return []
    
    def create_result_visualization(self, original_path, regions, results, output_path):
        """결과 시각화 이미지 생성"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 원본 이미지 로드
            img = Image.open(original_path)
            draw = ImageDraw.Draw(img)
            
            # 폰트 설정 (시스템 기본 폰트 사용)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # 결과가 있는 영역만 표시
            for i, (region_info, result) in enumerate(zip(regions, results)):
                if result:  # 텍스트가 있는 영역만
                    bbox = region_info['bbox']
                    row, col = region_info['position']
                    
                    # 영역 테두리 그리기
                    draw.rectangle(bbox, outline='red', width=3)
                    
                    # 번호 표시
                    draw.text((bbox[0] + 5, bbox[1] + 5), f"{row},{col}", 
                             fill='red', font=font)
                    
                    # 결과 텍스트 (짧게)
                    short_text = result[:15] + "..." if len(result) > 15 else result
                    draw.text((bbox[0] + 5, bbox[1] + 30), short_text, 
                             fill='blue', font=font)
            
            # 저장
            img.save(output_path)
            print(f"🎯 결과 시각화 저장: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 시각화 생성 실패: {e}")
            return False
    
    def process_image_grid_based(self, image_path, grid_size=None, target_regions=12):
        """그리드 기반 이미지 처리"""
        print(f"🔲 그리드 기반 OCR 시작: {os.path.basename(image_path)}")
        
        # 이미지 분할
        if grid_size:
            regions = self.split_image_into_grid(image_path, grid_size)
        else:
            regions = self.split_image_adaptive(image_path, target_regions)
        
        if not regions:
            print("❌ 이미지 분할 실패")
            return None
        
        # 각 영역 저장 (디버깅용)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_dir = "output/grid_regions"
        self.save_region_images(regions, output_dir, base_name)
        
        # 각 영역을 AI로 처리
        print(f"\n🤖 각 영역을 AI로 처리 중...")
        results = []
        successful_regions = 0
        
        for i, region_info in enumerate(regions):
            row, col = region_info['position']
            print(f"   영역 ({row},{col}) 처리 중...", end=" ")
            
            result = self.process_region_with_ai(region_info['image'], region_info)
            
            if result:
                results.append(result)
                successful_regions += 1
                print(f"✅ '{result[:30]}...'")
            else:
                results.append(None)
                print(f"❌ 텍스트 없음")
        
        # 결과 통합
        final_texts = [r for r in results if r]
        
        if final_texts:
            final_result = "\n".join(final_texts)
            
            print(f"\n🎉 그리드 처리 완료:")
            print(f"   처리된 영역: {len(regions)}개")
            print(f"   텍스트 발견: {successful_regions}개 영역")
            print(f"   총 추출 텍스트 길이: {len(final_result)}자")
            
            # 결과 시각화
            viz_path = f"output/grid_result_{base_name}.png"
            self.create_result_visualization(image_path, regions, results, viz_path)
            
            return final_result
        else:
            print(f"\n⚠️  모든 영역에서 원형 텍스트를 찾지 못했습니다")
            return None


def test_grid_based_ocr():
    """그리드 기반 OCR 테스트"""
    print("🔲 그리드 기반 OCR 테스트")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("❌ API 키가 설정되지 않음")
            return False
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return False
        
        # 그리드 기반 OCR 생성
        ocr = GridBasedOCR(api_key, "qwen-vl-plus")
        
        # 여러 격자 크기로 테스트
        test_configs = [
            {"grid_size": (3, 4), "name": "3×4 격자"},
            {"grid_size": (4, 3), "name": "4×3 격자"},
            {"target_regions": 12, "name": "적응적 12영역"},
            {"target_regions": 16, "name": "적응적 16영역"}
        ]
        
        best_result = None
        best_count = 0
        
        for config in test_configs:
            print(f"\n🔲 {config['name']} 테스트:")
            
            if 'grid_size' in config:
                result = ocr.process_image_grid_based(test_image, 
                                                    grid_size=config['grid_size'])
            else:
                result = ocr.process_image_grid_based(test_image, 
                                                    target_regions=config['target_regions'])
            
            if result:
                text_count = len(result.split('\n'))
                print(f"   ✅ {text_count}개 텍스트 추출")
                
                if text_count > best_count:
                    best_count = text_count
                    best_result = result
                    best_config = config['name']
            else:
                print(f"   ❌ 텍스트 추출 실패")
        
        # 최고 결과 저장
        if best_result:
            os.makedirs("output", exist_ok=True)
            result_path = "output/grid_based_result.txt"
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write("=== 그리드 기반 OCR 결과 ===\n")
                f.write(f"최적 설정: {best_config}\n")
                f.write(f"추출된 텍스트 수: {best_count}개\n")
                f.write(f"총 텍스트 길이: {len(best_result)}자\n\n")
                f.write("=== 추출된 텍스트 ===\n")
                f.write(best_result)
            
            print(f"\n🎉 최고 결과: {best_config} ({best_count}개 텍스트)")
            print(f"💾 결과 저장: {result_path}")
            
            # 미리보기
            print(f"\n📄 추출된 텍스트 미리보기:")
            lines = best_result.split('\n')
            for i, line in enumerate(lines[:5]):
                print(f"  {i+1}: {line}")
            
            if len(lines) > 5:
                print(f"  ... (총 {len(lines)}개)")
            
            return True
        else:
            print(f"\n❌ 모든 격자 설정에서 텍스트 추출 실패")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 실행 함수"""
    print("🚀 그리드 기반 OCR 시스템")
    print("💡 아이디어: OpenCV 대신 이미지를 격자로 나누어 AI가 각각 처리")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    success = test_grid_based_ocr()
    
    if success:
        print(f"\n" + "=" * 60)
        print("🎉 그리드 기반 OCR 성공!")
        print("✨ 장점:")
        print("   ✅ OpenCV 의존성 없음")
        print("   ✅ AI가 직접 원형 감지")
        print("   ✅ 영역별 세밀한 처리")
        print("   ✅ 다양한 격자 크기 지원")
        print("   ✅ 결과 시각화 제공")
        
        print(f"\n📁 생성된 파일들:")
        print("   output/grid_regions/ - 각 영역별 이미지")
        print("   output/grid_result_*.png - 결과 시각화")
        print("   output/grid_based_result.txt - 최종 추출 텍스트")
        
    else:
        print(f"\n💡 대안 방법:")
        print("   1. 격자 크기 조정")
        print("   2. 프롬프트 개선")
        print("   3. 수동 영역 지정")

if __name__ == "__main__":
    main()
