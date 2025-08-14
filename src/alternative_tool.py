#!/usr/bin/env python3
"""
네트워크 문제가 있을 때 사용할 수 있는 대안 도구
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

def show_network_troubleshooting():
    """네트워크 문제 해결 가이드"""
    print("🔧 네트워크 연결 문제 해결 가이드")
    print("=" * 50)
    
    print("\n📋 현재 상황:")
    print("- Qwen Cloud API 서버(dashscope.aliyuncs.com)에 연결할 수 없습니다")
    print("- 이는 지역적 네트워크 제한이나 방화벽 설정 때문일 수 있습니다")
    
    print("\n🔧 해결 방안:")
    print("1. 로컬 모델 사용 (권장)")
    print("   - GPU/CPU에서 직접 실행")
    print("   - 네트워크 연결 불필요")
    print("   - python src/main.py 실행 후 '1. 로컬 모델 사용' 선택")
    
    print("\n2. 네트워크 환경 변경")
    print("   - 다른 인터넷 연결 시도")
    print("   - VPN 사용 (중국/아시아 서버)")
    print("   - 모바일 핫스팟 사용")
    
    print("\n3. 시스템 설정 확인")
    print("   - 방화벽 설정 확인")
    print("   - 프록시 설정 확인")
    print("   - DNS 설정 확인 (8.8.8.8 시도)")
    
    print("\n4. API 키 및 권한 확인")
    print("   - Qwen Cloud API 키가 유효한지 확인")
    print("   - 계정에 충분한 크레딧이 있는지 확인")
    
    print("\n📞 추가 도움말:")
    print("- 로컬 모델은 더 느리지만 안정적입니다")
    print("- 2B 모델이 가장 빠르고, 3B 모델이 균형이 좋습니다")
    print("- CPU 모드도 지원되므로 GPU가 없어도 사용 가능합니다")

def run_local_only_mode():
    """로컬 전용 모드 실행"""
    print("\n🖥️  로컬 전용 모드 시작")
    print("=" * 30)
    
    try:
        from local_ocr import LocalOCRProcessor
        from utils import get_image_files, create_output_directory
        from models import get_model_info
        
        # 기본 설정
        base_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(base_dir)
        input_dir = os.path.join(parent_dir, 'input')
        output_dir = os.path.join(parent_dir, 'output')
        
        # 이미지 파일 확인
        image_files = get_image_files(input_dir)
        print(f"📁 발견된 이미지: {len(image_files)}개")
        
        if not image_files:
            print("❌ input 폴더에 이미지가 없습니다.")
            return
        
        # 모델 선택
        print("\n🧠 사용할 모델을 선택하세요:")
        print("1. Qwen2-VL-2B (가장 빠름, 4GB GPU 필요)")
        print("2. Qwen2.5-VL-3B (균형, 6GB GPU 필요)")
        print("3. CPU 모드 (느리지만 안전)")
        
        choice = input("\n선택 (1-3): ").strip()
        
        if choice == "1":
            model_info = get_model_info("qwen2-vl-2b", "local")
            device = "auto"
        elif choice == "2":
            model_info = get_model_info("qwen2.5-vl-3b", "local")
            device = "auto"
        elif choice == "3":
            model_info = get_model_info("qwen2.5-vl-3b", "local")
            device = "cpu"
            print("⚠️  CPU 모드는 매우 느립니다. 시간이 오래 걸릴 수 있습니다.")
        else:
            print("❌ 잘못된 선택입니다.")
            return
        
        # 확인
        print(f"\n📊 처리할 이미지: {len(image_files)}개")
        print(f"🧠 모델: {model_info['name']}")
        print(f"💾 디바이스: {device}")
        
        confirm = input("\n처리를 시작하시겠습니까? (y/N): ").strip().lower()
        if confirm != 'y':
            print("처리가 취소되었습니다.")
            return
        
        # 처리 실행
        processor = LocalOCRProcessor(model_info["model_id"], device=device)
        
        try:
            # 모델 로드
            print(f"\n📦 모델 로딩 중...")
            success, load_time = processor.load_model()
            
            if not success:
                print("❌ 모델 로딩 실패")
                return
            
            print(f"✅ 모델 로딩 완료 ({load_time:.2f}초)")
            
            # 이미지 처리
            success = processor.process_images(image_files, output_dir)
            
            if success:
                print("\n✅ 모든 처리가 완료되었습니다!")
                print("📁 결과는 output 폴더에서 확인할 수 있습니다.")
            else:
                print("\n❌ 처리 중 오류가 발생했습니다.")
                
        finally:
            processor.cleanup()
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    while True:
        print("\n🔍 OCR 대안 도구")
        print("=" * 30)
        print("1. 네트워크 문제 해결 가이드 보기")
        print("2. 로컬 전용 모드 실행")
        print("3. 네트워크 진단 실행")
        print("4. 종료")
        
        choice = input("\n선택하세요 (1-4): ").strip()
        
        if choice == "1":
            show_network_troubleshooting()
        elif choice == "2":
            run_local_only_mode()
        elif choice == "3":
            from network_advanced import run_comprehensive_test
            run_comprehensive_test()
        elif choice == "4":
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 1-4 사이의 숫자를 입력해주세요.")

if __name__ == "__main__":
    main()
