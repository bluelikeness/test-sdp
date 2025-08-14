#!/usr/bin/env python3
"""
스마트 영역 OCR 테스트 스크립트 (간단한 버전)
"""

import os
import sys
sys.path.append('src')

def quick_test():
    """빠른 테스트"""
    print("🔧 Smart Region OCR 빠른 테스트")
    print("=" * 50)
    
    try:
        # 1. 환경 확인
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("❌ API 키가 설정되지 않음")
            return False
        
        print("✅ API 키 확인됨")
        
        # 2. 테스트 이미지 확인
        test_image = "input/17301.png"
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return False
        
        print("✅ 테스트 이미지 확인됨")
        
        # 3. SmartRegionOCR 클래스 import 테스트
        from smart_region_ocr import SmartRegionOCR
        print("✅ SmartRegionOCR 클래스 import 성공")
        
        # 4. 객체 생성 테스트
        smart_ocr = SmartRegionOCR(api_key, "qwen-vl-plus")
        print("✅ SmartRegionOCR 객체 생성 성공")
        
        # 5. _process_region_directly 메서드 존재 확인
        if hasattr(smart_ocr, '_process_region_directly'):
            print("✅ _process_region_directly 메서드 확인됨")
        else:
            print("❌ _process_region_directly 메서드 없음")
            return False
        
        # 6. 위치 분석만 테스트
        print("\n🔍 위치 분석 테스트 시작...")
        location_info = smart_ocr.find_circle_regions_with_ai(test_image)
        print(f"📍 분석 결과: {location_info}")
        
        if location_info and location_info != "분석 실패":
            print("✅ 위치 분석 성공")
            
            # 7. 영역 생성 테스트
            print("\n🔲 영역 생성 테스트...")
            regions = smart_ocr.create_smart_regions(test_image, location_info)
            print(f"📊 생성된 영역 수: {len(regions)}")
            
            if len(regions) > 0:
                print("✅ 영역 생성 성공")
                
                # 첫 번째 영역만 테스트
                print(f"\n🤖 첫 번째 영역 테스트...")
                from PIL import Image
                from cloud_ocr import CloudOCRProcessor
                
                img = Image.open(test_image)
                processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
                
                region = regions[0]
                x1, y1, x2, y2 = region['bbox']
                name = region['name']
                
                print(f"📍 테스트 영역: {name} ({x1},{y1})→({x2},{y2})")
                
                # 영역 크롭 및 저장
                cropped = img.crop((x1, y1, x2, y2))
                os.makedirs("output/smart_regions", exist_ok=True)
                temp_path = f"output/smart_regions/{name}_test.png"
                cropped.save(temp_path)
                print(f"💾 테스트 영역 저장: {temp_path}")
                
                # 새로운 메서드로 처리
                result = smart_ocr._process_region_directly(temp_path, processor)
                print(f"📝 처리 결과: {result}")
                
                if isinstance(result, str):
                    print("✅ tuple 문제 해결됨 - 문자열 반환")
                    return True
                else:
                    print(f"❌ 여전히 tuple 문제: {type(result)}")
                    return False
            else:
                print("❌ 영역 생성 실패")
                return False
        else:
            print("❌ 위치 분석 실패")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            exit(1)
    
    success = quick_test()
    
    if success:
        print(f"\n" + "=" * 50)
        print("🎉 빠른 테스트 성공!")
        print("🚀 이제 전체 smart_region_ocr.py를 실행할 수 있습니다.")
    else:
        print(f"\n" + "=" * 50)
        print("❌ 빠른 테스트 실패")
        print("🔧 문제를 해결한 후 다시 시도해주세요.")
