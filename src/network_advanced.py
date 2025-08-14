"""
네트워크 연결 문제 해결을 위한 고급 설정
"""

import os
import requests
import urllib3
import ssl
import socket
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import certifi

# urllib3 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def configure_advanced_ssl():
    """고급 SSL/TLS 설정"""
    try:
        # 환경 변수 설정
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        os.environ['SSL_CERT_FILE'] = certifi.where()
        os.environ['CURL_CA_BUNDLE'] = certifi.where()
        
        # SSL 컨텍스트 생성
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')  # 보안 레벨 완화
        ssl_context.check_hostname = False  # 호스트명 검증 비활성화
        ssl_context.verify_mode = ssl.CERT_NONE  # 인증서 검증 비활성화 (임시)
        
        return ssl_context
    except Exception as e:
        print(f"SSL 설정 오류: {e}")
        return None

def test_dns_resolution():
    """DNS 해결 테스트"""
    hostnames = [
        'dashscope.aliyuncs.com',
        'google.com',
        '8.8.8.8'
    ]
    
    print("🔍 DNS 해결 테스트...")
    for hostname in hostnames:
        try:
            ip = socket.gethostbyname(hostname)
            print(f"✅ {hostname} -> {ip}")
        except Exception as e:
            print(f"❌ {hostname} -> 실패: {e}")

def test_direct_connection():
    """직접 연결 테스트"""
    host = 'dashscope.aliyuncs.com'
    port = 443
    
    try:
        print(f"🔌 {host}:{port} 직접 연결 테스트...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ {host}:{port} 연결 성공")
            return True
        else:
            print(f"❌ {host}:{port} 연결 실패 (오류 코드: {result})")
            return False
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

def create_permissive_session():
    """관대한 HTTP 세션 생성 (연결 문제 해결용)"""
    session = requests.Session()
    
    # 매우 관대한 재시도 전략
    retry_strategy = Retry(
        total=10,  # 총 재시도 횟수 증가
        backoff_factor=3,  # 백오프 시간 증가
        status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 523, 524],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        respect_retry_after_header=False
    )
    
    # 커스텀 어댑터
    class PermissiveHTTPAdapter(HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            kwargs['ssl_context'] = configure_advanced_ssl()
            kwargs['cert_reqs'] = 'CERT_NONE'
            kwargs['check_hostname'] = False
            return super().init_poolmanager(*args, **kwargs)
    
    adapter = PermissiveHTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=20,
        pool_maxsize=20
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 관대한 헤더 설정
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9,zh;q=0.8',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    })
    
    # 타임아웃 증가
    session.timeout = (30, 60)  # (연결, 읽기)
    
    # SSL 검증 비활성화 (임시)
    session.verify = False
    
    return session

def test_api_with_proxy():
    """프록시 없이 API 테스트"""
    print("🧪 API 연결 테스트 (고급 설정)...")
    
    session = create_permissive_session()
    
    # 간단한 GET 요청으로 테스트
    test_url = "https://dashscope.aliyuncs.com"
    
    try:
        response = session.get(test_url, timeout=30)
        print(f"✅ 기본 연결 성공: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ 연결 실패: {str(e)[:100]}...")
        return False

def suggest_alternatives():
    """대안 제시"""
    print("\n🔧 네트워크 문제 해결 방안:")
    print("1. VPN 사용 (중국 서버 접근)")
    print("2. 다른 네트워크 환경에서 시도")
    print("3. 방화벽/보안 소프트웨어 확인")
    print("4. 로컬 모델만 사용")
    print("5. API 키 및 권한 확인")
    
    print("\n🌐 네트워크 환경 정보:")
    print("- 현재 위치에서 중국 서버 접근이 제한될 수 있습니다")
    print("- dashscope.aliyuncs.com은 알리바바 클라우드 서비스입니다")
    print("- 지역별 네트워크 정책에 따라 접근이 차단될 수 있습니다")

def run_comprehensive_test():
    """종합 테스트"""
    print("🔍 종합 네트워크 진단 시작")
    print("=" * 50)
    
    test_dns_resolution()
    print()
    
    test_direct_connection()
    print()
    
    test_api_with_proxy()
    print()
    
    suggest_alternatives()

if __name__ == "__main__":
    run_comprehensive_test()
