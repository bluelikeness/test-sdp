#!/usr/bin/env python3
"""
네트워크 연결 진단 도구
"""

import os
import sys
sys.path.append('src')

def test_network_connection():
    """네트워크 연결 테스트"""
    print("🌐 네트워크 연결 진단")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        import dashscope
        
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("❌ API 키가 설정되지 않음")
            return False
        
        print(f"🔑 API 키: {'*' * (len(api_key) - 8) + api_key[-8:]}")
        
        # 기본 설정
        dashscope.api_key = api_key
        
        # 간단한 텍스트 요청으로 연결 테스트
        print("📡 기본 연결 테스트...")
        
        messages = [{"role": "user", "content": "Hello"}]
        
        response = dashscope.Generation.call(
            model="qwen-plus",
            messages=messages
        )
        
        if response and response.status_code == 200:
            print("✅ 기본 API 연결 성공")
            return True
        else:
            print(f"❌ 기본 API 연결 실패: {response}")
            return False
            
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

def test_advanced_network():
    """고급 네트워크 설정 테스트"""
    print(f"\n🔧 고급 네트워크 설정 테스트")
    print("=" * 60)
    
    try:
        from cloud_ocr import CloudOCRProcessor
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        print("🛠️  고급 SSL 설정 적용...")
        
        # CloudOCRProcessor 생성 (고급 네트워크 설정 포함)
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        
        # 더미 이미지로 연결 테스트
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print("❌ 테스트 이미지 없음")
            return False
        
        print("📡 멀티모달 API 연결 테스트...")
        
        # 단일 이미지 처리로 연결 테스트
        result = processor.process_image(test_image, "general")
        
        if result and not result.startswith("처리 실패"):
            print("✅ 고급 네트워크 설정으로 연결 성공")
            print(f"📝 응답 길이: {len(result)}자")
            return True
        else:
            print(f"❌ 고급 네트워크 설정으로도 실패: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 고급 네트워크 테스트 실패: {e}")
        return False

def main():
    """메인 진단 함수"""
    print("🔍 네트워크 연결 종합 진단")
    print("🎯 목표: SSL 오류 원인 파악")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    # 1단계: 기본 연결 테스트
    basic_success = test_network_connection()
    
    # 2단계: 고급 설정 테스트
    if basic_success:
        advanced_success = test_advanced_network()
    else:
        print("⚠️  기본 연결 실패로 고급 테스트 건너뜀")
        advanced_success = False
    
    # 결과 및 권장사항
    print(f"\n" + "=" * 60)
    print("📊 진단 결과:")
    print(f"   기본 연결: {'✅ 성공' if basic_success else '❌ 실패'}")
    print(f"   고급 설정: {'✅ 성공' if advanced_success else '❌ 실패'}")
    
    if advanced_success:
        print(f"\n🎉 네트워크 연결 정상!")
        print("💡 권장 사용법:")
        print("   python test_grid_fixed.py")
        print("   또는")
        print("   python src/main.py → 하이브리드 모드")
        
    elif basic_success:
        print(f"\n⚠️  기본 연결은 되지만 멀티모달 API에 문제")
        print("💡 해결책:")
        print("   1. 잠시 후 재시도")
        print("   2. 다른 모델 사용")
        print("   3. API 사용량 확인")
        
    else:
        print(f"\n❌ 네트워크 연결 문제")
        print("💡 해결책:")
        print("   1. 인터넷 연결 확인")
        print("   2. API 키 확인")
        print("   3. VPN 사용 시 비활성화")
        print("   4. 방화벽 설정 확인")

if __name__ == "__main__":
    main()
