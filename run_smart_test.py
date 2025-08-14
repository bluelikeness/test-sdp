#!/usr/bin/env python3
"""
Smart Region OCR 테스트 실행기
"""

import os
import sys

def run_test():
    """테스트 실행"""
    print("🧪 Smart Region OCR 실행 테스트")
    print("=" * 50)
    
    # 현재 디렉토리 확인 및 이동
    current_dir = os.getcwd()
    print(f"현재 디렉토리: {current_dir}")
    
    if not current_dir.endswith('test-sdp'):
        test_sdp_path = '\\\\wsl.localhost\\Udev\\home\\kckang\\work\\test-sdp'
        if os.path.exists(test_sdp_path):
            os.chdir(test_sdp_path)
            print(f"디렉토리 변경: {test_sdp_path}")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return False
    
    # Python 경로에 src 추가
    src_path = os.path.join(os.getcwd(), 'src')
    if src_path not in sys.path:
        sys.path.append(src_path)
    
    try:
        # smart_region_ocr 모듈 import
        from smart_region_ocr import test_smart_region_ocr
        
        print("✅ 모듈 import 성공")
        print("🚀 테스트 시작...")
        
        # 테스트 실행
        success = test_smart_region_ocr()
        
        if success:
            print("\n🎉 테스트 성공!")
            return True
        else:
            print("\n❌ 테스트 실패")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    run_test()
