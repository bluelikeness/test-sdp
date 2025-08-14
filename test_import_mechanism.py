#!/usr/bin/env python3
"""
모듈 탐색 경로 실험
"""

import sys
import os

def show_module_search_paths():
    """Python이 모듈을 찾는 경로들 보기"""
    print("🔍 Python 모듈 탐색 경로:")
    print("=" * 50)
    
    for i, path in enumerate(sys.path):
        print(f"{i}: {path}")
    
    print(f"\n📁 현재 작업 디렉토리: {os.getcwd()}")
    print(f"📄 현재 실행 파일: {__file__}")

def test_import():
    """import 테스트"""
    print(f"\n🧪 Import 테스트:")
    print("=" * 30)
    
    try:
        # 현재 폴더의 파일 import 시도
        import web_region_selector
        print("✅ web_region_selector import 성공")
        
        # 모듈의 위치 확인
        print(f"📍 모듈 위치: {web_region_selector.__file__}")
        
    except ImportError as e:
        print(f"❌ import 실패: {e}")
    
    try:
        # main 함수가 있는지 확인
        from web_region_selector import main
        print("✅ main 함수 import 성공")
        print(f"📋 함수 타입: {type(main)}")
        
    except ImportError as e:
        print(f"❌ main 함수 import 실패: {e}")

def test_different_folder():
    """다른 폴더에서 실행했을 때 어떻게 되는지 테스트"""
    print(f"\n🗂️ 다른 폴더 테스트:")
    print("=" * 30)
    
    # 상위 폴더로 이동
    original_dir = os.getcwd()
    parent_dir = os.path.dirname(original_dir)
    
    try:
        os.chdir(parent_dir)
        print(f"📁 폴더 변경: {os.getcwd()}")
        
        # 이제 web_region_selector를 import 해보기
        import importlib
        try:
            # 이전에 import된 모듈 제거
            if 'web_region_selector' in sys.modules:
                del sys.modules['web_region_selector']
                
            import web_region_selector
            print("✅ 상위 폴더에서도 import 성공 (캐시된 모듈)")
        except ImportError:
            print("❌ 상위 폴더에서는 import 실패")
            
    finally:
        # 원래 폴더로 돌아가기
        os.chdir(original_dir)

if __name__ == "__main__":
    print("🐍 Python 모듈 Import 메커니즘 실험")
    print("=" * 60)
    
    show_module_search_paths()
    test_import()
    test_different_folder()
