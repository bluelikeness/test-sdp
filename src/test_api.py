#!/usr/bin/env python3
"""
네트워크 및 API 연결 테스트
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

def test_api_connection():
    """API 연결 테스트"""
    print("🔗 Qwen Cloud API 연결 테스트")
    print("=" * 40)
    
    api_key = os.getenv('QWEN_API_KEY')
    
    if not api_key or api_key == "your_api_key_here":
        print("❌ API 키가 설정되지 않았습니다.")
        print("   .env 파일에서 QWEN_API_KEY를 설정해주세요.")
        return False
    
    print(f"🔑 API 키: ...{api_key[-8:]}")
    
    # 네트워크 연결 테스트
    from network_utils import test_network_connectivity
    print("\n📡 네트워크 연결 테스트...")
    if not test_network_connectivity():
        print("❌ 네트워크 연결에 문제가 있습니다.")
        return False
    
    # 간단한 API 테스트
    try:
        import dashscope
        from network_utils import configure_ssl
        
        configure_ssl()
        dashscope.api_key = api_key
        
        print("\n🧪 API 테스트 중...")
        
        # 간단한 텍스트 모델로 테스트
        response = dashscope.Generation.call(
            model='qwen-turbo',
            prompt='Hello',
            max_tokens=10
        )
        
        if response.status_code == 200:
            print("✅ API 연결 성공!")
            return True
        else:
            print(f"❌ API 연결 실패: {response.code} - {response.message}")
            return False
            
    except ImportError:
        print("❌ dashscope 모듈이 설치되지 않았습니다.")
        return False
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")
        return False

def main():
    """메인 함수"""
    success = test_api_connection()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ 모든 테스트 통과! Cloud API를 사용할 수 있습니다.")
    else:
        print("❌ 테스트 실패. 설정을 확인해주세요.")
        print("\n해결 방법:")
        print("1. .env 파일에 올바른 QWEN_API_KEY 설정")
        print("2. 네트워크 연결 확인")
        print("3. 방화벽 설정 확인")

if __name__ == "__main__":
    main()
