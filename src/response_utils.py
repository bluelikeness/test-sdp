"""
Cloud API 응답 처리 유틸리티
"""

def extract_text_from_response(response):
    """
    Cloud API 응답에서 텍스트를 안전하게 추출
    다양한 응답 형식을 처리
    """
    try:
        if response.status_code != 200:
            return f"API 호출 실패: {response.code} - {response.message}"
        
        # 기본 응답 구조 접근
        content = response.output.choices[0].message.content
        
        # 1. 문자열인 경우 (가장 간단한 경우)
        if isinstance(content, str):
            return content.strip()
        
        # 2. 리스트인 경우 (복합 응답)
        elif isinstance(content, list):
            text_parts = []
            
            for item in content:
                # 딕셔너리 형태의 아이템 처리
                if isinstance(item, dict):
                    # OpenAI 스타일: {"type": "text", "text": "content"}
                    if item.get('type') == 'text' and 'text' in item:
                        text_parts.append(item['text'])
                    # 단순 텍스트 필드
                    elif 'text' in item:
                        text_parts.append(str(item['text']))
                    # content 필드
                    elif 'content' in item:
                        text_parts.append(str(item['content']))
                    # 메시지 필드
                    elif 'message' in item:
                        text_parts.append(str(item['message']))
                    # 전체 딕셔너리를 문자열로
                    else:
                        # 딕셔너리에서 가장 긴 문자열 값 찾기
                        longest_text = ""
                        for value in item.values():
                            if isinstance(value, str) and len(value) > len(longest_text):
                                longest_text = value
                        if longest_text:
                            text_parts.append(longest_text)
                        else:
                            text_parts.append(str(item))
                
                # 문자열 아이템
                elif isinstance(item, str):
                    text_parts.append(item)
                
                # 기타 타입
                else:
                    text_parts.append(str(item))
            
            # 텍스트 부분들을 합치기
            result = '\n'.join(text_parts).strip()
            return result if result else "No text detected"
        
        # 3. 딕셔너리인 경우
        elif isinstance(content, dict):
            # 일반적인 텍스트 필드들 확인
            text_fields = ['text', 'content', 'message', 'response', 'result']
            for field in text_fields:
                if field in content and isinstance(content[field], str):
                    return content[field].strip()
            
            # 필드가 없으면 전체를 문자열로
            return str(content).strip()
        
        # 4. 기타 타입
        else:
            return str(content).strip()
    
    except Exception as e:
        return f"응답 처리 오류: {str(e)}"

def debug_response_structure(response):
    """응답 구조를 자세히 분석 (디버깅용)"""
    try:
        print(f"📊 응답 구조 분석:")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            print(f"  Content 타입: {type(content)}")
            
            if isinstance(content, list):
                print(f"  리스트 길이: {len(content)}")
                for i, item in enumerate(content[:3]):  # 처음 3개만 표시
                    print(f"    [{i}] {type(item)}: {str(item)[:50]}...")
                    
            elif isinstance(content, dict):
                print(f"  딕셔너리 키들: {list(content.keys())}")
                
            elif isinstance(content, str):
                print(f"  문자열 길이: {len(content)}")
                print(f"  내용 미리보기: {content[:100]}...")
                
        return True
        
    except Exception as e:
        print(f"❌ 구조 분석 실패: {e}")
        return False
