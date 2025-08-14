"""
국제 엔드포인트 설정을 위한 dashscope 패치
"""

import os
import dashscope

def configure_international_endpoint():
    """국제 엔드포인트로 dashscope 설정"""
    try:
        base_url = os.getenv('QWEN_API_BASE_URL', 'https://dashscope-intl.aliyuncs.com/api/v1')
        
        if 'dashscope-intl' in base_url:
            # 국제 엔드포인트 설정
            print("🌍 국제 엔드포인트 설정 중...")
            
            # 방법 1: constants 모듈 수정
            try:
                import dashscope.utils.constants as constants
                constants.DASHSCOPE_BASE_HTTP_API_URL = 'https://dashscope-intl.aliyuncs.com/api/v1'
                print("✅ Constants 모듈 설정 완료")
            except:
                pass
            
            # 방법 2: 환경 변수 설정
            os.environ['DASHSCOPE_BASE_URL'] = 'https://dashscope-intl.aliyuncs.com/api/v1'
            
            # 방법 3: dashscope 내부 설정 직접 수정
            try:
                if hasattr(dashscope, 'base_http_api_url'):
                    dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
                    print("✅ Base URL 직접 설정 완료")
            except:
                pass
            
            # 방법 4: 모든 관련 모듈에 적용
            try:
                import dashscope.aigc.multimodal_conversation as mmc
                if hasattr(mmc, 'base_url'):
                    mmc.base_url = 'https://dashscope-intl.aliyuncs.com'
            except:
                pass
                
            print("✅ 국제 엔드포인트 설정 완료")
            return True
        else:
            print("🇨🇳 중국 내수용 엔드포인트 사용")
            return True
            
    except Exception as e:
        print(f"⚠️  엔드포인트 설정 오류: {e}")
        return False

def test_endpoint_connection():
    """엔드포인트 연결 테스트"""
    import requests
    from network_advanced import create_permissive_session
    
    endpoints = [
        'https://dashscope-intl.aliyuncs.com',
        'https://dashscope.aliyuncs.com'
    ]
    
    session = create_permissive_session()
    
    print("🔍 엔드포인트 연결 테스트...")
    
    for endpoint in endpoints:
        try:
            response = session.head(endpoint, timeout=10)
            print(f"✅ {endpoint} - 연결 가능 ({response.status_code})")
            return endpoint
        except Exception as e:
            print(f"❌ {endpoint} - 연결 실패: {str(e)[:50]}...")
    
    return None

if __name__ == "__main__":
    print("🔧 DashScope 엔드포인트 설정 테스트")
    print("=" * 40)
    
    # 연결 테스트
    working_endpoint = test_endpoint_connection()
    
    # 설정 적용
    configure_international_endpoint()
    
    if working_endpoint:
        print(f"\n✅ 사용 가능한 엔드포인트: {working_endpoint}")
    else:
        print("\n❌ 사용 가능한 엔드포인트가 없습니다.")
