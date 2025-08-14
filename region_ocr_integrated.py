#!/usr/bin/env python3
"""
영역 선택 + OCR 통합 도구
UI로 영역을 선택한 후 바로 OCR 처리
"""

import os
import sys
import json
from datetime import datetime

sys.path.append('src')

class RegionOCRProcessor:
    """영역 선택 후 OCR 처리를 통합하는 클래스"""
    
    def __init__(self, api_key, model_name="qwen-vl-plus"):
        self.api_key = api_key
        self.model_name = model_name
        
    def select_regions_and_process(self, image_path):
        """영역 선택 후 OCR 처리"""
        print("🖼️  영역 선택 + OCR 통합 처리")
        print("=" * 50)
        
        # 1단계: UI로 영역 선택
        print("1️⃣ 영역 선택 단계")
        from region_selector_ui import RegionSelector
        
        selector = RegionSelector(image_path)
        selector.run()
        
        if not selector.regions:
            print("❌ 선택된 영역이 없습니다.")
            return False
        
        print(f"✅ {len(selector.regions)}개 영역 선택 완료")
        
        # 2단계: 영역 크롭
        print("\n2️⃣ 영역 크롭 단계")
        success = selector.crop_regions()
        
        if not success:
            print("❌ 영역 크롭 실패")
            return False
        
        # 3단계: OCR 처리
        print("\n3️⃣ OCR 처리 단계")
        return self.process_cropped_regions(selector)
    
    def process_cropped_regions(self, selector):
        """크롭된 영역들을 OCR 처리"""
        try:
            from cloud_ocr import CloudOCRProcessor
            
            # OCR 프로세서 초기화
            ocr_processor = CloudOCRProcessor(self.api_key, self.model_name)
            
            # 출력 디렉토리
            output_dir = "output/cropped_regions"
            
            results = []
            successful_count = 0
            
            for region in selector.regions:
                region_name = region['name']
                print(f"\n🤖 {region_name} OCR 처리 중...")
                
                # 크롭된 이미지 파일 찾기
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.splitext(os.path.basename(selector.image_path))[0]
                
                # 가장 최근 파일 찾기
                import glob
                pattern = os.path.join(output_dir, f"{base_name}_{region_name}_*.png")
                cropped_files = glob.glob(pattern)
                
                if not cropped_files:
                    print(f"❌ 크롭된 파일을 찾을 수 없음: {region_name}")
                    continue
                
                # 가장 최근 파일 선택
                cropped_file = max(cropped_files, key=os.path.getctime)
                
                try:
                    # OCR 처리 (tuple 처리 포함)
                    result_tuple = ocr_processor.process_image(cropped_file, "shape_detection")
                    
                    # measure_time 데코레이터 때문에 tuple이 반환될 수 있음
                    if isinstance(result_tuple, tuple) and len(result_tuple) == 2:
                        result_text, process_time = result_tuple
                    else:
                        result_text = result_tuple
                        process_time = 0
                    
                    if result_text and len(result_text.strip()) > 3:
                        # "없음" 같은 응답 필터링
                        if result_text.lower() not in ['없음', 'none', 'no text', 'no circles']:
                            results.append({
                                'region': region_name,
                                'coordinates': region['original_coords'],
                                'size': f"{region['width']}×{region['height']}",
                                'text': result_text.strip(),
                                'file': os.path.basename(cropped_file),
                                'process_time': process_time
                            })
                            successful_count += 1
                            print(f"✅ 텍스트 추출: '{result_text.strip()[:50]}...'")
                        else:
                            print(f"❌ 의미있는 텍스트 없음")
                    else:
                        print(f"❌ 텍스트 추출 실패")
                        
                except Exception as e:
                    print(f"❌ OCR 처리 오류: {e}")
                    continue
            
            # 결과 저장
            if results:
                self.save_ocr_results(results, selector.image_path, output_dir)
                
                print(f"\n🎉 OCR 처리 완료!")
                print(f"📊 총 {len(selector.regions)}개 영역 중 {successful_count}개에서 텍스트 추출")
                
                return True
            else:
                print(f"\n⚠️  모든 영역에서 텍스트 추출 실패")
                return False
                
        except Exception as e:
            print(f"❌ OCR 처리 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_ocr_results(self, results, original_image_path, output_dir):
        """OCR 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(original_image_path))[0]
        
        # 텍스트 결과 파일
        txt_file = os.path.join(output_dir, f"{base_name}_ocr_results_{timestamp}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=== 영역별 OCR 결과 ===\n")
            f.write(f"원본 이미지: {original_image_path}\n")
            f.write(f"처리 시간: {timestamp}\n")
            f.write(f"추출된 영역: {len(results)}개\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"--- {result['region']} ---\n")
                f.write(f"좌표: {result['coordinates']}\n")
                f.write(f"크기: {result['size']}\n")
                f.write(f"파일: {result['file']}\n")
                f.write(f"추출 텍스트:\n{result['text']}\n\n")
        
        # JSON 결과 파일
        json_file = os.path.join(output_dir, f"{base_name}_ocr_results_{timestamp}.json")
        result_data = {
            'original_image': original_image_path,
            'timestamp': timestamp,
            'total_regions': len(results),
            'results': results
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        # 통합 텍스트 파일 (모든 텍스트만)
        all_text_file = os.path.join(output_dir, f"{base_name}_all_text_{timestamp}.txt")
        with open(all_text_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(result['text'] + '\n')
        
        print(f"💾 결과 저장:")
        print(f"   📄 상세 결과: {os.path.basename(txt_file)}")
        print(f"   📋 JSON 데이터: {os.path.basename(json_file)}")
        print(f"   📝 통합 텍스트: {os.path.basename(all_text_file)}")
    
    def process_existing_regions(self, regions_json_file):
        """기존에 저장된 영역 정보로 OCR 처리"""
        print("📋 기존 영역 정보로 OCR 처리")
        print("=" * 50)
        
        try:
            with open(regions_json_file, 'r', encoding='utf-8') as f:
                region_data = json.load(f)
            
            original_image = region_data['original_image']
            regions = region_data['regions']
            
            print(f"📸 원본 이미지: {os.path.basename(original_image)}")
            print(f"🔲 저장된 영역: {len(regions)}개")
            
            if not os.path.exists(original_image):
                print(f"❌ 원본 이미지를 찾을 수 없습니다: {original_image}")
                return False
            
            # 영역들을 다시 크롭
            import cv2
            original_img = cv2.imread(original_image)
            
            output_dir = "output/cropped_regions"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(original_image))[0]
            
            # 각 영역 크롭
            for region in regions:
                x1, y1, x2, y2 = region['original_coords']
                cropped = original_img[y1:y2, x1:x2]
                
                filename = f"{base_name}_{region['name']}_{timestamp}.png"
                filepath = os.path.join(output_dir, filename)
                cv2.imwrite(filepath, cropped)
                
                print(f"💾 {region['name']} 크롭 완료")
            
            # OCR 처리를 위한 가짜 selector 객체 생성
            class FakeSelector:
                def __init__(self, image_path, regions):
                    self.image_path = image_path
                    self.regions = regions
            
            fake_selector = FakeSelector(original_image, regions)
            return self.process_cropped_regions(fake_selector)
            
        except Exception as e:
            print(f"❌ 기존 영역 처리 실패: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """메인 함수"""
    print("🖼️🤖 영역 선택 + OCR 통합 도구")
    print("=" * 60)
    
    # 환경 설정 확인
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("❌ API 키가 설정되지 않았습니다.")
            print("   .env 파일에서 QWEN_API_KEY를 설정해주세요.")
            return
        
        print("✅ API 키 확인됨")
        
    except ImportError:
        print("❌ dotenv 모듈을 찾을 수 없습니다.")
        print("   pip install python-dotenv")
        return
    
    # 기본 테스트 이미지
    default_image = "input/17301.png"
    
    # 사용법 안내
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        # JSON 파일인 경우 기존 영역 처리
        if arg.endswith('.json'):
            if os.path.exists(arg):
                processor = RegionOCRProcessor(api_key, "qwen-vl-plus")
                processor.process_existing_regions(arg)
            else:
                print(f"❌ JSON 파일을 찾을 수 없습니다: {arg}")
            return
        else:
            image_path = arg
    else:
        image_path = default_image
    
    # 이미지 파일 확인
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        print(f"💡 사용법:")
        print(f"   새로운 영역 선택: python {sys.argv[0]} <이미지_경로>")
        print(f"   기존 영역 처리: python {sys.argv[0]} <regions.json>")
        return
    
    try:
        # 통합 처리 시작
        processor = RegionOCRProcessor(api_key, "qwen-vl-plus")
        success = processor.select_regions_and_process(image_path)
        
        if success:
            print(f"\n" + "=" * 60)
            print("🎉 영역 선택 + OCR 처리 완료!")
            print("📁 결과 파일들이 output/cropped_regions/ 폴더에 저장되었습니다.")
        else:
            print(f"\n" + "=" * 60)
            print("❌ 처리 중 문제가 발생했습니다.")
            
    except KeyboardInterrupt:
        print(f"\n👋 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
