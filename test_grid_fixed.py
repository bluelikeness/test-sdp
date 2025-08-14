#!/usr/bin/env python3
"""
그리드 기반 OCR 시스템 (네트워크 오류 수정 버전)
"""

import os
import sys
import math
import time
sys.path.append('src')

def test_grid_based_ocr_fixed():
    """네트워크 설정이 수정된 그리드 기반 OCR 테스트"""
    print("🔲 그리드 기반 OCR 테스트 (네트워크 수정 버전)")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        from cloud_ocr import CloudOCRProcessor
        
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("❌ API 키가 설정되지 않음")
            return False
        
        test_image = "input/17301.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 테스트 이미지 없음: {test_image}")
            return False
        
        print(f"📸 테스트 이미지: {test_image}")
        
        # 기존 CloudOCRProcessor 사용 (네트워크 설정 포함)
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        processor.set_ocr_mode("hybrid")  # 이미 그리드 방식으로 수정됨
        
        print("🔲 그리드 기반 하이브리드 모드 실행...")
        
        # 하이브리드 처리 (그리드 방식)
        result_text = processor.process_image_hybrid(test_image)
        
        if result_text and not result_text.startswith("처리 실패"):
            print(f"✅ 그리드 기반 OCR 성공!")
            print(f"📝 추출된 텍스트 길이: {len(result_text)}자")
            
            # 결과 저장
            os.makedirs("output", exist_ok=True)
            result_path = "output/grid_based_fixed_result.txt"
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write("=== 그리드 기반 OCR 결과 (네트워크 수정) ===\n")
                f.write(f"방식: 그리드 분할 + AI 원형 감지\n")
                f.write(f"추출된 텍스트 길이: {len(result_text)}자\n\n")
                f.write("=== 추출된 텍스트 ===\n")
                f.write(result_text)
            
            print(f"💾 결과 저장: {result_path}")
            
            # 미리보기
            print(f"\n📄 추출된 텍스트 미리보기:")
            lines = result_text.split('\n')
            for i, line in enumerate(lines[:5]):
                if line.strip():
                    print(f"  {i+1}: {line.strip()}")
            
            if len(lines) > 5:
                print(f"  ... (총 {len(lines)}개)")
            
            return True
        else:
            print(f"❌ 그리드 기반 OCR 실패: {result_text}")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_grid_approach():
    """간단한 그리드 접근법 테스트"""
    print(f"\n🔧 간단한 그리드 접근법 테스트")
    print("=" * 60)
    
    try:
        from cloud_ocr import CloudOCRProcessor
        from PIL import Image
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        test_image = "input/17301.png"
        
        # 이미지 수동 분할
        img = Image.open(test_image)
        width, height = img.size
        
        print(f"📏 원본 이미지 크기: {width}×{height}")
        
        # 간단히 4개 영역으로 분할
        regions = [
            (0, 0, width//2, height//2),           # 좌상
            (width//2, 0, width, height//2),       # 우상  
            (0, height//2, width//2, height),      # 좌하
            (width//2, height//2, width, height)   # 우하
        ]
        
        processor = CloudOCRProcessor(api_key, "qwen-vl-plus")
        
        print(f"🔲 4개 영역으로 수동 분할하여 처리:")
        
        all_results = []
        for i, (x1, y1, x2, y2) in enumerate(regions):
            print(f"   영역 {i+1}: ({x1},{y1}) → ({x2},{y2})")
            
            # 영역 크롭
            region = img.crop((x1, y1, x2, y2))
            
            # 임시 저장
            os.makedirs("output/temp", exist_ok=True)
            temp_path = f"output/temp/region_{i+1}.png"
            region.save(temp_path)
            
            print(f"   🤖 영역 {i+1} AI 처리 중...")
            
            # AI 처리 (shape_detection 모드)
            result = processor.process_image(temp_path, "shape_detection")
            
            if result and len(result.strip()) > 5:
                all_results.append(result.strip())
                print(f"   ✅ 영역 {i+1}: '{result.strip()[:30]}...'")
            else:
                print(f"   ❌ 영역 {i+1}: 텍스트 없음")
        
        # 결과 통합
        if all_results:
            final_result = "\n".join(all_results)
            
            result_path = "output/simple_grid_result.txt"
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write("=== 간단한 4분할 그리드 결과 ===\n")
                f.write(f"성공 영역: {len(all_results)}/4\n")
                f.write(f"총 텍스트 길이: {len(final_result)}자\n\n")
                f.write("=== 추출된 텍스트 ===\n")
                f.write(final_result)
            
            print(f"\n✅ 간단한 그리드 성공: {len(all_results)}/4 영역")
            print(f"💾 결과 저장: {result_path}")
            return True
        else:
            print(f"\n❌ 모든 영역에서 텍스트 추출 실패")
            return False
            
    except Exception as e:
        print(f"❌ 간단한 그리드 테스트 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 네트워크 오류 수정된 그리드 기반 OCR 테스트")
    print("💡 기존 cloud_ocr.py의 네트워크 설정을 활용")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    if os.path.basename(os.getcwd()) != "test-sdp":
        if os.path.exists("test-sdp"):
            os.chdir("test-sdp")
        else:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            return
    
    # 1단계: 수정된 하이브리드 모드 테스트
    print("🔲 1단계: 수정된 하이브리드 모드 (그리드 방식)")
    success1 = test_grid_based_ocr_fixed()
    
    # 2단계: 간단한 그리드 접근법
    print("🔧 2단계: 간단한 4분할 그리드")
    success2 = test_simple_grid_approach()
    
    print(f"\n" + "=" * 60)
    if success1 or success2:
        print("🎉 그리드 기반 OCR 성공!")
        print("✨ 작동하는 방식:")
        if success1:
            print("   ✅ 하이브리드 모드 (12개 영역 자동 분할)")
        if success2:
            print("   ✅ 간단한 4분할 그리드")
        
        print(f"\n📁 생성된 파일들:")
        if success1:
            print("   output/grid_based_fixed_result.txt")
        if success2:
            print("   output/simple_grid_result.txt")
            print("   output/temp/region_*.png")
        
        print(f"\n🎯 이제 main.py에서도 사용 가능:")
        print("   python src/main.py")
        print("   → 2. Qwen Cloud API 사용")
        print("   → 2. 하이브리드 모드 (그리드 방식)")
        
    else:
        print("❌ 모든 그리드 방식 실패")
        print("💡 대안:")
        print("   1. API 키 확인")
        print("   2. 네트워크 연결 확인") 
        print("   3. 다른 시간에 재시도")

if __name__ == "__main__":
    main()
