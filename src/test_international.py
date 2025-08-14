#!/usr/bin/env python3
"""
국제 엔드포인트 테스트
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

def test_international_endpoint():
    """국제 엔드포인트 테스트"""
    print("🌍 DashScope 국제 엔드포인트 테스트")
    print("=" * 50)
    
    # 엔드포인트 설정
    from endpoint_config import configure_international_endpoint, test_endpoint_connection
    
    # 연결 테스트
    working_endpoint = test_endpoint_connection()
    
    if not working_endpoint:
        print("❌ 엔드포인트 연결에 실패했습니다.")
        return False
    
    # 설정 적용
    configure_international_endpoint()
    
    # API 키 확인
    api_key = os.getenv('QWEN_API_KEY')
    if not api_key or api_key == "your_api_key_here":
        print("❌ API 키가 설정되지 않았습니다.")
        print("   .env 파일에서 QWEN_API_KEY를 설정해주세요.")
        return False
    
    print(f"🔑 API 키: ...{api_key[-8:]}")
    
    # Cloud OCR 테스트
    try:
        from cloud_ocr import CloudOCRProcessor
        from utils import get_image_files
        
        # 테스트 이미지 확인
        base_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(base_dir)
        input_dir = os.path.join(parent_dir, 'input')
        
        image_files = get_image_files(input_dir)
        
        if not image_files:
            print("❌ input 폴더에 테스트할 이미지가 없습니다.")
            return False
        
        test_image = image_files[0]
        print(f"🖼️  테스트 이미지: {os.path.basename(test_image)}")
        
        # Cloud OCR 프로세서 생성
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        
        # 단일 이미지 테스트
        print("\n🔍 이미지 처리 테스트 중...")
        result_text, process_time = processor.process_image(test_image)
        
        print(f"\n=== 결과 ===")
        print(f"처리 시간: {process_time:.2f}초")
        
        if result_text and not result_text.startswith("연결 실패") and not result_text.startswith("API 호출 실패"):
            print(f"✅ 성공! 추출된 텍스트 길이: {len(result_text)}자")
            print(f"추출된 텍스트:")
            print("-" * 30)
            print(result_text[:200] + ("..." if len(result_text) > 200 else ""))
            print("-" * 30)
            return True
        else:
            print(f"❌ 실패: {result_text}")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실행 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_full_cloud_test():
    """전체 클라우드 테스트 실행"""
    print("🌐 전체 클라우드 OCR 테스트")
    print("=" * 50)
    
    # 국제 엔드포인트 테스트
    if not test_international_endpoint():
        print("\n❌ 국제 엔드포인트 테스트 실패")
        return False
    
    # 전체 처리 테스트
    try:
        from cloud_ocr import run_cloud_ocr
        from utils import get_image_files
        
        api_key = os.getenv('QWEN_API_KEY')
        base_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(base_dir)
        input_dir = os.path.join(parent_dir, 'input')
        output_dir = os.path.join(parent_dir, 'output')
        
        image_files = get_image_files(input_dir)
        
        print(f"\n📊 전체 이미지 처리: {len(image_files)}개")
        confirm = input("전체 처리를 시작하시겠습니까? (y/N): ").strip().lower()
        
        if confirm == 'y':
            success = run_cloud_ocr(api_key, "qwen-vl-plus", image_files, output_dir)
            
            if success:
                print("\n✅ 전체 클라우드 OCR 처리 완료!")
            else:
                print("\n❌ 전체 처리 중 오류 발생")
            
            return success
        else:
            print("전체 처리가 취소되었습니다.")
            return True
            
    except Exception as e:
        print(f"❌ 전체 테스트 오류: {e}")
        return False

def main():
    """메인 함수"""
    while True:
        print("\n🌍 국제 엔드포인트 테스트 도구")
        print("=" * 40)
        print("1. 엔드포인트 연결 테스트")
        print("2. 단일 이미지 OCR 테스트")
        print("3. 전체 이미지 OCR 테스트")
        print("4. 종료")
        
        choice = input("\n선택하세요 (1-4): ").strip()
        
        if choice == "1":
            from endpoint_config import test_endpoint_connection
            test_endpoint_connection()
        elif choice == "2":
            test_international_endpoint()
        elif choice == "3":
            run_full_cloud_test()
        elif choice == "4":
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 1-4 사이의 숫자를 입력해주세요.")

if __name__ == "__main__":
    main()
