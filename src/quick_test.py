#!/usr/bin/env python3
"""
빠른 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

from utils import get_image_files
from local_ocr import LocalOCRProcessor

def quick_test():
    """빠른 테스트 실행"""
    print("🔍 빠른 OCR 테스트 시작")
    print("=" * 40)
    
    # 설정
    base_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(base_dir)
    input_dir = os.path.join(parent_dir, 'input')
    output_dir = os.path.join(parent_dir, 'output')
    
    # 이미지 파일 찾기
    image_files = get_image_files(input_dir)
    print(f"📁 발견된 이미지: {len(image_files)}개")
    
    if not image_files:
        print("❌ input 폴더에 이미지가 없습니다.")
        return
    
    # 첫 번째 이미지만 테스트
    test_image = image_files[0]
    print(f"🖼️  테스트 이미지: {os.path.basename(test_image)}")
    
    # 가장 작은 모델로 CPU 테스트
    model_id = "Qwen/Qwen2-VL-2B-Instruct"
    print(f"🧠 사용 모델: {model_id}")
    print("⚠️  CPU 모드로 실행 - 시간이 오래 걸릴 수 있습니다")
    
    processor = LocalOCRProcessor(model_id, device="cpu")
    
    try:
        # 모델 로드
        print("\n📦 모델 로딩 중...")
        success, load_time = processor.load_model()
        
        if not success:
            print("❌ 모델 로딩 실패")
            return
        
        print(f"✅ 모델 로딩 완료 ({load_time:.2f}초)")
        
        # 단일 이미지 처리
        print("\n🔍 이미지 처리 중...")
        result_text, process_time = processor.process_image(test_image)
        
        print(f"\n=== 결과 ===")
        print(f"처리 시간: {process_time:.2f}초")
        print(f"추출된 텍스트 길이: {len(result_text)}자")
        print(f"추출된 텍스트:")
        print("-" * 30)
        print(result_text)
        print("-" * 30)
        
        # 결과 저장
        from utils import save_text_result, create_output_directory
        test_output_dir = create_output_directory(output_dir, "quick_test")
        saved_file = save_text_result(result_text, test_output_dir, test_image)
        
        if saved_file:
            print(f"💾 결과 저장: {saved_file}")
        
        print("\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        processor.cleanup()

if __name__ == "__main__":
    quick_test()
