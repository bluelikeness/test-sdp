#!/usr/bin/env python3
"""
스마트 영역 분할 OCR 시스템 (수정된 버전)
무작정 자르지 않고 AI가 먼저 원형 위치를 찾은 후 해당 영역만 세밀 처리
"""

import os
import sys
sys.path.append('src')

class SmartRegionOCR:
    """스마트 영역 기반 OCR 처리기"""
    
    def __init__(self, api_key, model_name="qwen-vl-plus"):
        self.api_key = api_key
        self.model_name = model_name
        
    def find_circle_regions_with_ai(self, image_path):
        """AI로 먼저 원형이 있는 대략적인 위치 찾기"""
        try:
            from cloud_ocr import CloudOCRProcessor
            
            processor = CloudOCRProcessor(self.api_key, self.model_name)
            
            # 1단계: 전체 이미지에서 원형 위치 스캔
            location_prompt = """이 이미지에서 수기로 그어진 원형이나 타원형 도형들이 있는 위치를 알려주세요.

🎯 찾아야 할 것:
- 손으로 그린 원, 타원, 동그라미 위치
- 완전하지 않은 원형도 포함

📍 출력 형식:
원형이 있는 위치를 다음과 같이 설명해주세요:
- "좌상단에 원형 2개"
- "중앙 부분에 큰 원형 1개"  
- "우하단에 작은 원형들 여러 개"
- "전체적으로 분산되어 있음"

위치가 파악되면 그 영역들을 어떻게 나누면 좋을지도 제안해주세요."""

            # 기존 CloudOCRProcessor의 단일 이미지 처리 사용
            import base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            messages = [
                {
                    "role": "user", 
                    "content": [
                        {"image": f"data:image/jpeg;base64,{base64_image}"},
                        {"text": location_prompt}
                    ]
                }
            ]
            
            import dashscope
            dashscope.api_key = self.api_key
            
            response = dashscope.MultiModalConversation.call(
                model=self.model_name,
                messages=messages
            )
            
            if response and response.status_code == 200:
                content = response.output.choices[0].message.content
                if isinstance(content, list):
                    location_info = ' '.join([item.get('text', '') for item in content if item.get('text')])
                else:
                    location_info = str(content)
                
                print(f"🔍 AI가 분석한 원형 위치:")
                print(f"   {location_info}")
                
                return location_info
            else:
                return "분석 실패"
                
        except Exception as e:
            print(f"❌ 위치 분석 실패: {e}")
            return "분석 실패"
    
    def create_smart_regions(self, image_path, location_info):
        """AI 분석 결과를 바탕으로 스마트한 영역 분할"""
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            width, height = img.size
            
            print(f"📏 이미지 크기: {width}×{height}")
            
            # 위치 정보를 바탕으로 영역 결정
            regions = []
            
            if "전체적으로 분산" in location_info or "여러 곳" in location_info:
                # 전체 분산 → 3×3 그리드 (오버랩 포함)
                print("📊 전체 분산 감지 → 3×3 오버랩 그리드 사용")
                regions = self._create_overlap_grid(width, height, 3, 3)
                
            elif "좌" in location_info and "우" in location_info:
                # 좌우 분포 → 2×2 그리드
                print("📊 좌우 분포 감지 → 2×2 그리드 사용")
                regions = self._create_overlap_grid(width, height, 2, 2)
                
            elif "상단" in location_info and "하단" in location_info:
                # 상하 분포 → 2×3 그리드
                print("📊 상하 분포 감지 → 2×3 그리드 사용")
                regions = self._create_overlap_grid(width, height, 3, 2)
                
            elif "중앙" in location_info:
                # 중앙 집중 → 중앙 강화 방식
                print("📊 중앙 집중 감지 → 중앙 강화 영역 사용")
                regions = self._create_center_focused_regions(width, height)
                
            else:
                # 기본값 → 2×2 그리드
                print("📊 기본 설정 → 2×2 그리드 사용")
                regions = self._create_overlap_grid(width, height, 2, 2)
            
            print(f"🔲 생성된 영역 수: {len(regions)}개")
            return regions
            
        except Exception as e:
            print(f"❌ 스마트 영역 생성 실패: {e}")
            return []
    
    def _create_overlap_grid(self, width, height, cols, rows, overlap=0.2):
        """오버랩이 있는 그리드 생성"""
        regions = []
        
        grid_width = width // cols
        grid_height = height // rows
        overlap_w = int(grid_width * overlap)
        overlap_h = int(grid_height * overlap)
        
        for row in range(rows):
            for col in range(cols):
                x1 = max(0, col * grid_width - overlap_w)
                y1 = max(0, row * grid_height - overlap_h)
                x2 = min(width, (col + 1) * grid_width + overlap_w)
                y2 = min(height, (row + 1) * grid_height + overlap_h)
                
                regions.append({
                    'bbox': (x1, y1, x2, y2),
                    'name': f"그리드_{row}_{col}",
                    'priority': 1
                })
        
        return regions
    
    def _create_center_focused_regions(self, width, height):
        """중앙 강화 영역 생성"""
        regions = []
        
        # 중앙 영역 (큰 영역)
        center_w = width * 0.6
        center_h = height * 0.6
        center_x = (width - center_w) // 2
        center_y = (height - center_h) // 2
        
        regions.append({
            'bbox': (int(center_x), int(center_y), int(center_x + center_w), int(center_y + center_h)),
            'name': "중앙_메인",
            'priority': 1
        })
        
        # 코너 영역들
        corner_size = 0.4
        corners = [
            (0, 0, width * corner_size, height * corner_size, "좌상단"),
            (width * (1-corner_size), 0, width, height * corner_size, "우상단"),
            (0, height * (1-corner_size), width * corner_size, height, "좌하단"),
            (width * (1-corner_size), height * (1-corner_size), width, height, "우하단")
        ]
        
        for x1, y1, x2, y2, name in corners:
            regions.append({
                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                'name': name,
                'priority': 2
            })
        
        return regions
    
    def process_smart_regions(self, image_path):
        """스마트 영역 처리 파이프라인"""
        print(f"🧠 스마트 영역 OCR 시작: {os.path.basename(image_path)}")
        
        # 1단계: AI로 원형 위치 분석
        location_info = self.find_circle_regions_with_ai(image_path)
        
        # 2단계: 분석 결과를 바탕으로 영역 생성
        regions = self.create_smart_regions(image_path, location_info)
        
        if not regions:
            print("❌ 영역 생성 실패")
            return None
        
        # 3단계: 각 영역 처리
        from PIL import Image
        from cloud_ocr import CloudOCRProcessor
        
        img = Image.open(image_path)
        processor = CloudOCRProcessor(self.api_key, self.model_name)
        
        all_results = []
        successful_regions = 0
        
        # 우선순위별로 처리
        regions.sort(key=lambda x: x['priority'])
        
        for i, region in enumerate(regions):
            x1, y1, x2, y2 = region['bbox']
            name = region['name']
            
            print(f"🤖 {name} 영역 처리 중... ({x1},{y1})→({x2},{y2})")
            
            try:
                # 영역 크롭
                cropped = img.crop((x1, y1, x2, y2))
                
                # 임시 저장
                os.makedirs("output/smart_regions", exist_ok=True)
                temp_path = f"output/smart_regions/{name}.png"
                cropped.save(temp_path)
                
                # AI 처리 - process_image 대신 직접 처리하여 tuple 문제 해결
                result = self._process_region_directly(temp_path, processor)
                
                if result and len(result.strip()) > 5:
                    # 중복 제거 (이전 결과와 비교)
                    if not any(result.strip() in existing for existing in all_results):
                        all_results.append(result.strip())
                        successful_regions += 1
                        print(f"✅ {name}: '{result.strip()[:30]}...'")
                    else:
                        print(f"🔄 {name}: 중복 결과 제외")
                else:
                    print(f"❌ {name}: 텍스트 없음")
                    
            except Exception as e:
                print(f"❌ {name} 처리 오류: {e}")
                continue
        
        # 결과 통합
        if all_results:
            final_result = "\n".join(all_results)
            
            print(f"\n🎉 스마트 영역 처리 완료:")
            print(f"   성공 영역: {successful_regions}/{len(regions)}개")
            print(f"   고유 텍스트: {len(all_results)}개")
            print(f"   총 길이: {len(final_result)}자")
            
            return final_result
        else:
            print(f"\n⚠️  모든 영역에서 원형 텍스트 추출 실패")
            return None

    def _process_region_directly(self, image_path, processor):
        """영역을 직접 처리하여 tuple 문제 해결"""
        try:
            import base64
            
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
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
            
            import dashscope
            response = dashscope.MultiModalConversation.call(
                model=processor.model_name,
                messages=messages
            )
            
            # 응답 처리 - response_utils 사용
            from response_utils import extract_text_from_response
            result = extract_text_from_response(response)
            
            # 결과가 문자열인지 확인 (tuple 방지)
            if isinstance(result, tuple):
                result = result[0] if len(result) > 0 else "처리 실패"
            
            return result if result else "없음"
            
        except Exception as e:
            print(f"❌ 영역 처리 오류: {e}")
            return f"이미지 처리 중 오류: {e}"


