#!/usr/bin/env python3
"""
간단한 테스트 스크립트 - 문제 진단용
"""

import os
import sys
import traceback
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """필요한 모듈들이 정상적으로 import되는지 확인"""
    print("=== 모듈 Import 테스트 ===")
    
    modules_to_test = [
        'torch',
        'transformers', 
        'PIL',
        'cv2',
        'numpy',
        'tqdm',
        'psutil'
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module} - OK")
        except ImportError as e:
            print(f"❌ {module} - FAILED: {e}")
    
    print()

def test_gpu():
    """GPU 정보 확인"""
    print("=== GPU 테스트 ===")
    
    try:
        import torch
        print(f"PyTorch 버전: {torch.__version__}")
        print(f"CUDA 사용가능: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA 버전: {torch.version.cuda}")
            print(f"GPU 개수: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print()
    except Exception as e:
        print(f"GPU 테스트 실패: {e}")
        print()

def test_directories():
    """디렉토리 구조 확인"""
    print("=== 디렉토리 테스트 ===")
    
    base_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(base_dir)
    
    dirs_to_check = [
        os.path.join(parent_dir, 'input'),
        os.path.join(parent_dir, 'output')
    ]
    
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} - 존재")
            files = os.listdir(dir_path)
            print(f"   파일 수: {len(files)}")
            if files:
                for f in files[:3]:  # 최대 3개만 표시
                    print(f"   - {f}")
                if len(files) > 3:
                    print(f"   ... 외 {len(files) - 3}개")
        else:
            print(f"❌ {dir_path} - 없음")
    print()

def test_env_vars():
    """환경 변수 확인"""
    print("=== 환경 변수 테스트 ===")
    
    api_key = os.getenv('QWEN_API_KEY')
    if api_key:
        if api_key == 'your_api_key_here':
            print("⚠️  QWEN_API_KEY가 기본값으로 설정되어 있습니다")
        else:
            print(f"✅ QWEN_API_KEY 설정됨 (...{api_key[-8:]})")
    else:
        print("❌ QWEN_API_KEY가 설정되지 않았습니다")
    
    print()

def test_simple_image_processing():
    """간단한 이미지 처리 테스트"""
    print("=== 이미지 처리 테스트 ===")
    
    try:
        from utils import get_image_files, create_output_directory
        
        base_dir = os.path.dirname(__file__)
        input_dir = os.path.join(os.path.dirname(base_dir), 'input')
        output_dir = os.path.join(os.path.dirname(base_dir), 'output')
        
        # 이미지 파일 찾기
        image_files = get_image_files(input_dir)
        print(f"발견된 이미지 파일: {len(image_files)}개")
        
        if image_files:
            for img in image_files:
                print(f"  - {os.path.basename(img)}")
            
            # 테스트 출력 디렉토리 생성
            test_output_dir = create_output_directory(output_dir, "test")
            print(f"테스트 출력 디렉토리 생성: {test_output_dir}")
            
            # 간단한 텍스트 파일 생성 테스트
            from utils import save_text_result
            test_text = "이것은 테스트 텍스트입니다.\nOCR 결과 저장 테스트중..."
            test_file = save_text_result(test_text, test_output_dir, image_files[0])
            
            if test_file:
                print(f"✅ 텍스트 파일 저장 성공: {os.path.basename(test_file)}")
            else:
                print("❌ 텍스트 파일 저장 실패")
        else:
            print("⚠️  테스트할 이미지가 없습니다")
            
    except Exception as e:
        print(f"❌ 이미지 처리 테스트 실패: {e}")
        traceback.print_exc()
    
    print()

def main():
    """메인 테스트 함수"""
    print("🔍 OCR 테스트 도구 진단 스크립트")
    print("=" * 50)
    
    test_imports()
    test_gpu() 
    test_directories()
    test_env_vars()
    test_simple_image_processing()
    
    print("=" * 50)
    print("진단 완료! 문제가 있다면 위의 ❌ 항목들을 확인해주세요.")

if __name__ == "__main__":
    main()
