#!/usr/bin/env python3
"""
간단한 Cloud API 테스트 (응답 구조 확인용)
"""

import os
import sys
import json
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

def test_api_response():
    """API 응답 구조 확인"""
    print("🔍 Cloud API 응답 구조 테스트")
    print("=" * 40)
    
    # API 키 확인
    api_key = os.getenv('QWEN_API_KEY')
    if not api_key or api_key == "your_api_key_here":
        print("❌ API 키가 설정되지 않았습니다.")
        return
    
    # 국제 엔드포인트 설정
    from endpoint_config import configure_international_endpoint
    configure_international_endpoint()
    
    # 테스트 이미지 확인
    from utils import get_image_files
    base_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(base_dir)
    input_dir = os.path.join(parent_dir, 'input')
    
    image_files = get_image_files(input_dir)
    if not image_files:
        print("❌ 테스트할 이미지가 없습니다.")
        return
    
    test_image = image_files[0]
    print(f"🖼️  테스트 이미지: {os.path.basename(test_image)}")
    
    try:
        import dashscope
        import base64
        
        dashscope.api_key = api_key
        
        # 이미지 인코딩
        with open(test_image, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # API 호출
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{base64_image}"},
                    {"text": "이미지에서 모든 텍스트를 추출해주세요."}
                ]
            }
        ]
        
        print("\n📡 API 호출 중...")
        response = dashscope.MultiModalConversation.call(
            model="qwen-vl-plus",
            messages=messages
        )
        
        print(f"\n=== 응답 분석 ===")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API 호출 성공!")
            
            # 응답 구조 자세히 분석
            choice = response.output.choices[0]
            message = choice.message
            content = message.content
            
            print(f"\nResponse 타입: {type(response)}")
            print(f"Output 타입: {type(response.output)}")
            print(f"Choices 타입: {type(response.output.choices)}")
            print(f"Choice 타입: {type(choice)}")
            print(f"Message 타입: {type(message)}")
            print(f"Content 타입: {type(content)}")
            
            print(f"\n=== Content 상세 분석 ===")
            if isinstance(content, list):
                print(f"Content는 리스트입니다 (길이: {len(content)})")
                for i, item in enumerate(content):
                    print(f"  [{i}] 타입: {type(item)}")
                    if isinstance(item, dict):
                        print(f"      키들: {list(item.keys())}")
                        for key, value in item.items():
                            print(f"      {key}: {type(value)} = {str(value)[:100]}...")
                    else:
                        print(f"      값: {str(item)[:100]}...")
            elif isinstance(content, str):
                print(f"Content는 문자열입니다 (길이: {len(content)})")
                print(f"내용: {content[:200]}...")
            else:
                print(f"Content는 {type(content)} 타입입니다")
                print(f"내용: {str(content)[:200]}...")
            
            # JSON으로 전체 응답 저장
            try:
                response_dict = {
                    "status_code": response.status_code,
                    "output": response.output.__dict__ if hasattr(response.output, '__dict__') else str(response.output),
                }
                
                with open('api_response_debug.json', 'w', encoding='utf-8') as f:
                    json.dump(response_dict, f, ensure_ascii=False, indent=2, default=str)
                print(f"\n💾 전체 응답을 api_response_debug.json에 저장했습니다.")
            except Exception as e:
                print(f"⚠️  JSON 저장 실패: {e}")
        
        else:
            print(f"❌ API 호출 실패: {response.code} - {response.message}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_response()