def test_smart_region_ocr():
    """스마트 영역 OCR 테스트"""
    print("🧠 스마트 영역 OCR 테스트 (수정된 버전)")
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
        
        # 스마트 OCR 실행
        smart_ocr = SmartRegionOCR(api_key, "qwen-vl-plus")
        result = smart_ocr.process_smart_regions(test_image)
        
        if result:
            # 결과 저장
            os.makedirs("output", exist_ok=True)
            result_path = "output/smart_region_result_fixed.txt"
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write("=== 스마트 영역 OCR 결과 (수정된 버전) ===\n")
                f.write(f"방식: AI 위치 분석 → 적응적 영역 분할 → 세밀 처리\n")
                f.write(f"추출된 텍스트 길이: {len(result)}자\n\n")
                f.write("=== 추출된 텍스트 ===\n")
                f.write(result)
            
            print(f"💾 결과 저장: {result_path}")
            
            # 미리보기
            print(f"\n📄 추출된 텍스트:")
            lines = result.split('\n')
            for i, line in enumerate(lines):
                print(f"  {i+1}: {line}")
            
            return True
        else:
            print("❌ 스마트 영역 OCR 실패")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 실행 함수"""
    print("🚀 스마트 영역 분할 OCR 시스템 (수정된 버전)")
    print("💡 아이디어: AI가 먼저 원형 위치 파악 → 적응적 영역 분할")
    print("🔧 수정 사항: tuple 반환 값 문제 해결")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    success = test_smart_region_ocr()
    
    if success:
        print(f"\n" + "=" * 60)
        print("🎉 스마트 영역 OCR 성공!")
        print("✨ 장점:")
        print("   ✅ 무작정 자르지 않음")
        print("   ✅ AI가 먼저 위치 파악")
        print("   ✅ 적응적 영역 분할")
        print("   ✅ 중복 제거")
        print("   ✅ 우선순위 기반 처리")
        print("   ✅ tuple 오류 수정")
        
        print(f"\n📁 생성된 파일들:")
        print("   output/smart_regions/ - 각 영역별 이미지")
        print("   output/smart_region_result_fixed.txt - 최종 결과")
        
    else:
        print(f"\n💡 개선 방향:")
        print("   1. 위치 분석 프롬프트 개선")
        print("   2. 영역 분할 알고리즘 조정")
        print("   3. 네트워크 연결 확인")

if __name__ == "__main__":
    main()
