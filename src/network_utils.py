"""
네트워크 연결 문제 해결을 위한 유틸리티
"""

import os
import ssl
import certifi
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def configure_ssl():
    """SSL 설정 최적화"""
    try:
        # 인증서 경로 설정
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        os.environ['SSL_CERT_FILE'] = certifi.where()
        
        # SSL 컨텍스트 설정
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        return True
    except Exception as e:
        print(f"SSL 설정 중 오류: {e}")
        return False

def create_robust_session():
    """안정적인 HTTP 세션 생성"""
    session = requests.Session()
    
    # 재시도 전략
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 523, 524],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    # 어댑터 설정
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 헤더 설정
    session.headers.update({
        'User-Agent': 'OCR-Test-Tool/1.0',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate'
    })
    
    # 타임아웃 설정
    session.timeout = (10, 30)  # (연결 타임아웃, 읽기 타임아웃)
    
    return session

def test_network_connectivity():
    """네트워크 연결 상태 테스트"""
    test_urls = [
        "https://www.google.com",
        "https://dashscope.aliyuncs.com"
    ]
    
    session = create_robust_session()
    
    for url in test_urls:
        try:
            response = session.head(url, timeout=5)
            print(f"✅ {url} - 연결 가능 ({response.status_code})")
        except Exception as e:
            print(f"❌ {url} - 연결 실패: {str(e)[:50]}...")
            return False
    
    return True

if __name__ == "__main__":
    print("=== 네트워크 연결 테스트 ===")
    configure_ssl()
    test_network_connectivity()
