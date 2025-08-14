#!/usr/bin/env python3
"""
튜플 문제 디버깅 스크립트
"""

import os
import sys

# src 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

def debug_tuple_issue():
    """튜플 문제 디버깅"""
    print("🔍 튜플 문제 디버깅")
    print("=" * 40)
    
    try:
        # 1. 환경 설정 확인
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("❌ API 키가 설정되지 않음")
            return False
            
        print("✅ API 키 확인")
        
        # 2. CloudOCRProcessor import 및 객체 생성
        from cloud_ocr import CloudOCRProcessor
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        
        print("✅ CloudOCRProcessor 생성")
        
        # 3. 테스트 이미지 확인
        test_image = "input/17301.png"
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return False
            
        print("✅ 테스트 이미지 확인")
        
        # 4. process_image 호출 및 반환값 타입 확인
        print("🔬 process_image 호출...")
        result = processor.process_image(test_image, "shape_detection")
        
        print(f"📊 반환값 타입: {type(result)}")
        print(f"📊 반환값 내용: {str(result)[:100]}...")
        
        if isinstance(result, tuple):
            print(f"🔍 튜플 길이: {len(result)}")
            for i, item in enumerate(result):
                print(f"  [{i}] {type(item)}: {str(item)[:50]}...")
                
            # 튜플에서 텍스트 추출
            if len(result) >= 2:
                text_result = result[0]
                time_result = result[1]
                print(f"✅ 텍스트 결과: {type(text_result)}")
                print(f"✅ 시간 결과: {type(time_result)}")
                
                if isinstance(text_result, str):
                    print(f"✅ 문자열 strip() 테스트: '{text_result.strip()[:30]}...'")
                    return True
                else:
                    print(f"❌ 텍스트가 문자열이 아님: {type(text_result)}")
                    return False
            else:
                print("❌ 튜플 길이가 예상과 다름")
                return False
        else:
            print(f"✅ 튜플이 아님: {type(result)}")
            if isinstance(result, str):
                print(f"✅ 문자열 strip() 테스트: '{result.strip()[:30]}...'")
                return True
            else:
                print(f"❌ 반환값이 문자열이 아님")
                return False
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_tuple_issue()
